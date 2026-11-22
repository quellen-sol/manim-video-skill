"""Find working ffmpeg/ffprobe binaries for the helper scripts (stdlib only)."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from functools import cache
from pathlib import Path

HOME_BIN = Path(os.environ.get("MANIM_VIDEO_HOME", Path.home() / ".local/share/manim-video")) / "bin"


@cache
def tool(name: str) -> str:
    """Return a path to `name` that actually runs.

    Order: $FFMPEG/$FFPROBE, then the user-space static build in $MANIM_VIDEO_HOME/bin, then PATH.
    Each candidate is test-run, because a system binary can be present but broken
    (for example a missing shared library).
    """
    candidates = [os.environ.get(name.upper()), str(HOME_BIN / name), shutil.which(name)]
    for c in candidates:
        if not c or not Path(c).exists():
            continue
        try:
            if subprocess.run([c, "-version"], capture_output=True, timeout=20).returncode == 0:
                return c
        except (OSError, subprocess.TimeoutExpired):
            continue
    sys.exit(f"{Path(sys.argv[0]).name}: no working {name} found. Run scripts/setup_env.sh "
             f"(installs a static build into {HOME_BIN}) or set {name.upper()}=/path/to/{name}.")
