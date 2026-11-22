#!/opt/venv/bin/python3
"""manim-job: run one manim-video render job inside the render image.

The job directory is mounted at /job (read-only) with /job/out writable:
    /job/scene.py      the Manim Community scene file (name set by job.json "file")
    /job/job.json      what to render (see references/container.md)
    /job/assets/       optional images, SVGs, data
    /job/out/          everything this command writes

Commands:
    manim-job render [--quality preview|final] [--animations A,B]
                                                 render the job into /job/out (the default)
    manim-job inspect                            read job.json on stdin; print the settings the
                                                 wrapper needs (NETWORK, GPU, NARRATION, ...)
    manim-job frames [frames.py options]         more stills from the last render, no re-render
                                                 (--at 12.5,30 | --count 24 | --anims --from 20
                                                 --to 40 | --cues) -> out/frames/
    manim-job still K                            PNG at final resolution of the frame after
                                                 animation K (0-based) -> out/stills-full/
    manim-job doctor                             versions, fonts, LaTeX, EGL and VA-API status
    manim-job exec CMD [ARG...]                  run a command in the image (diagnostics, benchmarks)

Exit status: 0 rendered and checks passed (WARNs allowed), 1 rendered but a check FAILed,
2 bad job, 3 refused (running as root), 4 render failed.
Never prints environment values; the Kokoro key is only ever read by KokoroService.
"""

from __future__ import annotations

import configparser
import hashlib
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlsplit

JOB = Path(os.environ.get("MANIM_JOB_DIR", "/job"))
OUT = JOB / "out"
HELPERS = Path("/opt/manim-video/scripts")
PY = sys.executable

QUALITY = {  # manim flag, default resolution, default fps
    "preview": ("l", (854, 480), 15),
    "final": ("h", (1920, 1080), 60),
}
DEFAULT_KOKORO = {"base_url": "http://host.docker.internal:8880/v1", "model": "kokoro"}
DEFAULT_VOICE = "af_heart"
TOP_KEYS = {"scene", "file", "quality", "fps", "resolution", "renderer", "gpu", "encode",
            "narration", "requirements", "stills", "checks", "timeout", "animations"}
# ManimGL (3b1b/manim) idioms that fail or misbehave under Manim Community.
MANIMGL = re.compile(r"\b(manimlib|manimgl|ShowCreation|ShowCreationThenDestruction|TexMobject|TextMobject|"
                     r"GraphScene|InteractiveScene|TexText)\b|^\s*CONFIG\s*=|self\.embed\(|\.fix_in_frame\(")
NARRATION_KEYS = {"enabled", "mode", "script", "voice", "speed", "kokoro"}
KOKORO_KEYS = {"base_url", "model", "voice"}
CHECK_KEYS = {"light_bg", "min_duration", "max_duration"}


class JobError(Exception):
    pass


def say(msg: str) -> None:
    print(f"manim-job: {msg}", flush=True)


def refuse_root() -> None:
    if os.geteuid() == 0 or os.getegid() == 0:
        say("refusing to run as root (uid or gid 0). Run the container as an unprivileged user, "
            "for example --user \"$(id -u):$(id -g)\"; scripts/render-in-container.sh does this.")
        sys.exit(3)


# ---------------------------------------------------------------------------------------------
# job.json


def _unknown(d: dict, allowed: set[str], where: str) -> None:
    extra = sorted(k for k in d if k not in allowed and not k.startswith("_") and k != "notes")
    if extra:
        raise JobError(f"unknown key(s) in {where}: {', '.join(extra)} "
                       f"(allowed: {', '.join(sorted(allowed))}; prefix a key with _ for comments)")


