# Narration

Narration is optional. Ask the user before planning (SKILL.md Step 0); silent is the default.

## Writing the script

- Write it in the storyboard, one or two sentences per beat, before writing code.
- Conversational and concrete: "Watch the blue segment: that height is the sine." Not a
  textbook paragraph.
- About 2.5 words per second: a 10 s beat holds about 25 words. Sentences under 20 words.
- The voice gives the why and the connections; the screen shows the what. Never have the voice
  read on-screen text word for word, and keep on-screen text to labels.
- Spell symbols the way they should be spoken: "theta", "sine of theta", "x squared",
  "d L by d w", "git rebase". TTS reads `sin θ` or `dL/dw` badly.
- Avoid filler ("now", "so") at the start of every sentence; vary rhythm.

## Primary path: manim-voiceover with Kokoro

`scripts/kokoro_service.py` provides `KokoroService`, a manim-voiceover `SpeechService` that
POSTs to an OpenAI-compatible `/v1/audio/speech` endpoint. `render.sh` puts it on `PYTHONPATH`
and, for scenes that use it, lets the Docker renderer reach the TTS server.

```python
from manim import *
from manim_voiceover import VoiceoverScene
from kokoro_service import KokoroService

class Explainer(VoiceoverScene):
    def construct(self):
        self.set_speech_service(KokoroService())          # voice from KOKORO_VOICE, default af_heart
        with self.voiceover(text="Here is a circle of radius one.") as tracker:
            self.play(Create(circle), run_time=tracker.duration)
        with self.voiceover(text="Mark a point on it, then drop a line to the axis.") as tracker:
            self.play(FadeIn(dot), run_time=0.3 * tracker.duration)
            self.play(Create(drop), run_time=tracker.get_remaining_duration())
        self.wait(0.5)
```

- Animations inside the `with` block share the clip's time: split it with fractions of
  `tracker.duration` and finish with `tracker.get_remaining_duration()`.
- When the block's animations end before the speech, manim-voiceover waits for the speech to
  finish at the end of the block, so a sentence is never cut off.
- Add `self.wait(0.3)` to `self.wait(1)` between blocks when a pause helps.
- Options: `KokoroService(voice="am_michael", speed=1.0)`. List voices with
  `curl -s $KOKORO_BASE_URL/audio/voices`.
- Clips are cached in `media/voiceovers/` (with `cache.json`); re-renders only synthesize
  sentences whose text changed. Delete nothing there by hand during iteration.
- Word-level bookmarks (`<bookmark mark="A"/>` with `self.wait_until_bookmark("A")`) need a
  transcription model (the `transcribe` extra, Whisper), which is not installed. Use separate
  `voiceover` blocks per sentence instead.

## Fallback: one WAV per beat, then mux

Use this when manim-voiceover cannot be installed or imported in the renderer.

1. Write `narration.json` (template: `templates/narration.json`): beat ids, text, optional
   per-beat `gap`.
2. Synthesize and measure: `python3 "$SKILL_DIR/scripts/narrate_mux.py" tts narration.json`.
   This writes `audio/NN_<id>.wav` and `audio/timeline.json` with each beat's start, speech
   duration and slot. Unchanged beats are not re-synthesized.
3. Time the scene from the timeline with `scripts/narration_timeline.py` (on `PYTHONPATH` under
   `render.sh`):

   ```python
   from narration_timeline import Timeline
   TL = Timeline("audio/timeline.json")
   ...
       TL.sync(self, "intro")                       # wait until the intro clip starts
       self.play(Create(circle), run_time=TL.speech("intro"))
       TL.sync(self, "point")
       ...
       TL.finish(self)                              # hold until the narration has ended
   ```

   `sync` prints a `NARRATION` warning (shown by `render.sh`) if the scene runs late for a beat.
4. Render silently (`render.sh preview` or `final`), then mux:
   `python3 "$SKILL_DIR/scripts/narrate_mux.py" mux <video.mp4> audio/timeline.json --out final.mp4`.
5. Check with `qa_check.py final.mp4 --expect-audio`.

## Settings and secrets

| Variable | Default | Meaning |
|---|---|---|
| `KOKORO_BASE_URL` | `http://127.0.0.1:8880/v1` | OpenAI-compatible base URL |
| `KOKORO_MODEL` | `kokoro` | model name sent to the server |
| `KOKORO_VOICE` | `af_heart` | voice id |
| `KOKORO_API_KEY` | unset | optional; sent as `Authorization: Bearer` |

The key is only ever read from the environment. Do not print it, echo it, write it into scene
files, logs or reports, or pass it on a command line. `render.sh` forwards it to the container
by name only.

## Checks specific to narration

- `qa_check.py --expect-audio`: audio stream present, not silent, not clipping, audio and video
  lengths agree, no long gaps in speech.
- Look at the stills at each beat's start time and confirm the visual matches the sentence.
- If a beat feels rushed, lengthen the sentence's animations or add a short pause; if it drags,
  tighten the sentence rather than speeding up the voice.
