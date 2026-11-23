"""Render one Manim scene as N contiguous sections in parallel processes, then join them.

Opt-in through job.json "workers": N (see references/gpu-and-speed.md). Used by the container's job
runner (docker/manim_job.py); it can also run on a host Manim. Manim Community 0.22.1, Cairo only.

How it works
  1. plan:   one quick pass over the scene (every play() jumps to its end) records every play()'s
             duration and estimated cost (its frame count times the measured cost of one update
             step and one drawn frame of its end state) and fills the LaTeX and text caches; the
             animations are split into N contiguous ranges of about equal estimated cost.
  2. render: N worker processes render their range with `manim render -n A,B`, each with its own
             media directory (seeded with hard links to the shared LaTeX/text caches, so no two
             processes ever write the same file).
  3. join:   the workers' partial movie files are concatenated in animation order with ffmpeg
             (stream copy: the encoded frames are exactly what a serial render writes).

Correctness traps and how they are handled
  - State carried between animations (ValueTracker, always_redraw, updaters): each worker runs the
    whole construct() and fast-forwards the animations before its range without drawing or
    encoding them. An animation jumps to its end in one step (Manim's own skipping) when nothing on
    screen can depend on the individual frames; it is stepped frame by frame (interpolation and
    updaters, still without drawing) when the scene has a time-based updater (one that takes dt,
    e.g. TracedPath), a scene-level updater, a wait_until stop condition or an UpdateFromFunc.
  - Safety nets: (a) seam check: worker k also renders the last animation of worker k-1, and the
    two renderings must decode to identical frames; (b) GeometryGuard cross-check: every tracked
    object's measured box after every fast-forwarded animation must match the worker that drew
    it. Either failing makes the job render serially instead. What neither catches: an updater
    without dt that changes state on every call (frame-rate dependent, e.g. lambda m:
    m.rotate(0.01)) on an object that is neither on screen at a seam nor tracked.
  - Shared caches: separate media directories per worker; LaTeX/text caches pre-filled by the plan
    run and hard-linked, never shared for writing. Manim's partial-movie cache is not used.
  - Narration through manim-voiceover (add_sound offsets, a voiceover cache written by every
    process) and sections with skip_animations are not supported: the caller renders those
    serially. Narration in "mux" mode is added after the join and works.

Commands (run with the scene's directory as the working directory):
    python3 -m parallel_render plan OUT.json -- <manim render args>     the dry-run plan
    python3 -m parallel_render worker FROM -- <manim render args>       one exact-fast-forward worker
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

# ---------------------------------------------------------------------------------------------
# inside the manim process: patches


class _State(threading.local):
    ff = False


_STATE = _State()


def _run_manim_cli(args: list[str]) -> int:
    from manim.__main__ import main
    sys.argv = ["manim", *args]
    try:
        main()
    except SystemExit as exc:  # click exits; keep its code
        code = exc.code
        return code if isinstance(code, int) else (0 if code is None else 1)
    return 0


def cmd_plan(out_path: str, manim_args: list[str]) -> int:
    """Quick pass: every play() jumps to its end (Manim's --dry_run alone still steps and draws
    every frame). Records, for every play(): its duration, whether it is a frozen frame (a wait
    with nothing moving), the time of its one update step and of drawing its end state once."""
    from manim.renderer.cairo_renderer import CairoRenderer
    from manim.scene.scene import Scene
    plays: list[dict] = []
    cur: dict = {}
    orig = CairoRenderer.play
    orig_uss = CairoRenderer.update_skipping_status
    orig_update_frame = CairoRenderer.update_frame
    orig_update_to_time = Scene.update_to_time
    orig_frozen = Scene.is_current_animation_frozen_frame

    def update_skipping_status(self):
        orig_uss(self)
        self.skip_animations = True

    def update_to_time(self, t):
        t0 = time.perf_counter()
        cur["in_update"] = True
        try:
            return orig_update_to_time(self, t)
        finally:
            cur["in_update"] = False
            cur["update_s"] = cur.get("update_s", 0.0) + time.perf_counter() - t0

    # One-time cache fills (LaTeX, dvisvgm, Pango) inside an updater are not per-frame costs.
    import importlib

    def timed_fill(fn):
        def inner(*a, **k):
            t0 = time.perf_counter()
            try:
                return fn(*a, **k)
            finally:
                if cur.get("in_update"):
                    cur["fill_s"] = cur.get("fill_s", 0.0) + time.perf_counter() - t0
        return inner
    for mod, owner, name in (("manim.utils.tex_file_writing", None, "compile_tex"),
                             ("manim.utils.tex_file_writing", None, "convert_to_svg"),
                             ("manim.mobject.text.text_mobject", "Text", "_text2svg"),
                             ("manim.mobject.text.text_mobject", "MarkupText", "_text2svg")):
        try:
            m = importlib.import_module(mod)
            target = getattr(m, owner) if owner else m
            if hasattr(target, name):
                setattr(target, name, timed_fill(getattr(target, name)))
        except Exception:
            pass

    def is_frozen(self):
        cur["frozen"] = bool(orig_frozen(self))
        return cur["frozen"]

    CairoRenderer.update_skipping_status = update_skipping_status
    CairoRenderer.update_frame = lambda self, *a, **k: None
    CairoRenderer.render = lambda self, *a, **k: None
    Scene.update_to_time = update_to_time
    Scene.is_current_animation_frozen_frame = is_frozen

    def play(self, scene, *a, **k):
        idx = self.num_plays
        cur.clear()
        try:
            return orig(self, scene, *a, **k)
        finally:
            if self.num_plays > idx:   # the play happened (not ended early)
                t0 = time.perf_counter()
                try:
                    orig_update_frame(self, scene)          # draw the end state once, to time it
                except Exception:
                    pass
                plays.append({"index": idx, "duration": float(getattr(scene, "duration", 0.0) or 0.0),
                              "frozen": cur.get("frozen", False),
                              "update_s": max(0.0, cur.get("update_s", 0.0) - cur.get("fill_s", 0.0)),
                              "draw_s": time.perf_counter() - t0,
                              "sections_skip": bool(self.file_writer.sections[-1].skip_animations)})
    CairoRenderer.play = play
    rc = _run_manim_cli(["render", "--dry_run", *manim_args])
    from manim import config
    Path(out_path).write_text(json.dumps({"rc": rc, "fps": float(config.frame_rate), "plays": plays}))
    return rc


def frame_dependent(scene) -> str | None:
    """Why this play's end state can depend on stepping through its frames (None = it cannot)."""
    if getattr(scene, "updaters", None):
        return "scene-level updater"
    if getattr(scene, "stop_condition", None) is not None:
        return "wait_until"
    anims = list(getattr(scene, "animations", None) or [])
    for a in anims:
        if type(a).__name__ == "UpdateFromFunc":
            return "UpdateFromFunc"
    mobs = list(scene.mobjects) + [a.mobject for a in anims if getattr(a, "mobject", None) is not None]
    for m in mobs:
        for sm in m.get_family():
            if sm.has_time_based_updater():
                return f"time-based updater on {type(sm).__name__}"
    return None