def load_job(raw: dict, quality_override: str | None = None, animations_override: str | None = None) -> dict:
    if not isinstance(raw, dict):
        raise JobError("job.json must be a JSON object")
    _unknown(raw, TOP_KEYS, "job.json")
    job: dict = {}

    scene = raw.get("scene")
    if not isinstance(scene, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", scene):
        raise JobError('"scene" must be the Scene class name, e.g. "Explainer"')
    job["scene"] = scene

    f = raw.get("file", "scene.py")
    if not isinstance(f, str) or not f.endswith(".py") or "/" in f or f.startswith("."):
        raise JobError('"file" must be a .py file name in the job directory (default "scene.py")')
    job["file"] = f

    q = quality_override or raw.get("quality", "preview")
    if q not in QUALITY:
        raise JobError('"quality" must be "preview" or "final"')
    job["quality"] = q
    flag, (w, h), fps = QUALITY[q]

    if raw.get("fps") is not None:
        if not isinstance(raw["fps"], (int, float)) or not 1 <= raw["fps"] <= 120:
            raise JobError('"fps" must be a number between 1 and 120')
        fps = raw["fps"]
    if raw.get("resolution") is not None:
        m = re.fullmatch(r"(\d{2,5})x(\d{2,5})", str(raw["resolution"]))
        if not m:
            raise JobError('"resolution" must look like "1920x1080"')
        w, h = int(m.group(1)), int(m.group(2))
        if w % 2 or h % 2:
            raise JobError('"resolution" needs even width and height (H.264 4:2:0)')
    job.update(quality_flag=flag, width=w, height=h, fps=fps)

    r = raw.get("renderer", "cairo")
    if r not in ("cairo", "opengl"):
        raise JobError('"renderer" must be "cairo" or "opengl"')
    job["renderer"] = r

    g = raw.get("gpu", False)
    if not isinstance(g, bool):
        raise JobError('"gpu" must be true or false')
    job["gpu"] = g

    enc = raw.get("encode", "manim")
    if enc not in ("manim", "libx264", "h264_vaapi"):
        raise JobError('"encode" must be "manim" (keep Manim\'s own H.264), "libx264" or "h264_vaapi"')
    job["encode"] = enc

    n = raw.get("narration") or {}
    if isinstance(n, bool):
        n = {"enabled": n}
    if not isinstance(n, dict):
        raise JobError('"narration" must be an object, e.g. {"enabled": true}')
    _unknown(n, NARRATION_KEYS, "narration")
    k = n.get("kokoro") or {}
    if not isinstance(k, dict):
        raise JobError('"narration.kokoro" must be an object')
    _unknown(k, KOKORO_KEYS, "narration.kokoro")
    narr = {
        "enabled": bool(n.get("enabled", False)),
        "mode": n.get("mode", "voiceover"),
        "script": n.get("script"),
        "voice": n.get("voice") or k.get("voice") or os.environ.get("KOKORO_VOICE") or DEFAULT_VOICE,
        "speed": n.get("speed", 1.0),
        "base_url": k.get("base_url") or os.environ.get("KOKORO_BASE_URL") or DEFAULT_KOKORO["base_url"],
        "model": k.get("model") or os.environ.get("KOKORO_MODEL") or DEFAULT_KOKORO["model"],
    }
    if narr["mode"] not in ("voiceover", "mux"):
        raise JobError('"narration.mode" must be "voiceover" (manim-voiceover in the scene) or "mux"')
    if narr["enabled"] and narr["mode"] == "mux" and not narr["script"]:
        raise JobError('"narration.mode": "mux" needs "narration.script" (a file name or an inline object)')
    if narr["script"] is not None and not isinstance(narr["script"], (str, dict)):
        raise JobError('"narration.script" must be a file name in the job directory or an inline object')
    if not isinstance(narr["speed"], (int, float)) or not 0.5 <= narr["speed"] <= 2.0:
        raise JobError('"narration.speed" must be between 0.5 and 2.0')
    narr["base_url"] = loopback_to_host(narr["base_url"])
    job["narration"] = narr

    reqs = raw.get("requirements", [])
    if not isinstance(reqs, list) or not all(isinstance(x, str) and x.strip() for x in reqs):
        raise JobError('"requirements" must be a list of pip requirement strings')
    for x in reqs:
        if x.strip().startswith("-") or any(c in x for c in "\n;"):
            raise JobError(f'"requirements" entries must be plain specifiers like "sympy==1.13", not {x!r}')
    job["requirements"] = [x.strip() for x in reqs]

    st = raw.get("stills", "auto")
    if not (st in ("auto", "anims", "beats", "none") or re.fullmatch(r"count:\d{1,3}", str(st))):
        raise JobError('"stills" must be "auto", "anims" (one per animation), "none" or "count:N"')
    job["stills"] = st

    c = raw.get("checks") or {}
    if not isinstance(c, dict):
        raise JobError('"checks" must be an object')
    _unknown(c, CHECK_KEYS, "checks")
    job["checks"] = c

    a = animations_override or raw.get("animations")
    if a is not None and not re.fullmatch(r"\d{1,4}(,\d{1,4})?", str(a)):
        raise JobError('"animations" must look like "12,20" (render animations 12 to 20 only) or "12"')
    job["animations"] = str(a) if a is not None else None

    t = raw.get("timeout", 3600)
    if not isinstance(t, (int, float)) or t <= 0:
        raise JobError('"timeout" must be a positive number of seconds')
    job["timeout"] = t

    job["network"] = "bridge" if (narr["enabled"] or job["requirements"]) else "none"
    return job


def loopback_to_host(url: str) -> str:
    """Inside the container the host's loopback is host.docker.internal."""
    return re.sub(r"//(127\.0\.0\.1|localhost|\[::1\])([:/]|$)", r"//host.docker.internal\2", url)


def read_job_file(quality: str | None = None, animations: str | None = None) -> dict:
    p = JOB / "job.json"
    if not p.is_file():
        raise JobError(f"no job.json in the job directory ({p})")
    try:
        raw = json.loads(p.read_text())
    except json.JSONDecodeError as e:
        raise JobError(f"job.json is not valid JSON: {e}") from None
    return load_job(raw, quality, animations)


# ---------------------------------------------------------------------------------------------
# helpers


def run_logged(cmd: list[str], log, env=None, cwd=None, timeout=None) -> int:
    log.write(f"\n$ {' '.join(cmd)}\n")
    log.flush()
    try:
        return subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, env=env, cwd=cwd,
                              timeout=timeout).returncode
    except subprocess.TimeoutExpired:
        log.write(f"\nmanim-job: timed out after {timeout}s\n")
        return 124


