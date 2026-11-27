#!/usr/bin/env python3
"""Render a manim-video job in the render container. This is the default render path.

Cross-platform (Linux, macOS, Windows; Python 3.9+, standard library only). The shims
render-in-container.sh (Linux, macOS, WSL2, Git Bash) and render-in-container.ps1 (Windows
PowerShell) run this file with the same arguments.

Usage:
  render-in-container JOB_DIR [--quality preview|final] [--animations A,B] [--workers N]
                              [--gpu | --no-gpu | --nvidia] [--no-build]
  render-in-container JOB_DIR --frames [--at T1,T2 | --count N | --anims --from S --to S | --cues]
                                             more stills from the last render (no re-render),
                                             written to JOB_DIR/out/frames/
  render-in-container JOB_DIR --geometry     re-measure the GeometryGuard rules in seconds, without
                                             rendering frames -> out/geometry-check.txt/.json
  render-in-container JOB_DIR --still K      PNG at final resolution of the frame after animation K
                                             (0-based, as in stills/index.txt) -> out/stills-full/
  render-in-container --pull                 fetch the published image built from these exact sources
                                             (MANIM_PULL_FROM:<source hash>) and tag it manim-video:local
  render-in-container --build                build or rebuild the image locally (manim-video:local)
  render-in-container --status               is the image present and built from these sources?
  render-in-container --source-sha           print the source hash (the published image's tag)
  render-in-container --doctor [--gpu]       versions, fonts, LaTeX, EGL and VA-API in the image
  render-in-container --check [--tts]        is Docker usable and the image current? (any OS)

JOB_DIR holds scene.py, job.json and optional assets/ (references/container.md). The container
sees JOB_DIR read-only at /job and writes only JOB_DIR/out/:
  out/<Scene>-<quality>.mp4   the video             out/report.md, report.json  automated checks
  out/stills/sheet_NN.png     contact sheets        out/stills/frame_*.png      full-size stills
  out/stills/index.txt        tile -> time -> beat  out/summary.json            machine summary
  out/render.log              full render log       out/media/                  Manim's cache

--gpu / --no-gpu override job.json "gpu" (default off). --gpu passes /dev/dri (Linux only; Intel or
AMD through Mesa). --nvidia adds docker/compose.nvidia.yml (NVIDIA Container Toolkit; UNTESTED).
The GPU only helps the OpenGL renderer and hardware encoding; the default Cairo renderer is
CPU-only. Docker Desktop on macOS and Windows gives Linux containers no GPU for this use.
--workers N overrides job.json "workers": N parallel sections (references/gpu-and-speed.md).

A render with the image missing or stale first pulls the published image for these sources, then
builds locally if that fails (--no-build: neither; it renders with what is there, or stops).

Exit status: 0 rendered and checks passed (WARNs allowed), 1 rendered but a check FAILed,
2 bad job or usage, 3 Docker or image problem, 4 render failed, 130 interrupted.

Environment (all optional):
  MANIM_IMAGE      image tag (default manim-video:local)
  MANIM_PULL_FROM  where published images live (default ghcr.io/quellen-sol/manim-video, built by
                   .github/workflows/image.yml); none = never pull, always build locally
  KOKORO_API_KEY   given to narrated jobs only, by name, never printed. If unset, it is read from
                   KOKORO_ENV_FILE (default ~/.config/agent-stack/gateway.env, if readable).
  KOKORO_BASE_URL, KOKORO_MODEL, KOKORO_VOICE   defaults for narrated jobs (job.json wins)
  MANIM_TTS_NETWORK  network for narrated jobs: bridge (default; the host is reached through
                   host.docker.internal) or host (fallback if that route is blocked)
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

if sys.version_info < (3, 9):
    sys.exit("render-in-container: needs Python 3.9 or newer")

SCRIPTS_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPTS_DIR.parent
DOCKER_DIR = SKILL_DIR / "docker"
SELF_NAME = "render_in_container.py"   # host-only: excluded from the image and its source hash
IS_WINDOWS = os.name == "nt" or sys.platform in ("cygwin", "msys")
IS_MAC = sys.platform == "darwin"
IS_LINUX = sys.platform.startswith("linux")
DEFAULT_PULL_FROM = "ghcr.io/quellen-sol/manim-video"


class Exit(Exception):
    def __init__(self, code: int, msg: str = ""):
        super().__init__(msg)
        self.code, self.msg = code, msg


def note(msg: str) -> None:
    print(f"render-in-container: {msg}", flush=True)


def fail(code: int, msg: str) -> None:
    raise Exit(code, msg)


# ---------------------------------------------------------------------------------------------
# paths


class PathError(ValueError):
    pass


def to_docker_path(path: str, windows: bool = IS_WINDOWS) -> str:
    """The form of an absolute host path that `docker compose` bind mounts accept.

    POSIX hosts (Linux, macOS, WSL2): unchanged. Windows (Docker Desktop): drive paths with forward
    slashes and an upper-case drive letter, e.g. C:\\Users\\me\\job -> C:/Users/me/job. MSYS/Git Bash
    (/c/Users/me) and Cygwin (/cygdrive/c/Users/me) forms are converted to the same. Paths inside a
    WSL distro (\\\\wsl$\\... or \\\\wsl.localhost\\...) and network shares are refused: run the
    renderer from inside WSL for files that live there, and copy network files to a local disk.
    """
    if not windows:
        return path
    p = path.strip()
    if p.startswith("\\\\?\\UNC\\"):
        p = "\\\\" + p[8:]
    elif p.startswith("\\\\?\\") or p.startswith("//?/"):
        p = p[4:]
    p = p.replace("\\", "/")
    m = re.match(r"^/(?:cygdrive/)?([A-Za-z])(/.*)?$", p)
    if m:
        p = f"{m.group(1)}:{m.group(2) or '/'}"
    if p.lower().startswith(("//wsl$/", "//wsl.localhost/")):
        raise PathError(f"{path} is inside a WSL distro; run the renderer from inside WSL "
                        "(the .sh shim) instead of from Windows")
    if p.startswith("//"):
        raise PathError(f"{path} is a network share; Docker Desktop cannot bind-mount it reliably. "
                        "Copy the job directory to a local drive")
    m = re.match(r"^([A-Za-z]):(/.*)?$", p)
    if not m:
        raise PathError(f"{path} is not an absolute Windows path (expected e.g. C:\\Users\\me\\job)")
    rest = re.sub(r"/{2,}", "/", m.group(2) or "/")
    if len(rest) > 1:
        rest = rest.rstrip("/")
    return f"{m.group(1).upper()}:{rest}"


def cache_dir() -> Path:
    if IS_WINDOWS and os.environ.get("LOCALAPPDATA"):
        return Path(os.environ["LOCALAPPDATA"]) / "manim-video"
    if IS_MAC:
        return Path.home() / "Library" / "Caches" / "manim-video"
    return Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache") / "manim-video"


# ---------------------------------------------------------------------------------------------
# docker helpers


def docker_bin() -> str:
    exe = shutil.which("docker")
    if not exe:
        fail(3, "docker is not installed (Linux: Docker Engine with the compose plugin; macOS and Windows: "
                "Docker Desktop). Host fallback on Linux/macOS: scripts/render.sh (references/environment.md)")
    return exe


def run_quiet(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, **kw)


def source_sha() -> str:
    """Hash of everything baked into the image (the same bytes, in the same order, as
    `cat docker/Dockerfile docker/requirements.lock docker/manim_job.py scripts/*.py | sha256sum`
    in the C locale), to spot a stale image after the skill changes."""
    h = hashlib.sha256()
    files = [DOCKER_DIR / "Dockerfile", DOCKER_DIR / "requirements.lock", DOCKER_DIR / "manim_job.py"]
    files += sorted((p for p in SCRIPTS_DIR.glob("*.py") if p.name != SELF_NAME),
                    key=lambda p: p.name.encode())
    for f in files:
        h.update(f.read_bytes())
    return h.hexdigest()[:16]


def pull_from() -> str | None:
    """The registry repository of published images, or None if pulling is off."""
    v = os.environ.get("MANIM_PULL_FROM")
    if v is None:
        return DEFAULT_PULL_FROM
    v = v.strip()
    return None if v.lower() in ("", "none", "off", "0") else v


def image_label(docker: str, image: str) -> str | None:
    r = run_quiet([docker, "image", "inspect", "-f", '{{index .Config.Labels "org.manim-video.source-sha"}}', image])
    return r.stdout.strip() if r.returncode == 0 else None


def image_size(docker: str, image: str) -> str:
    r = run_quiet([docker, "image", "inspect", "-f", "{{.Size}}", image])
    try:
        return f"{int(r.stdout.strip()) / 1e9:.2f} GB"
    except ValueError:
        return "?"


class Runner:
    def __init__(self) -> None:
        self.docker = docker_bin()
        self.image = os.environ.get("MANIM_IMAGE") or "manim-video:local"
        self.env = os.environ.copy()
        self.env["MANIM_IMAGE"] = self.image
        self.compose_files = ["-f", str(DOCKER_DIR / "compose.yml")]
        self.project = ""
        self.child: subprocess.Popen | None = None
        self.gpu_on = False
        self.no_build = False
        if IS_WINDOWS or not hasattr(os, "getuid"):
            # Docker Desktop maps file ownership itself; any non-root uid works. The image refuses 0.
            self.uid, self.gid = 1000, 1000
        else:
            self.uid, self.gid = os.getuid(), os.getgid()
        self.env["HOST_UID"], self.env["HOST_GID"] = str(self.uid), str(self.gid)
        self.env["MANIM_NETWORK"] = "none"

    # -- preflight ---------------------------------------------------------------------------
    def preflight(self) -> None:
        if hasattr(os, "geteuid") and not IS_WINDOWS and os.geteuid() == 0:
            fail(2, "refusing to run as root; run as the user who owns the job directory")
        if run_quiet([self.docker, "info"]).returncode != 0:
            hint = ("start Docker Desktop and wait until it says it is running" if (IS_WINDOWS or IS_MAC)
                    else "is the daemon running, and is this user in the docker group?")
            fail(3, f"cannot talk to the Docker daemon ({hint}). Host fallback: scripts/render.sh")
        if run_quiet([self.docker, "compose", "version"]).returncode != 0:
            fail(3, "the docker compose plugin (v2+) is missing")

    # -- image -------------------------------------------------------------------------------
    def build_image(self) -> None:
        logdir = cache_dir()
        logdir.mkdir(parents=True, exist_ok=True)
        log = logdir / f"build-{time.strftime('%Y%m%d-%H%M%S')}.log"
        note(f"building {self.image} (first build: about 6 minutes; later builds reuse the cache). Log: {log}")
        env = dict(self.env, SOURCE_SHA=source_sha(), JOB_DIR=to_docker_path(str(SKILL_DIR)))
        with log.open("w") as fh:
            rc = subprocess.run([self.docker, "compose", "--progress", "plain", "-f", str(DOCKER_DIR / "compose.yml"),
                                 "build", "manim"], env=env, stdout=fh, stderr=subprocess.STDOUT).returncode
        if rc != 0:
            lines = log.read_text(errors="replace").splitlines()
            print("\n".join(lines[-30:]), file=sys.stderr)
            hint = ""
            if re.search(r"certificate verif|CERTIFICATE_VERIFY_FAILED|x509:|SSLError|unknown authority",
                         "\n".join(lines[-60:]), re.I):
                hint = (" (TLS errors inside the build usually mean a proxy that re-signs HTTPS; use the "
                        "published image instead: render-in-container --pull)")
            fail(3, f"image build failed{hint}; full log: {log}")
        note(f"built {self.image} ({image_size(self.docker, self.image)})")

    def pull_image(self, required: bool) -> bool:
        """Fetch the image published for exactly these sources (tag = source hash) and tag it as
        self.image. required: fail on any problem; otherwise note it and return False."""
        def give_up(msg: str) -> bool:
            if required:
                fail(3, msg)
            note(f"{msg}; building locally instead")
            return False
        repo = pull_from()
        if not repo:
            if required:
                fail(3, "pulling is off (MANIM_PULL_FROM=none); build locally with --build")
            return False
        want = source_sha()
        ref = f"{repo}:{want}"
        note(f"pulling {ref} (the published image for these sources; about 0.7 GB to download)")
        r = run_quiet([self.docker, "pull", "-q", ref])
        if r.returncode != 0:
            err = (r.stderr.strip().splitlines() or ["no output"])[-1]
            if re.search(r"not found|manifest unknown", err, re.I):
                err += " (not published: local changes, or the image workflow has not finished)"
            elif re.search(r"denied|unauthorized", err, re.I):
                err += (f" (GHCR says this for a package that does not exist yet, and for a private one: "
                        f"docker login {repo.split('/')[0]})")
            return give_up(f"could not pull {ref}: {err}")
        have = image_label(self.docker, ref)
        if have != want:
            if ref != self.image:
                run_quiet([self.docker, "image", "rm", ref])
            return give_up(f"{ref} is labelled with sources {have}, expected {want}")
        if ref != self.image:
            t = run_quiet([self.docker, "tag", ref, self.image])
            if t.returncode != 0:
                return give_up(f"could not tag {ref} as {self.image}: {t.stderr.strip()}")
            run_quiet([self.docker, "image", "rm", ref])   # drops only the registry tag
        note(f"pulled {ref} as {self.image} ({image_size(self.docker, self.image)})")
        return True

    def ensure_image(self) -> None:
        have = image_label(self.docker, self.image)
        want = source_sha()
        if not have:
            if self.no_build:
                fail(3, f"image {self.image} not found; run: render-in-container --pull (or --build)")
            self.pull_image(required=False) or self.build_image()
        elif have != want and have != "<no value>":
            if self.no_build:
                note(f"warning: {self.image} was built from older skill sources ({have}, now {want}); "
                     "update with --pull or --build")
            else:
                note("image is older than the skill's sources; updating it")
                self.pull_image(required=False) or self.build_image()

    def status(self) -> int:
        have = image_label(self.docker, self.image)
        want = source_sha()
        if not have:
            print(f"image {self.image}: missing (get it: render-in-container --pull, or --build)")
            return 2
        size = image_size(self.docker, self.image)
        if have == want:
            print(f"image {self.image}: current ({size}, sources {want})")
            return 0
        print(f"image {self.image}: stale (built from {have}, sources now {want}; the next render pulls or "
              "rebuilds it)")
        return 1

    # -- GPU ---------------------------------------------------------------------------------
    def enable_gpu(self) -> None:
        if not IS_LINUX:
            note("warning: GPU requested, but Docker Desktop on macOS and Windows gives Linux containers no "
                 "GPU for this use; rendering on the CPU (references/gpu-and-speed.md)")
            return
        nodes = sorted(Path("/dev/dri").glob("renderD*")) if Path("/dev/dri").is_dir() else []
        if not nodes:
            note("warning: GPU requested but this host has no /dev/dri render node; rendering on the CPU")
            return
        cards = sorted(Path("/dev/dri").glob("card*"))

        def gid(group: str, fallback: Path) -> str:
            r = run_quiet(["getent", "group", group]) if shutil.which("getent") else None
            if r is not None and r.returncode == 0 and r.stdout.count(":") >= 2:
                return r.stdout.split(":")[2]
            return str(fallback.stat().st_gid)
        self.env["RENDER_GID"] = gid("render", nodes[0])
        self.env["VIDEO_GID"] = gid("video", cards[0] if cards else nodes[0])
        self.compose_files += ["-f", str(DOCKER_DIR / "compose.gpu.yml")]
        self.gpu_on = True

    def enable_nvidia(self) -> None:
        note("NVIDIA: adding docker/compose.nvidia.yml (UNTESTED on the maintainers' hardware; needs the NVIDIA "
             "Container Toolkit on a Linux host; references/gpu-and-speed.md)")
        self.compose_files += ["-f", str(DOCKER_DIR / "compose.nvidia.yml")]
        self.gpu_on = True

    # -- compose project lifecycle -----------------------------------------------------------
    def new_project(self, name: str) -> None:
        slug = re.sub(r"[^a-z0-9]+", "-", Path(name).name.lower()).strip("-")[:24].strip("-")
        self.project = f"manim-{slug or 'job'}-{time.strftime('%Y%m%d%H%M%S')}-{os.getpid()}"

    def cleanup(self) -> None:
        if self.child is not None and self.child.poll() is None:
            try:
                self.child.terminate()
                self.child.wait(timeout=10)
            except Exception:
                try:
                    self.child.kill()
                except Exception:
                    pass
        self.child = None
        if not self.project:
            return
        r = run_quiet([self.docker, "ps", "-aq", "--filter", f"label=com.docker.compose.project={self.project}"])
        ids = r.stdout.split() if r.returncode == 0 else []
        if ids:
            run_quiet([self.docker, "rm", "-f", *ids])
        run_quiet([self.docker, "compose", "-p", self.project, *self.compose_files, "down",
                   "--remove-orphans", "--timeout", "5"], env=self.env)
        self.project = ""

    def run_service(self, args: list[str]) -> int:
        cmd = [self.docker, "compose", "--progress", "quiet", "-p", self.project, *self.compose_files,
               "run", "--rm", "-T", "manim", *args]
        self.child = subprocess.Popen(cmd, env=self.env, stdin=subprocess.DEVNULL)
        while True:   # short waits, so Ctrl-C reaches Python promptly on Windows too
            try:
                rc = self.child.wait(timeout=0.5)
                break
            except subprocess.TimeoutExpired:
                continue
        self.child = None
        return rc

    # -- Kokoro key --------------------------------------------------------------------------
    def kokoro_key(self, narrated: bool) -> None:
        if not narrated:
            self.env.pop("KOKORO_API_KEY", None)   # silent jobs never see the key
            return
        if not self.env.get("KOKORO_API_KEY"):
            envfile = Path(self.env.get("KOKORO_ENV_FILE") or Path.home() / ".config" / "agent-stack" / "gateway.env")
            try:
                text = envfile.read_text(errors="replace")
            except OSError:
                text = ""
            vals = [m.group(2) for m in re.finditer(r"^(export\s+)?KOKORO_API_KEY=(.*)$", text, re.M)]
            if vals:
                v = vals[-1].strip()
                if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
                    v = v[1:-1]
                if v:
                    self.env["KOKORO_API_KEY"] = v
                    note(f"narration: using KOKORO_API_KEY from {envfile} (passed by name; value not shown)")
        if not self.env.get("KOKORO_API_KEY"):
            self.env.pop("KOKORO_API_KEY", None)


# ---------------------------------------------------------------------------------------------
# commands


def parse_args(argv: list[str]) -> dict:
    o = {"job": None, "quality": None, "gpu": None, "nvidia": False, "no_build": False, "action": "render",
         "frame_args": [], "still": None, "anims": None, "workers": None, "tts": False}
    i = 0
    while i < len(argv):
        a = argv[i]
        if o["action"] == "frames":
            o["frame_args"].append(a)
            i += 1
            continue

        def value() -> str:
            if i + 1 >= len(argv):
                raise Exit(2, f"{a} needs a value")
            return argv[i + 1]
        if a == "--frames":
            o["action"] = "frames"
        elif a == "--quality":
            o["quality"] = value(); i += 1
        elif a.startswith("--quality="):
            o["quality"] = a.split("=", 1)[1]
        elif a in ("--preview", "--final"):
            o["quality"] = a[2:]
        elif a == "--animations":
            o["anims"] = value(); i += 1
        elif a == "--workers":
            o["workers"] = value(); i += 1
        elif a.startswith("--workers="):
            o["workers"] = a.split("=", 1)[1]
        elif a == "--gpu":
            o["gpu"] = True
        elif a == "--no-gpu":
            o["gpu"] = False
        elif a == "--nvidia":
            o["nvidia"] = True
        elif a == "--no-build":
            o["no_build"] = True
        elif a in ("--build", "--pull", "--status", "--geometry", "--doctor", "--check", "--source-sha"):
            o["action"] = a[2:]
        elif a == "--tts":
            o["tts"] = True
        elif a == "--still":
            o["action"] = "still"; o["still"] = value(); i += 1
        elif a in ("-h", "--help"):
            o["action"] = "help"
        elif a.startswith("-"):
            raise Exit(2, f"unknown option {a} (see --help)")
        else:
            if o["job"] is not None:
                raise Exit(2, "only one JOB_DIR, please (see --help)")
            o["job"] = a
        i += 1
    if o["quality"] not in (None, "preview", "final"):
        raise Exit(2, "--quality must be preview or final")
    if o["workers"] is not None and not re.fullmatch(r"\d{1,2}", o["workers"]):
        raise Exit(2, "--workers must be a whole number (1 = serial)")
    if o["action"] == "still" and not (o["still"] or "").isdigit():
        raise Exit(2, "--still needs an animation number (0-based)")
    return o


def kokoro_check(base_url: str, key: str | None) -> str:
    req = urllib.request.Request(base_url.rstrip("/") + "/models")
    if key:
        req.add_header("Authorization", f"Bearer {key}")
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return f"ok (HTTP {r.status})"
    except urllib.error.HTTPError as e:
        return f"reachable, HTTP {e.code}" + (" (check KOKORO_API_KEY)" if e.code in (401, 403) else "")
    except (urllib.error.URLError, OSError) as e:
        return f"NOT reachable ({getattr(e, 'reason', e)})"


def cmd_check(r: Runner, tts: bool) -> int:
    """Read-only readiness check for any OS (check_env.sh is the fuller Linux/macOS version)."""
    bad = 0
    print(f"host      {platform.system()} {platform.release()} {platform.machine()}, Python {platform.python_version()}")
    v = run_quiet([r.docker, "version", "-f", "{{.Server.Version}} {{.Server.Os}}/{{.Server.Arch}}"])
    if v.returncode != 0:
        print("FAIL docker daemon not reachable (start Docker Desktop, or check the docker group on Linux)")
        return 1
    print(f"ok   docker engine {v.stdout.strip()}")
    c = run_quiet([r.docker, "compose", "version", "--short"])
    print(f"{'ok  ' if c.returncode == 0 else 'FAIL'} docker compose {c.stdout.strip() or 'missing'}")
    bad += c.returncode != 0
    st = r.status()
    bad += st == 2
    try:
        to_docker_path(str(SKILL_DIR))
        print(f"ok   skill directory mountable: {to_docker_path(str(SKILL_DIR))}")
    except PathError as e:
        print(f"FAIL {e}")
        bad += 1
    if tts:
        base = os.environ.get("KOKORO_BASE_URL") or "http://127.0.0.1:8880/v1"
        r.kokoro_key(True)
        res = kokoro_check(base, r.env.get("KOKORO_API_KEY"))
        print(f"{'ok  ' if res.startswith('ok') else 'WARN'} Kokoro at {base}: {res}; "
              f"key {'set (not shown)' if r.env.get('KOKORO_API_KEY') else 'not set'}")
    if IS_MAC or IS_WINDOWS:
        print("note GPU: Docker Desktop gives Linux containers no GPU for this skill; renders use the CPU")
    print("RESULT: " + ("READY" if not bad else "NOT READY") + (" (image missing or stale: the first render "
          "pulls or builds it, or run --pull / --build)" if st else ""))
    return 0 if not bad else 1


def main(argv: list[str]) -> int:
    o = parse_args(argv)
    if o["action"] == "help":
        print(__doc__)
        return 0
    if o["action"] == "source-sha":     # no Docker needed (the image workflow uses this)
        print(source_sha())
        return 0
    r = Runner()
    r.no_build = o["no_build"]
    if o["action"] == "check":
        return cmd_check(r, o["tts"])
    r.preflight()
    if o["action"] == "build":
        r.build_image()
        return 0
    if o["action"] == "pull":
        if image_label(r.docker, r.image) == source_sha():
            note(f"{r.image} is already current (sources {source_sha()})")
        else:
            r.pull_image(required=True)
        return 0
    if o["action"] == "status":
        return r.status()

    if o["action"] == "doctor":
        r.ensure_image()
        if o["gpu"]:
            r.enable_gpu()
        if o["nvidia"]:
            r.enable_nvidia()
        tmp = Path(tempfile.mkdtemp(prefix="manim-doctor-"))
        (tmp / "out").mkdir()
        try:
            r.env["JOB_DIR"] = to_docker_path(str(tmp))
        except PathError as e:
            shutil.rmtree(tmp, ignore_errors=True)
            fail(3, f"temporary directory not mountable: {e} (set TEMP/TMPDIR to a local folder)")
        try:
            r.new_project("doctor")
            return r.run_service(["doctor"])
        finally:
            r.cleanup()
            shutil.rmtree(tmp, ignore_errors=True)

    # ---- job ------------------------------------------------------------------------------
    if not o["job"]:
        print(__doc__)
        return 2
    job = Path(o["job"])
    if not job.is_dir():
        fail(2, f"no such job directory: {o['job']}")
    job = job.resolve()
    if not (job / "job.json").is_file():
        fail(2, f"{job} has no job.json (template: templates/job.json)")
    try:
        r.env["JOB_DIR"] = to_docker_path(str(job))
    except PathError as e:
        fail(2, str(e))
    out = job / "out"
    out.mkdir(exist_ok=True)
    if not os.access(out, os.W_OK):
        fail(2, f"{out} is not writable by this user")

    r.ensure_image()

    # Validate job.json in a throwaway container (no network, no mounts) and read the settings.
    info = subprocess.run([r.docker, "run", "--rm", "-i", "--network", "none", "--user", f"{r.uid}:{r.gid}",
                           "--read-only", "--cap-drop", "ALL", "--security-opt", "no-new-privileges", r.image,
                           "inspect"], input=(job / "job.json").read_bytes(), stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE)
    text = info.stdout.decode(errors="replace")
    if info.returncode != 0:
        for line in text.splitlines():
            if line.startswith("ERROR="):
                print(f"render-in-container: bad job.json: {line[6:]}", file=sys.stderr)
        if "ERROR=" not in text:
            print(info.stderr.decode(errors="replace").strip()[-500:], file=sys.stderr)
        return 2
    s = dict(line.split("=", 1) for line in text.splitlines() if "=" in line)
    narrated = s.get("NARRATION") == "1"
    network = "bridge" if s.get("NETWORK") == "bridge" else "none"
    if network == "bridge":
        tn = os.environ.get("MANIM_TTS_NETWORK") or "bridge"
        if tn not in ("bridge", "host"):
            fail(2, "MANIM_TTS_NETWORK must be bridge or host")
        network = tn
    want_gpu = s.get("GPU") == "1" if o["gpu"] is None else o["gpu"]
    action = o["action"]
    if action == "frames":          # still extraction needs no network, key or GPU
        network, narrated, want_gpu = "none", False, False
        o["nvidia"] = False
    if action == "geometry":        # a dry run draws nothing
        want_gpu = False
        o["nvidia"] = False
    if want_gpu:
        r.enable_gpu()
    if o["nvidia"]:
        r.enable_nvidia()
    r.env["MANIM_NETWORK"] = network
    r.kokoro_key(narrated)

    r.new_project(str(job))
    gpu_desc = "off"
    if r.gpu_on:
        gpu_desc = "on" + (f" (video {r.env.get('VIDEO_GID')}, render {r.env.get('RENDER_GID')})"
                           if "RENDER_GID" in r.env else " (nvidia)")
    note(f"job {job}: scene {s.get('SCENE', '')}, GPU {gpu_desc}, network {network}")
    if action == "frames":
        args = ["frames", *o["frame_args"]]
    elif action == "still":
        args = ["still", o["still"]]
    elif action == "geometry":
        args = ["geometry"]
    else:
        args = ["render"]
        if o["quality"]:
            args += ["--quality", o["quality"]]
        if o["anims"]:
            args += ["--animations", o["anims"]]
        if o["workers"]:
            args += ["--workers", o["workers"]]
    try:
        rc = r.run_service(args)
    finally:
        r.cleanup()

    def show(tag: str, paths) -> None:
        for p in paths:
            print(f"{tag}: {p}")
    show("VIDEO", sorted(out.glob("*.mp4")))
    if action == "still":
        pngs = sorted((out / "stills-full").glob(f"anim_{o['still']}-*.png"), key=lambda p: p.stat().st_mtime)
        if pngs:
            print(f"IMAGE: {pngs[-1]}")
        return rc
    if action == "geometry":
        for name, tag in (("geometry-check.txt", "GEOMETRY"), ("geometry-check.json", "MEASUREMENTS")):
            if (out / name).is_file():
                print(f"{tag}: {out / name}")
        return rc
    if action == "frames":
        show("SHEET", sorted((out / "frames").glob("sheet_*.png")))
        if (out / "frames" / "index.txt").is_file():
            print(f"INDEX: {out / 'frames' / 'index.txt'}")
        return rc
    show("SHEET", sorted((out / "stills").glob("sheet_*.png")))
    for name, tag in (("stills/index.txt", "INDEX"), ("report.md", "REPORT"), ("render.log", "LOG")):
        if (out / name).is_file():
            print(f"{tag}: {out / name}")
    return rc


def _on_signal(signum, frame):  # noqa: ARG001
    raise KeyboardInterrupt


if __name__ == "__main__":
    for sig in ("SIGTERM", "SIGBREAK", "SIGHUP"):
        if hasattr(signal, sig):
            try:
                signal.signal(getattr(signal, sig), _on_signal)
            except (OSError, ValueError):
                pass
    try:
        sys.exit(main(sys.argv[1:]))
    except Exit as e:
        if e.msg:
            print(f"render-in-container: {e.msg}", file=sys.stderr)
        sys.exit(e.code)
    except KeyboardInterrupt:
        print()
        note("interrupted; removing the container")
        sys.exit(130)
