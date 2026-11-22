"""Narration text by beat id, read from the job's narration script (job.json "narration.script").

    from narration_script import line
    with self.voiceover(text=line("intro")) as tracker:
        self.play(Create(circle), run_time=tracker.duration)

The script uses the narrate_mux.py format: {"beats": [{"id": "intro", "text": "..."}, ...]}.
Inside the render container, manim-job sets NARRATION_SCRIPT to the script file (or to a copy of
an inline script). Elsewhere, set NARRATION_SCRIPT or pass the path: line("intro", "narration.json").
Keeping the words in job.json means narration can be edited without touching scene code.
"""

from __future__ import annotations

import json
import os
from functools import cache
from pathlib import Path


@cache
def _load(path: str) -> dict[str, str]:
    data = json.loads(Path(path).read_text())
    beats = data.get("beats", []) if isinstance(data, dict) else data
    return {b["id"]: b["text"] for b in beats}


def _path(path: str | None) -> str:
    return str(path or os.environ.get("NARRATION_SCRIPT") or "narration.json")


def line(beat_id: str, path: str | None = None) -> str:
    """The narration text for one beat."""
    p = _path(path)
    beats = _load(p)
    if beat_id not in beats:
        raise KeyError(f"narration script {p} has no beat {beat_id!r}; it has: {', '.join(beats)}")
    return beats[beat_id]


def beat_ids(path: str | None = None) -> list[str]:
    """Beat ids in script order."""
    return list(_load(_path(path)))