def gpu_status() -> dict:
    nodes = sorted(str(p) for p in Path("/dev/dri").glob("renderD*")) if Path("/dev/dri").is_dir() else []
    usable = [n for n in nodes if os.access(n, os.R_OK | os.W_OK)]
    return {"render_nodes": nodes, "usable": usable}


def gl_renderer() -> str:
    """The OpenGL renderer Manim's headless context gets (EGL): iris = iGPU, llvmpipe = CPU."""
    code = ("import moderngl\n"
            "try:\n    c = moderngl.create_context(standalone=True)\n"
            "except Exception:\n    c = moderngl.create_context(standalone=True, backend='egl')\n"
            "print(c.info['GL_RENDERER'])")
    r = subprocess.run([PY, "-c", code], capture_output=True, text=True, timeout=60)
    return (r.stdout.strip().splitlines() or ["unavailable: " + (r.stderr.strip().splitlines() or ["?"])[-1]])[-1]


def kokoro_reachable(url: str) -> str | None:
    parts = urlsplit(url)
    host, port = parts.hostname, parts.port or (443 if parts.scheme == "https" else 80)
    try:
        with socket.create_connection((host, port), timeout=5):
            return None
    except OSError as e:
        return f"cannot reach the TTS server at {host}:{port} ({e.strerror or e})"


def find_video(since: float) -> Path | None:
    vids = [p for p in (OUT / "media" / "videos").rglob("*.mp4")
            if "partial_movie_files" not in p.parts and p.stat().st_mtime >= since - 1]
    return max(vids, key=lambda p: p.stat().st_mtime) if vids else None