def cmd_worker(ff_until: int, manim_args: list[str]) -> int:
    """Render with `-n FROM,TO`; animations before FROM are fast-forwarded without drawing or
    encoding: in one step when no frame-dependent state is involved, else frame by frame."""
    import atexit
    from manim.renderer.cairo_renderer import CairoRenderer
    from manim.scene.scene import Scene
    stats = {"one_step": 0, "stepped": 0, "reasons": {}}

    orig_play = CairoRenderer.play
    orig_render = CairoRenderer.render
    orig_update_frame = CairoRenderer.update_frame
    orig_progression = Scene.get_time_progression
    orig_play_internal = Scene.play_internal

    def play(self, scene, *a, **k):
        # Fast-forward only plays that a serial render would draw: before FROM, and not inside a
        # section that the scene itself marked skip_animations (Manim collapses those in serial too).
        _STATE.ff = self.num_plays < ff_until and not self.file_writer.sections[-1].skip_animations
        try:
            return orig_play(self, scene, *a, **k)
        finally:
            _STATE.ff = False

    def get_time_progression(self, run_time, description, n_iterations=None, override_skip_animations=False):
        step = False
        if _STATE.ff:
            why = frame_dependent(self)
            step = why is not None
            stats["stepped" if step else "one_step"] += 1
            if why:
                stats["reasons"][why] = stats["reasons"].get(why, 0) + 1
        return orig_progression(self, run_time, description, n_iterations, override_skip_animations or step)

    def render(self, scene, t, moving_mobjects=None):
        if _STATE.ff:
            return None
        return orig_render(self, scene, t, moving_mobjects)

    def update_frame(self, scene, *a, **k):
        if _STATE.ff:
            return None
        return orig_update_frame(self, scene, *a, **k)

    def play_internal(self, skip_rendering=False):
        result = orig_play_internal(self, skip_rendering)
        if _STATE.ff:
            # A drawn play ends with update_mobjects(0); Manim omits it for skipped plays.
            self.update_mobjects(0)
        return result

    CairoRenderer.play = play
    CairoRenderer.render = render
    CairoRenderer.update_frame = update_frame
    Scene.get_time_progression = get_time_progression
    Scene.play_internal = play_internal
    if 0 < ff_until < 1000000000:
        atexit.register(lambda: print(
            f"PARALLEL worker: fast-forwarded animations 0..{ff_until - 1}: {stats['one_step']} in one step, "
            f"{stats['stepped']} frame by frame {stats['reasons'] or ''}", flush=True))
    return _run_manim_cli(["render", *manim_args])


