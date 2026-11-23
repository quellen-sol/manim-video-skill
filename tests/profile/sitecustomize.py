"""Time-split profiler for one Manim render (tests/profile_render.sh mounts this directory).

Imported by every Python process in the container when this directory is on PYTHONPATH, but it
only acts in the `manim` process and only when MANIM_PROFILE_OUT is set. It wraps a few Manim
functions with wall-clock timers and attributes *exclusive* time (minus time in nested wrapped
calls) to a stage, separately for the main (drawing) thread and the partial-movie encoder
threads. At exit it writes the totals, call counts and CPU use (getrusage) to MANIM_PROFILE_OUT.
Overhead: a few microseconds per wrapped call, a handful of calls per frame.
"""
import os
import sys

_OUT = os.environ.get("MANIM_PROFILE_OUT")
_argv = getattr(sys, "orig_argv", sys.argv)
if _OUT and len(_argv) > 1 and os.path.basename(_argv[1]) == "manim":
    try:
        import manim_profile_hooks
        manim_profile_hooks.install(_OUT)
    except Exception as exc:  # never break a render
        print(f"PROFILE hook error {type(exc).__name__}: {exc}", flush=True)