def reencode(src: Path, dst: Path, codec: str, log) -> tuple[int, float]:
    t0 = time.monotonic()
    if codec == "h264_vaapi":
        node = (gpu_status()["usable"] or [None])[0]
        if node is None:
            log.write("manim-job: h264_vaapi needs the GPU (job.json \"gpu\": true)\n")
            return 2, 0.0
        cmd = ["ffmpeg", "-y", "-hide_banner", "-nostats", "-vaapi_device", node, "-i", str(src),
               "-vf", "format=nv12,hwupload", "-c:v", "h264_vaapi", "-qp", "20", "-c:a", "copy", str(dst)]
    else:
        cmd = ["ffmpeg", "-y", "-hide_banner", "-nostats", "-i", str(src), "-c:v", "libx264",
               "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "copy", str(dst)]
    rc = run_logged(cmd, log)
    return rc, time.monotonic() - t0


def clean_previous_outputs() -> None:
    for p in OUT.glob("*.mp4"):
        p.unlink()
    for name in ("report.json", "report.md", "render.log", "summary.json", "geometry.json"):
        (OUT / name).unlink(missing_ok=True)
    shutil.rmtree(OUT / "stills", ignore_errors=True)
    shutil.rmtree(OUT / "frames", ignore_errors=True)
    shutil.rmtree(OUT / "tmp", ignore_errors=True)


def write_merged_cfg() -> Path:
    """Manim keeps only 100 partial movies by default and deletes older ones, which breaks
    per-animation stills in longer scenes. The limit has no CLI flag and --config_file replaces a
    project manim.cfg, so write a merged copy with the limit raised."""
    cfg = configparser.ConfigParser(interpolation=None)
    if (JOB / "manim.cfg").is_file():
        cfg.read(JOB / "manim.cfg")
    if not cfg.has_section("CLI"):
        cfg.add_section("CLI")
    cfg.set("CLI", "max_files_cached", "100000")
    path = OUT / "tmp" / "manim-video.cfg"
    with path.open("w") as fh:
        cfg.write(fh)
    return path


def install_requirements(job: dict, log, env: dict) -> bool:
    """Extra Python packages, installed once per requirement set into out/.pydeps/<hash>."""
    if not job["requirements"]:
        return True
    key = hashlib.sha256("\n".join(sorted(job["requirements"])).encode()).hexdigest()[:12]
    target = OUT / ".pydeps" / key
    if not (target / ".complete").exists():
        say(f"installing extra requirements: {', '.join(job['requirements'])}")
        shutil.rmtree(target, ignore_errors=True)
        rc = run_logged([PY, "-m", "pip", "install", "--no-cache-dir", "--disable-pip-version-check",
                         "--target", str(target), *job["requirements"]], log, env=env)
        if rc != 0:
            say("pip install of the extra requirements failed; see the log in out/")
            return False
        (target / ".complete").touch()
    env["PYTHONPATH"] = f"{target}:{env.get('PYTHONPATH', '')}"
    return True


def narration_script_path(narr: dict) -> Path | None:
    if narr["script"] is None:
        return None
    if isinstance(narr["script"], str):
        p = JOB / narr["script"]
        if not p.is_file():
            raise JobError(f"narration script {narr['script']} not found in the job directory")
        return p
    p = OUT / "tmp" / "narration.json"
    p.write_text(json.dumps(narr["script"]))
    return p


def setup_dirs() -> None:
    os.umask(int(os.environ.get("UMASK", "002"), 8))
    for d in (Path(os.environ.get("HOME", "/tmp/home")), Path(os.environ.get("XDG_CACHE_HOME", "/tmp/cache"))):
        d.mkdir(parents=True, exist_ok=True)
    (OUT / "tmp").mkdir(parents=True, exist_ok=True)


def manimgl_hits(path: Path) -> list[str]:
    hits = []
    for i, line in enumerate(path.read_text(errors="replace").splitlines(), 1):
        if MANIMGL.search(line) and not line.lstrip().startswith("#"):
            hits.append(f"{i}: {line.strip()}")
    return hits


def refuse_manimgl(path: Path) -> bool:
    hits = manimgl_hits(path)
    if hits:
        print("\n".join(hits), flush=True)
        say("the lines above use ManimGL (3b1b/manim) idioms. This skill targets Manim Community: "
            "ShowCreation->Create, TexMobject->MathTex, TextMobject/TexText->Tex, CONFIG dict->__init__ "
            "args, GraphScene->Axes, no self.embed(), fix_in_frame->add_fixed_in_frame_mobjects. "
            "See references/api-cheatsheet.md.")
        return True
    return False


def geometry_check(log_text: str) -> dict:
    """Turn GeometryGuard's dump (out/geometry.json) into one check for the report."""
    path = OUT / "geometry.json"
    if "GEOMETRY-GUARD active" not in log_text or not path.is_file():
        return {"status": "not used", "level": "WARN",
                "message": "GeometryGuard not used: mix it in and declare rules for the main figure "
                           "(SKILL.md Step 2); the geometry gate needs measurements"}
    try:
        dump = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        return {"status": "error", "level": "FAIL", "message": f"cannot read out/geometry.json: {exc}"}
    s = dump.get("summary") or {}
    viol, rules = s.get("violations", []), dump.get("rules", [])
    unchecked = [r for r in rules if r not in s.get("checked_rules", [])]
    if viol:
        return {"status": "FAIL", "level": "FAIL", "violations": viol, "unchecked": unchecked,
                "message": f"{len(viol)} geometry violation(s) over {s.get('animations', 0)} animations "
                           f"({len(rules)} rule(s) declared, plus the frame-edge rule)"}
    if not rules:
        return {"status": "no rules", "level": "WARN", "violations": [], "unchecked": [],
                "message": "GeometryGuard ran but no rules were declared; only the frame-edge rule was checked"}
    if unchecked:
        return {"status": "PASS", "level": "WARN", "violations": [], "unchecked": unchecked,
                "message": f"{len(unchecked)} declared rule(s) never checked (objects never on screen together)"}
    return {"status": "PASS", "level": "PASS", "violations": [], "unchecked": [],
            "message": f"all {len(rules)} rule(s) and the frame-edge rule hold over {s.get('animations', 0)} animations"}


def tail(path: Path, n: int = 40) -> str:
    lines = path.read_text(errors="replace").splitlines()
    return "\n".join(lines[-n:])


# ---------------------------------------------------------------------------------------------
# commands


def cmd_inspect() -> int:
    try:
        job = load_job(json.loads(sys.stdin.read()))
    except (JobError, json.JSONDecodeError) as e:
        print(f"ERROR={e}")
        return 2
    print(f"SCENE={job['scene']}")
    print(f"QUALITY={job['quality']}")
    print(f"RENDERER={job['renderer']}")
    print(f"GPU={int(job['gpu'] or job['encode'] == 'h264_vaapi')}")
    print(f"NARRATION={int(job['narration']['enabled'])}")
    print(f"NETWORK={job['network']}")
    return 0


def cmd_doctor() -> int:
    def first_line(cmd: list[str]) -> str:
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            return ((r.stdout or r.stderr).strip().splitlines() or ["?"])[0]
        except (OSError, subprocess.TimeoutExpired) as e:
            return f"unavailable ({e})"

    print(f"uid:gid      {os.getuid()}:{os.getgid()} groups {sorted(os.getgroups())}")
    print(f"manim        {first_line(['manim', '--version'])}")
    print(f"voiceover    {first_line([PY, '-c', 'import importlib.metadata as m; print(m.version(\"manim-voiceover\"))'])}")
    print(f"python       {first_line([PY, '--version'])}")
    print(f"ffmpeg       {first_line(['ffmpeg', '-version'])}")
    print(f"latex        {first_line(['latex', '--version'])}")
    print(f"dvisvgm      {first_line(['dvisvgm', '--version'])}")
    print(f"fonts        {first_line(['fc-match', 'Noto Sans'])}")
    st = gpu_status()
    print(f"dri nodes    {st['render_nodes'] or 'none (no GPU passed in; CPU only)'}")
    print(f"opengl       {gl_renderer()}")
    if st["usable"]:
        r = subprocess.run(["vainfo", "--display", "drm", "--device", st["usable"][0]],
                           capture_output=True, text=True, timeout=60)
        drv = re.search(r"Driver version: (.*)", r.stdout + r.stderr)
        enc = sorted(set(re.findall(r"(VAProfileH264\w+)\s*:\s*(VAEntrypointEnc\w+)", r.stdout)))
        print(f"vaapi        {drv.group(1) if drv else 'no driver: ' + (r.stderr.strip().splitlines() or ['?'])[-1]}")
        print(f"h264 encode  {', '.join(f'{p}/{e}' for p, e in enc) or 'none'}")
    else:
        print("vaapi        not available (no usable /dev/dri render node)")
    return 0


def cmd_frames(args: list[str]) -> int:
    """Extra stills from the last rendered video (out/summary.json), written to out/frames/."""
    try:
        summary = json.loads((OUT / "summary.json").read_text())
        video = JOB / summary["video"]
    except (OSError, KeyError, json.JSONDecodeError):
        say("no finished render in out/ yet; render the job first")
        return 2
    if not video.is_file():
        say(f"{video} is missing; render the job again")
        return 2
    if any(a in ("--out",) for a in args):
        say("frames: --out is fixed to out/frames/")
        return 2
    media = JOB / summary.get("media_video", summary["video"])
    # Per-animation and subtitle-cue modes need Manim's partial-movie list / .srt next to the video.
    src = media if media.is_file() and {"--anims", "--beats", "--cues"} & set(args) else video
    return subprocess.run([PY, str(HELPERS / "frames.py"), str(src), "--out", str(OUT / "frames"), *args]).returncode


def cmd_still(k: str) -> int:
    """PNG at final resolution of the frame after animation K -> out/stills-full/."""
    if not k.isdigit():
        say("usage: manim-job still K   (K = 0-based animation number, as in stills/index.txt)")
        return 2
    try:
        job = read_job_file("final")
    except JobError as e:
        say(f"bad job: {e}")
        return 2
    if refuse_manimgl(JOB / job["file"]):
        return 2
    setup_dirs()
    log_path = OUT / "still.log"
    env = os.environ.copy()
    env.setdefault("COLUMNS", "200")
    with log_path.open("w") as log:
        if not install_requirements(job, log, env):
            return 4
        narr = job["narration"]
        if narr["enabled"]:
            env.update(KOKORO_BASE_URL=narr["base_url"], KOKORO_MODEL=narr["model"], KOKORO_VOICE=narr["voice"])
            try:
                script_path = narration_script_path(narr)
            except JobError as e:
                say(f"bad job: {e}")
                return 2
            if script_path is not None:
                env["NARRATION_SCRIPT"] = str(script_path)
            if narr["mode"] == "mux":
                timeline = OUT / "audio" / "timeline.json"
                if not timeline.is_file():
                    say("render the job once first (mux narration needs out/audio/timeline.json)")
                    return 2
                env["NARRATION_TIMELINE"] = str(timeline)
        env["GEOMETRY_JSON"] = str(OUT / "tmp" / "geometry-still.json")
        cmd = ["manim", "render", "-q", "h", "--config_file", str(write_merged_cfg()),
               "--media_dir", str(OUT / "media"), "--progress_bar", "none", "--renderer", job["renderer"],
               "-r", f"{job['width']},{job['height']}", "-s", "-n", f"0,{k}",
               str(JOB / job["file"]), job["scene"]]
        t0 = time.time()
        say(f"rendering the frame after animation {k} at {job['width']}x{job['height']}")
        rc = run_logged(cmd, log, env=env, cwd=str(JOB), timeout=job["timeout"])
    shutil.rmtree(OUT / "tmp", ignore_errors=True)
    if rc != 0:
        say(f"still FAILED (exit {rc}). Last lines of out/still.log:")
        print(tail(log_path), flush=True)
        return 4
    pngs = [p for p in (OUT / "media" / "images").rglob("*.png") if p.stat().st_mtime >= t0 - 1]
    if not pngs:
        say("no PNG was written")
        return 4
    dest = OUT / "stills-full" / f"anim_{k}-{time.strftime('%H%M%S')}.png"
    dest.parent.mkdir(exist_ok=True)
    shutil.copyfile(max(pngs, key=lambda p: p.stat().st_mtime), dest)
    say(f"wrote {dest.relative_to(JOB)}")
    return 0


def cmd_render(quality: str | None, animations: str | None = None) -> int:
    t_start = time.monotonic()
    try:
        job = read_job_file(quality, animations)
    except JobError as e:
        say(f"bad job: {e}")
        return 2
    if not (JOB / job["file"]).is_file():
        say(f"bad job: {job['file']} not found in the job directory")
        return 2
    if refuse_manimgl(JOB / job["file"]):
        return 2
    if not os.access(OUT, os.W_OK):
        say(f"{OUT} is not writable; the wrapper mounts it read-write")
        return 2

    clean_previous_outputs()
    setup_dirs()
    log_path = OUT / "render.log"
    log = log_path.open("w")
    env = os.environ.copy()
    env.setdefault("COLUMNS", "200")
    summary: dict = {"status": "running", "scene": job["scene"], "quality": job["quality"],
                     "renderer": job["renderer"], "resolution": f"{job['width']}x{job['height']}",
                     "fps": job["fps"], "timings": {}}
    gpu = gpu_status()
    summary["gpu"] = {"requested": job["gpu"], "render_nodes": gpu["render_nodes"], "usable": bool(gpu["usable"])}
    warnings: list[str] = []
    if job["gpu"] and not gpu["usable"]:
        warnings.append("gpu requested but no usable /dev/dri render node in the container; ran on the CPU")
    if job["renderer"] == "opengl":
        summary["gpu"]["gl_renderer"] = gl_renderer()
        log.write(f"manim-job: OpenGL renderer: {summary['gpu']['gl_renderer']}\n")

    def finish(status: str, rc: int) -> int:
        summary["status"] = status
        summary["warnings"] = warnings
        summary["timings"]["total"] = round(time.monotonic() - t_start, 2)
        (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
        shutil.rmtree(OUT / "tmp", ignore_errors=True)
        log.close()
        return rc

    if not install_requirements(job, log, env):
        return finish("failed", 4)

    # Narration settings for KokoroService / narrate_mux.py (the key itself is only passed through).
    narr = job["narration"]
    timeline = None
    if narr["enabled"]:
        env.update(KOKORO_BASE_URL=narr["base_url"], KOKORO_MODEL=narr["model"], KOKORO_VOICE=narr["voice"])
        problem = kokoro_reachable(narr["base_url"])
        if problem:
            say(f"narration: {problem}. Is the TTS server running, and did the wrapper give the "
                "container network access (it does for narrated jobs)?")
            return finish("failed", 4)
        summary["narration"] = {"mode": narr["mode"], "voice": narr["voice"], "model": narr["model"],
                                "base_url": narr["base_url"], "key_passed": bool(env.get("KOKORO_API_KEY"))}
        try:
            script_path = narration_script_path(narr)
        except JobError as e:
            say(f"bad job: {e}")
            return finish("failed", 2)
        if script_path is not None:
            env["NARRATION_SCRIPT"] = str(script_path)
            if narr["mode"] == "mux":
                t0 = time.monotonic()
                audio_dir = OUT / "audio"
                say("narration: synthesizing one clip per beat (narrate_mux.py tts)")
                rc = run_logged([PY, str(HELPERS / "narrate_mux.py"), "tts", str(script_path),
                                 "--out-dir", str(audio_dir)], log, env=env)
                if rc != 0:
                    say("narration: TTS failed; see out/render.log")
                    return finish("failed", 4)
                timeline = audio_dir / "timeline.json"
                env["NARRATION_TIMELINE"] = str(timeline)
                summary["timings"]["tts"] = round(time.monotonic() - t0, 2)

    # Render. GeometryGuard (scripts/geometry_qa.py) dumps its measurements here.
    env["GEOMETRY_JSON"] = str(OUT / "geometry.json")
    cmd = ["manim", "render", "-q", job["quality_flag"], "--config_file", str(write_merged_cfg()),
           "--media_dir", str(OUT / "media"), "--progress_bar", "none", "--renderer", job["renderer"],
           "--fps", f"{job['fps']:g}", "-r", f"{job['width']},{job['height']}", "--format", "mp4"]
    if job["animations"]:
        cmd += ["-n", job["animations"]]
        summary["animations"] = job["animations"]
    if narr["enabled"]:
        # Reusing cached partial movies lets the picture drift from the audio; the TTS clips
        # themselves stay cached in out/media/voiceovers/.
        cmd.append("--disable_caching")
    cmd += [str(JOB / job["file"]), job["scene"]]
    say(f"rendering {job['file']} {job['scene']}: {job['quality']} {job['width']}x{job['height']} @ "
        f"{job['fps']:g} fps, {job['renderer']} renderer, GPU {'on' if gpu['usable'] else 'off'}, "
        f"network {'on' if job['network'] == 'bridge' else 'off'}")
    t0 = time.time()
    tm = time.monotonic()
    rc = run_logged(cmd, log, env=env, cwd=str(JOB), timeout=job["timeout"])
    summary["timings"]["render"] = round(time.monotonic() - tm, 2)
    log.flush()

    text = log_path.read_text(errors="replace")
    scene_warnings = list(dict.fromkeys(
        re.sub(r"^.*?((LAYOUT|NARRATION)\b)", r"\1", line).strip()
        for line in text.splitlines()
        if re.search(r"\b(LAYOUT |LAYOUT$|NARRATION)", line) and "LAYOUT-GUARD" not in line
        and "GEOMETRY" not in line))
    summary["scene_warnings"] = scene_warnings[:200]
    if "LAYOUT-GUARD active" in text:
        summary["layout_guard"] = "active"
    elif "LayoutGuard" in (JOB / job["file"]).read_text(errors="replace"):
        summary["layout_guard"] = "did not run"
        warnings.append("the scene mentions LayoutGuard but it did not run (import failed, or it is "
                        "not the first base class)")
    else:
        summary["layout_guard"] = "not used"
    if rc != 0:
        say(f"render FAILED (exit {rc}) after {summary['timings']['render']}s. Last lines of out/render.log:")
        print(tail(log_path), flush=True)
        if re.search(r"latex error|LaTeX compilation error|! Undefined control sequence|! Missing|! LaTeX Error",
                     text, re.I):
            say("this is a LaTeX error: check the MathTex/Tex strings (references/troubleshooting.md)")
        return finish("failed", 4)

    media_video = find_video(t0)
    if media_video is None:
        say("render finished but no video was written (did the scene play any animation?)")
        return finish("failed", 4)

    # Narration mux (fallback path) and optional re-encode, then deliver to out/.
    delivered = OUT / f"{job['scene']}-{job['quality']}.mp4"
    current = media_video
    if timeline is not None:
        muxed = OUT / "tmp" / "muxed.mp4"
        rc = run_logged([PY, str(HELPERS / "narrate_mux.py"), "mux", str(current), str(timeline),
                         "--out", str(muxed)], log, env=env)
        if rc != 0:
            say("narration: mux failed; see out/render.log")
            return finish("failed", 4)
        current = muxed
    if job["encode"] != "manim":
        tmp = OUT / "tmp" / "encoded.mp4"
        rc, secs = reencode(current, tmp, job["encode"], log)
        summary["timings"]["encode"] = round(secs, 2)
        summary["encode"] = job["encode"]
        if rc != 0:
            say(f"re-encode with {job['encode']} failed; see out/render.log")
            return finish("failed", 4)
        current = tmp
    shutil.copyfile(current, delivered)
    summary["video"] = str(delivered.relative_to(JOB))
    summary["media_video"] = str(media_video.relative_to(JOB))

    # Automated checks.
    tm = time.monotonic()
    qa = [PY, str(HELPERS / "qa_check.py"), str(delivered), "--json",
          "--expect-res", f"{job['width']}x{job['height']}",
          "--expect-audio" if narr["enabled"] else "--expect-silent"]
    if job["checks"].get("light_bg"):
        qa.append("--light-bg")
    for k in ("min_duration", "max_duration"):
        if k in job["checks"]:
            qa += [f"--{k.replace('_', '-')}", str(job["checks"][k])]
    r = subprocess.run(qa, capture_output=True, text=True, env=env)
    try:
        report = json.loads(r.stdout)
    except json.JSONDecodeError:
        report = {"result": "FAIL", "checks": [{"level": "FAIL", "check": "qa_check",
                                                "message": (r.stderr or r.stdout).strip()[-500:]}]}
    report["scene_warnings"] = scene_warnings[:200]
    geo = geometry_check(text)
    report["geometry"] = geo
    report.setdefault("checks", []).append({"level": geo["level"], "check": "geometry", "message": geo["message"]})
    levels = [c["level"] for c in report["checks"]]
    report["result"] = "FAIL" if "FAIL" in levels else ("WARN" if "WARN" in levels else "PASS")
    summary["geometry"] = {"status": geo["status"], "violations": len(geo.get("violations", []))}
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    summary["timings"]["checks"] = round(time.monotonic() - tm, 2)
    summary["checks"] = report.get("result", "FAIL")

    # Stills and contact sheets (beat ends from Manim's partial-movie list, so use the media copy).
    tm = time.monotonic()
    stills_mode = job["stills"]
    if stills_mode == "auto":
        stills_mode = "anims" if job["quality"] == "preview" else "count:8"
    sheets: list[str] = []
    if stills_mode != "none":
        fr = [PY, str(HELPERS / "frames.py"), str(media_video), "--out", str(OUT / "stills")]
        fr += ["--anims", "--mid"] if stills_mode in ("anims", "beats") else ["--count", stills_mode.split(":")[1]]
        r = subprocess.run(fr, capture_output=True, text=True, env=env)
        log.write("\n$ " + " ".join(fr) + "\n" + r.stdout + r.stderr)
        sheets = [str(Path(s.split("SHEET: ", 1)[1]).relative_to(JOB)) for s in r.stdout.splitlines()
                  if s.startswith("SHEET: ")]
        if r.returncode != 0:
            warnings.append("still extraction failed; see out/render.log")
    summary["timings"]["stills"] = round(time.monotonic() - tm, 2)
    summary["stills"] = sheets

    # Human-readable report.
    lines = [f"# Render report: {job['scene']} ({job['quality']})", "",
             f"- video: `{summary['video']}`",
             f"- {job['width']}x{job['height']} @ {job['fps']:g} fps, renderer {job['renderer']}, "
             f"GPU {'on' if gpu['usable'] else 'off'}" + (f" ({summary['gpu'].get('gl_renderer')})"
                                                           if job['renderer'] == 'opengl' else ""),
             f"- timings (s): " + ", ".join(f"{k} {v}" for k, v in summary["timings"].items()),
             f"- LayoutGuard: {summary['layout_guard']}; GeometryGuard: {summary['geometry']['status']}",
             f"- overall check result: **{summary['checks']}**", "", "## Checks", ""]
    lines += [f"- {c['level']} {c['check']}: {c['message']}" for c in report.get("checks", [])]
    lines += ["", "## Geometry (GeometryGuard, measured)", "", f"- {geo['message']}"]
    lines += [f"- FAIL {v['rule']} at anims {v['first_anim']}-{v['last_anim']} (t={v['first_t']}-{v['last_t']} s, "
              f"{v['count']}x): {v['detail']}" for v in geo.get("violations", [])]
    lines += [f"- UNCHECKED {r}: its objects were never on screen together" for r in geo.get("unchecked", [])]
    if geo["status"] != "not used":
        lines.append("- measurements per animation: `out/geometry.json`")
    if scene_warnings:
        lines += ["", "## Scene warnings (LayoutGuard / Timeline)", ""] + [f"- {w}" for w in scene_warnings[:60]]
    if warnings:
        lines += ["", "## Job warnings", ""] + [f"- {w}" for w in warnings]
    lines += ["", "## Stills", ""] + [f"- `{s}`" for s in sheets] + ["- index: `out/stills/index.txt`"]
    (OUT / "report.md").write_text("\n".join(lines) + "\n")

    status = "ok" if summary["checks"] != "FAIL" else "checks_failed"
    rc = finish(status, 0 if status == "ok" else 1)
    say(f"done in {summary['timings']['total']}s: checks {summary['checks']}"
        + (f", {len(scene_warnings)} scene warning(s)" if scene_warnings else ""))
    for w in warnings:
        say(f"warning: {w}")
    return rc


def main(argv: list[str]) -> int:
    refuse_root()
    cmd = argv[0] if argv else "render"
    if cmd == "render":
        opts, rest = {}, argv[1:]
        while rest:
            if len(rest) >= 2 and rest[0] in ("--quality", "--animations"):
                opts[rest[0][2:]] = rest[1]
                rest = rest[2:]
            else:
                say("usage: manim-job render [--quality preview|final] [--animations A,B]")
                return 2
        return cmd_render(opts.get("quality"), opts.get("animations"))
    if cmd == "inspect":
        return cmd_inspect()
    if cmd == "frames":
        return cmd_frames(argv[1:])
    if cmd == "still":
        return cmd_still(argv[1] if len(argv) > 1 else "")
    if cmd == "doctor":
        return cmd_doctor()
    if cmd == "exec":
        if len(argv) < 2:
            say("usage: manim-job exec CMD [ARG...]")
            return 2
        os.execvp(argv[1], argv[1:])
    if cmd in ("-h", "--help", "help"):
        print(__doc__)
        return 0
    say(f"unknown command {cmd!r}; try: render, inspect, doctor, exec, help")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