# ---------------------------------------------------------------------------------------------
# orchestration (called by the job runner; no Manim import here)


# Cost model for one play (seconds of serial render time), from the plan pass. Per animated frame:
# one update step plus one drawn frame; frozen waits only repeat an encoded frame; plus a fixed
# cost per play (encoder flush at the end of every animation: 0.39 s per play in the measured
# profile of examples/01-unit-circle).
FROZEN_FRAME_S = 0.002
PER_PLAY_S = 0.35


def play_costs(plan: dict) -> list[float]:
    fps = plan["fps"]
    out = []
    for p in plan["plays"]:
        frames = max(1, round(p["duration"] * fps))
        per_frame = FROZEN_FRAME_S if p.get("frozen") else p.get("update_s", 0.0) + p.get("draw_s", 0.0)
        out.append(PER_PLAY_S + frames * per_frame)
    return out


def split(costs: list[float], workers: int) -> list[tuple[int, int]]:
    """Contiguous animation ranges [(first, last)] with about equal estimated cost. Each boundary
    is nudged (within 8% of the total) to just after a cheap animation, because worker k
    re-renders the last animation of worker k-1 for the seam check."""
    frames = [max(1e-6, c) for c in costs]
    n = len(frames)
    workers = max(1, min(workers, n // 2))
    if workers == 1:
        return [(0, n - 1)]
    total = sum(frames)
    cum = [0]
    for f in frames:
        cum.append(cum[-1] + f)          # cum[j] = frames before animation j
    starts = [0]
    for k in range(1, workers):
        target = total * k / workers
        lo, hi = starts[-1] + 2, n - 2 * (workers - k) + 1   # >= 2 animations per worker
        cands = [j for j in range(lo, hi + 1) if abs(cum[j] - target) <= 0.08 * total]
        if not cands:
            cands = [min(range(lo, hi + 1), key=lambda j: abs(cum[j] - target))]
        starts.append(min(cands, key=lambda j: (frames[j - 1], abs(cum[j] - target))))
    return [(s, (starts[i + 1] - 1 if i + 1 < len(starts) else n - 1)) for i, s in enumerate(starts)]


def _link_tree(src: Path, dst: Path) -> None:
    if not src.is_dir():
        return
    try:
        shutil.copytree(src, dst, copy_function=os.link, dirs_exist_ok=True)
    except OSError:
        shutil.copytree(src, dst, dirs_exist_ok=True)


def _manifest(path: Path) -> list[Path]:
    files = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if line.startswith("file '"):
            p = line[len("file '"):-1]
            files.append(Path(p[len("file:"):] if p.startswith("file:") else p))
    return files


def _same_snapshot(a: dict, b: dict, tol: float = 2e-3) -> bool:
    oa, ob = a.get("objects", {}), b.get("objects", {})
    if set(oa) != set(ob):
        return False
    for k in oa:
        if any(abs(x - y) > tol for x, y in zip(oa[k].get("box", []), ob[k].get("box", []))):
            return False
    ra = sorted((r["rule"], r["ok"]) for r in a.get("results", []))
    rb = sorted((r["rule"], r["ok"]) for r in b.get("results", []))
    return ra == rb


def geometry_cross_check(procs: list[dict], dumps: list[dict]) -> int | None:
    """First animation whose fast-forwarded GeometryGuard measurement differs from the worker
    that drew it, or None."""
    owner = {}
    for w, d in zip(procs, dumps):
        for snap in d.get("snapshots", []):
            if w["first"] <= snap.get("anim", -1) <= w["last"]:
                owner[snap["anim"]] = snap
    for w, d in zip(procs, dumps):
        for snap in d.get("snapshots", []):
            n = snap.get("anim", -1)
            if n < w["first"] and n in owner and not _same_snapshot(owner[n], snap):
                return n
    return None


def frames_md5(ffmpeg: str, video: Path) -> str:
    r = subprocess.run([ffmpeg, "-v", "error", "-i", str(video), "-map", "0:v:0", "-f", "md5", "-"],
                       capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else f"error:{r.stderr.strip()[-200:]}"


def run(*, python: str, manim_args: list[str], scene_file: str, scene: str, cwd: str, out: Path,
        media: Path, workers: int, env: dict, log, timeout: float, ffmpeg: str = "ffmpeg") -> dict:
    """Plan, render in parallel, check the seams and join. Returns a dict with "status" in
    ok | fallback | failed, plus "video" (ok), "reason", timings and per-worker details."""
    res: dict = {"status": "failed", "workers": workers}
    work = out / "tmp" / "parallel"
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    me = [python, "-m", "parallel_render"]
    t0 = time.monotonic()
    # One random seed for the plan and every worker, unless the job's manim.cfg sets one: Manim
    # seeds random/NumPy from config.seed, which is unset by default (different in every process).
    if "--config_file" in manim_args:
        import configparser
        cfg = configparser.ConfigParser(interpolation=None)
        cfg.read(manim_args[manim_args.index("--config_file") + 1])
        seed = cfg.get("CLI", "seed", fallback="").strip()
    else:
        seed = ""
    if not seed:
        import random
        seed = str(random.SystemRandom().randrange(1, 2**31))
        manim_args = [*manim_args, "--seed", seed]
    res["seed"] = int(seed)

    # 1. plan (fills out/media/Tex and out/media/texts as a side effect)
    plan_json = work / "plan.json"
    penv = dict(env, GEOMETRY_JSON=str(work / "plan-geometry.json"))
    log.write("\n## parallel: plan (dry run)\n")
    log.flush()
    rc = subprocess.run([*me, "plan", str(plan_json), "--", *manim_args, "--media_dir", str(media),
                         scene_file, scene], cwd=cwd, env=penv, stdout=log, stderr=subprocess.STDOUT,
                        timeout=timeout).returncode
    res["timings"] = {"plan": round(time.monotonic() - t0, 2)}
    if rc != 0 or not plan_json.is_file():
        res.update(status="failed", reason=f"plan run failed (exit {rc})")
        return res
    plan = json.loads(plan_json.read_text())
    plays = plan["plays"]
    if any(p["sections_skip"] for p in plays):
        res.update(status="fallback", reason="the scene skips sections (next_section(skip_animations=True))")
        return res
    costs = play_costs(plan)
    ranges = split(costs, workers)
    res["estimated_s"] = [round(sum(costs[a:b + 1]), 1) for a, b in ranges]
    res["animations"] = len(plays)
    res["ranges"] = ranges
    if len(ranges) < 2:
        res.update(status="fallback", reason=f"only {len(plays)} animations; too few to split")
        return res
    res["workers"] = len(ranges)

    # 2. workers: each renders [first-1 (seam overlap), last] in its own media directory
    procs = []
    t1 = time.monotonic()
    for k, (first, last) in enumerate(ranges):
        wdir = work / f"w{k}"
        wmedia = wdir / "media"
        wmedia.mkdir(parents=True, exist_ok=True)
        _link_tree(media / "Tex", wmedia / "Tex")
        _link_tree(media / "texts", wmedia / "texts")
        start = first - 1 if k > 0 else 0
        wenv = dict(env, GEOMETRY_JSON=str(wdir / "geometry.json"))
        wlog = (wdir / "render.log").open("w")
        args = [*me, "worker", str(start), "--", *manim_args, "--media_dir", str(wmedia),
                "--disable_caching", "-n", f"{start},{last}", scene_file, scene]
        wlog.write("$ " + " ".join(args) + "\n")
        wlog.flush()
        p = subprocess.Popen(args, cwd=cwd, env=wenv, stdout=wlog, stderr=subprocess.STDOUT)
        procs.append({"k": k, "proc": p, "log": wlog, "dir": wdir, "start": start, "first": first,
                      "last": last, "t0": time.monotonic()})
    deadline = time.monotonic() + timeout
    failed = None
    while any("rc" not in w for w in procs):
        for w in procs:
            if "rc" in w:
                continue
            rc = w["proc"].poll()
            if rc is None and time.monotonic() > deadline:
                rc = 124
            if rc is None:
                continue
            w["rc"], w["secs"] = rc, round(time.monotonic() - w["t0"], 2)
            if rc != 0 and failed is None:
                failed = w
                for o in procs:
                    if o["proc"].poll() is None:
                        o["proc"].terminate()
        time.sleep(0.2)
    for w in procs:
        if w["proc"].poll() is None:
            w["proc"].kill()
            w["proc"].wait()
        w["log"].close()
        log.write(f"\n## parallel: worker {w['k']} (animations {w['start']}..{w['last']}, exit {w.get('rc')}, "
                  f"{w.get('secs')} s)\n")
        log.write((w["dir"] / "render.log").read_text(errors="replace"))
    log.flush()
    res["timings"]["workers"] = round(time.monotonic() - t1, 2)
    res["worker_secs"] = [w.get("secs") for w in procs]
    if failed is not None:
        res.update(status="failed", reason=f"worker {failed['k']} failed (exit {failed['rc']})")
        return res

    # 3. seam check and join
    t2 = time.monotonic()
    lists = []
    for w in procs:
        man = list((w["dir"] / "media" / "videos").rglob("partial_movie_file_list.txt"))
        if len(man) != 1:
            res.update(status="failed", reason=f"worker {w['k']}: expected one partial movie list, found {len(man)}")
            return res
        files = _manifest(man[0])
        want = w["last"] - w["start"] + 1
        if len(files) != want or not all(f.is_file() for f in files):
            res.update(status="failed", reason=f"worker {w['k']}: {len(files)} partial movies, expected {want}")
            return res
        lists.append(files)
    seams = []
    for k in range(1, len(procs)):
        a, b = lists[k - 1][-1], lists[k][0]
        ha, hb = frames_md5(ffmpeg, a), frames_md5(ffmpeg, b)
        seams.append({"anim": procs[k]["start"], "match": ha == hb and not ha.startswith("error")})
    res["seams"] = seams
    if not all(s["match"] for s in seams):
        bad = [s["anim"] for s in seams if not s["match"]]
        res.update(status="fallback", reason=f"seam check failed at animation(s) {bad}: the fast-forwarded "
                                             "state differs from the serial state")
        return res
    gdumps = [w["dir"] / "geometry.json" for w in procs]
    if all(d.is_file() for d in gdumps):
        bad = geometry_cross_check(procs, [json.loads(d.read_text()) for d in gdumps])
        res["geometry_cross_check"] = "ok" if bad is None else f"differs at animation {bad}"
        if bad is not None:
            res.update(status="fallback", reason=f"GeometryGuard measurements after fast-forwarded animation {bad} "
                                                 "differ from the worker that drew it")
            return res
    else:
        res["geometry_cross_check"] = "not available (scene does not use GeometryGuard)"

    dest = media / "videos" / "parallel"
    shutil.rmtree(dest, ignore_errors=True)
    pdir = dest / "partial_movie_files" / scene
    pdir.mkdir(parents=True)
    ordered = []
    for k, files in enumerate(lists):
        for f in files[(1 if k > 0 else 0):]:
            target = pdir / f.name
            if target.exists():
                target = pdir / f"w{k}_{f.name}"
            shutil.move(str(f), target)
            ordered.append(target)
    listing = pdir / "partial_movie_file_list.txt"
    listing.write_text("# Partial movies joined by parallel_render.py, in animation order.\n"
                       + "".join(f"file 'file:{p.as_posix()}'\n" for p in ordered))
    video = dest / f"{scene}.mp4"
    rc = subprocess.run([ffmpeg, "-y", "-hide_banner", "-nostats", "-loglevel", "error", "-f", "concat",
                         "-safe", "0", "-i", str(listing), "-map", "0:v:0", "-c", "copy",
                         "-movflags", "+faststart", str(video)], stdout=log, stderr=subprocess.STDOUT).returncode
    if rc != 0 or not video.is_file():
        res.update(status="failed", reason=f"ffmpeg concat failed (exit {rc})")
        return res

    # GeometryGuard: each animation's measurement from the worker that drew it.
    dumps = [w["dir"] / "geometry.json" for w in procs]
    if all(d.is_file() for d in dumps):
        merged = json.loads(dumps[-1].read_text())
        snaps = []
        for w, d in zip(procs, dumps):
            own = range(w["first"], w["last"] + 1)
            snaps += [s for s in json.loads(d.read_text()).get("snapshots", []) if s.get("anim") in own]
        merged["snapshots"] = sorted(snaps, key=lambda s: s["anim"])
        try:
            import geometry_qa
            merged["summary"] = geometry_qa.summarize_dump(merged)
        except Exception as exc:  # keep the last worker's summary
            log.write(f"parallel: could not re-summarize geometry: {exc}\n")
        gpath = env.get("GEOMETRY_JSON")
        if gpath:
            Path(gpath).write_text(json.dumps(merged, indent=1) + "\n")
    res["timings"]["join"] = round(time.monotonic() - t2, 2)
    res.update(status="ok", video=str(video), partial_list=str(listing))
    return res


def main(argv: list[str]) -> int:
    if len(argv) >= 3 and argv[0] in ("plan", "worker") and "--" in argv:
        i = argv.index("--")
        if argv[0] == "plan":
            return cmd_plan(argv[1], argv[i + 1:])
        return cmd_worker(int(argv[1]), argv[i + 1:])
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
