"""Wall-clock stage timers for a Manim Community 0.22 Cairo render (see sitecustomize.py)."""
import atexit
import functools
import importlib
import json
import resource
import threading
import time

T_START = time.perf_counter()
_tls = threading.local()
_lock = threading.Lock()
ACC: dict = {}      # (thread kind, stage) -> seconds (exclusive)
CNT: dict = {}
MARKS: dict = {}


def _kind() -> str:
    name = threading.current_thread().name
    return "encoder" if name.startswith("partial-movie-encoder") else ("main" if name == "MainThread" else "other")


def _wrap(stage: str, fn):
    @functools.wraps(fn)
    def inner(*a, **k):
        st = getattr(_tls, "stack", None)
        if st is None:
            st = _tls.stack = []
        t0 = time.perf_counter()
        st.append(0.0)
        try:
            return fn(*a, **k)
        finally:
            el = time.perf_counter() - t0
            child = st.pop()
            key = (_kind(), stage)
            with _lock:
                ACC[key] = ACC.get(key, 0.0) + el - child
                CNT[key] = CNT.get(key, 0) + 1
            if st:
                st[-1] += el
    inner.__profiled__ = True
    return inner


def _patch(modname: str, qual: str, stage: str) -> bool:
    try:
        mod = importlib.import_module(modname)
    except Exception:
        return False
    parts = qual.split(".")
    owner = mod
    for p in parts[:-1]:
        owner = getattr(owner, p, None)
        if owner is None:
            return False
    fn = getattr(owner, parts[-1], None)
    if fn is None or getattr(fn, "__profiled__", False):
        return False
    if isinstance(owner, type) and isinstance(owner.__dict__.get(parts[-1]), staticmethod):
        setattr(owner, parts[-1], staticmethod(_wrap(stage, fn)))
    else:
        setattr(owner, parts[-1], _wrap(stage, fn))
    return True


TARGETS = [
    # main thread: building the scene
    ("manim.utils.tex_file_writing", "compile_tex", "latex: tex -> dvi (latex subprocess)"),
    ("manim.utils.tex_file_writing", "convert_to_svg", "latex: dvi -> svg (dvisvgm subprocess)"),
    ("manim.mobject.svg.svg_mobject", "SVGMobject.init_svg_mobject", "svg: parse + build paths"),
    ("manim.mobject.text.text_mobject", "Text._text2svg", "text: Pango -> svg"),
    ("manim.mobject.text.text_mobject", "MarkupText._text2svg", "text: Pango -> svg"),
    # main thread: per frame
    ("manim.scene.scene", "Scene.update_to_time", "animate: interpolate + updaters (Python)"),
    ("manim.camera.camera", "Camera.capture_mobjects", "cairo: draw frame"),
    ("manim.camera.camera", "Camera.reset", "cairo: clear/copy background"),
    ("manim.camera.camera", "Camera.set_frame_to_background", "cairo: clear/copy background"),
    ("manim.renderer.cairo_renderer", "CairoRenderer.get_frame", "frame: copy pixel array"),
    ("manim.renderer.cairo_renderer", "get_hash_from_play_call", "cache: hash play call"),
    ("manim.scene.scene_file_writer", "SceneFileWriter.write_frame", "encode wait: frame queue full"),
    ("manim.scene.scene_file_writer", "SceneFileWriter.open_partial_movie_stream", "encode: open segment"),
    ("manim.scene.scene_file_writer", "SceneFileWriter.close_partial_movie_stream", "encode wait: end of animation"),
    ("manim.scene.scene_file_writer", "SceneFileWriter.join_all_encode_jobs", "encode wait: end of animation"),
    ("manim.scene.scene_file_writer", "SceneFileWriter.combine_to_movie", "concat: partial movies -> mp4"),
    ("manim.renderer.cairo_renderer", "CairoRenderer.play", "scene: other per-play Python"),
    ("manim.scene.scene", "Scene.render", "scene: construct() and setup outside play"),
    # encoder threads
    ("manim.scene.video_segment_encoder", "VideoSegmentEncoder.write_frame", "encoder thread: rgba->yuv + x264"),
    ("manim.scene.video_segment_encoder", "VideoSegmentEncoder.finish", "encoder thread: flush + close"),
    # the skill's guards
    ("geometry_qa", "GeometryGuard._geo_check", "checks: GeometryGuard per animation"),
    ("geometry_qa", "GeometryGuard._geo_finish", "checks: GeometryGuard per animation"),
    ("manim_qa", "LayoutGuard._qa_check", "checks: LayoutGuard per animation"),
]


def _dump(path: str) -> None:
    wall = time.perf_counter() - T_START
    ru_self = resource.getrusage(resource.RUSAGE_SELF)
    ru_kids = resource.getrusage(resource.RUSAGE_CHILDREN)
    out = {
        "wall_s": round(wall, 3),
        "marks": {k: round(v - T_START, 3) for k, v in MARKS.items()},
        "cpu_self_s": round(ru_self.ru_utime + ru_self.ru_stime, 3),
        "cpu_children_s": round(ru_kids.ru_utime + ru_kids.ru_stime, 3),
        "max_rss_mb": round(ru_self.ru_maxrss / 1024, 1),
        "stages": [{"thread": k[0], "stage": k[1], "s": round(v, 3), "calls": CNT[k]}
                   for k, v in sorted(ACC.items(), key=lambda kv: -kv[1])],
    }
    with open(path, "w") as fh:
        json.dump(out, fh, indent=1)


def install(path: str) -> None:
    patched = [t for t in TARGETS if _patch(*t)]
    MARKS["hooks_installed"] = time.perf_counter()
    # The guards are imported by the scene file later: patch them when they appear.
    import builtins
    real_import = builtins.__import__
    pending = {t[0] for t in TARGETS if t not in patched}

    def hook(name, *a, **k):
        mod = real_import(name, *a, **k)
        if name in pending:
            for t in TARGETS:
                if t[0] == name:
                    _patch(*t)
            pending.discard(name)
        return mod
    builtins.__import__ = hook
    atexit.register(_dump, path)
