"""Scene-side helper for the narrate_mux.py fallback (narration without manim-voiceover).

    from narration_timeline import Timeline
    TL = Timeline("audio/timeline.json")          # written by: narrate_mux.py tts narration.json

    class Explainer(Scene):
        def construct(self):
            TL.sync(self, "intro")                  # waits until the intro clip starts
            self.play(Create(circle), run_time=TL.speech("intro"))
            TL.sync(self, "sine")                   # pads with a wait, or warns if running late
            ...
            TL.finish(self)                         # holds until the last clip has ended

Run the scene from its project directory (render.sh does), so the relative path resolves.
Late beats print a line starting with NARRATION, which render.sh shows.
"""

from __future__ import annotations

import json
from pathlib import Path


class Timeline:
    def __init__(self, path: str | Path = "audio/timeline.json"):
        data = json.loads(Path(path).read_text())
        self.lead_in = float(data.get("lead_in", 0))
        self.total = float(data["total"])
        self.beats = {b["id"]: b for b in data["beats"]}

    def start(self, beat_id: str) -> float:
        return float(self.beats[beat_id]["start"])

    def speech(self, beat_id: str) -> float:
        """Seconds of speech in this beat: a good run_time for its main animation."""
        return float(self.beats[beat_id]["duration"])

    def slot(self, beat_id: str) -> float:
        """Seconds reserved for this beat: speech plus the gap after it."""
        return float(self.beats[beat_id]["slot"])

    def sync(self, scene, beat_id: str) -> None:
        """Call at the top of each beat: waits until its clip starts."""
        now = scene.renderer.time
        start = self.start(beat_id)
        if now < start - 1e-3:
            scene.wait(start - now)
        elif now > start + 0.1:
            print(f"NARRATION beat {beat_id!r} should start at {start:.2f}s but the scene is already at "
                  f"{now:.2f}s: shorten the previous beat's animations", flush=True)

    def finish(self, scene, tail: float = 0.5) -> None:
        """Hold until the narration has ended, plus a short tail."""
        remaining = self.total + tail - scene.renderer.time
        if remaining > 1e-3:
            scene.wait(remaining)
