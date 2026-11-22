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
POSTs to an OpenAI-compatible `/v1/audio/speech` endpoint. It is on `PYTHONPATH` in the render
image (and under `render.sh` on the host route). In the container, set
`"narration": {"enabled": true}` in job.json: only then does the job get network access to the
TTS server (as `host.docker.internal`) and the key.

Keep the words in job.json (`narration.script`, `{"beats": [{"id": "intro", "text": "..."}]}`)
and read them in the scene with `from narration_script import line`, then
`with self.voiceover(text=line("intro")) as tracker:`. You can then rewrite a sentence without
touching the code. Plain strings in `self.voiceover(text="...")` work too. If the scene already
uses `line` as a variable name (a `NumberLine`, say), import it under another name:
`from narration_script import line as say`.

manim-voiceover's audio track stops after the last clip, so a silent outro leaves it shorter than
the picture. In the container, the delivered video's audio is padded with silence to the video's
length, and `out/report.md` checks it (`av_length`: AAC, within 0.1 s of the video).

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

- **One `voiceover` block per clause that has its own visual change.** Inside a block, several
  animations share the clip's time (fractions of `tracker.duration`, finishing with
  `tracker.get_remaining_duration()`), but the fractions are guesses about where words fall;
  separate blocks put each visual exactly on its words.
- When the block's animations end before the speech, manim-voiceover waits for the speech to
  finish at the end of the block, so a sentence is never cut off.
- Add `self.wait(0.3)` to `self.wait(1)` between blocks when a pause helps.
- Options: `KokoroService(voice="am_michael", speed=1.0)`. List voices with
  `curl -s $KOKORO_BASE_URL/audio/voices`.
- Clips are cached in `media/voiceovers/` (with `cache.json`); re-renders only synthesize
  sentences whose text changed. Delete nothing there by hand during iteration. The first render
  of a long narrated scene is slow (Kokoro on CPU synthesizes each sentence); later ones reuse
  the clips.
- Manim's own animation cache is different: reusing cached partial movies lets the picture drift
  from the audio by up to a frame per animation, so both routes pass `--disable_caching` for
  narrated renders. Leave it on.
- manim-voiceover writes `<Scene>.srt` next to the video, with every sentence's exact start and
  end. `render-in-container.sh JOB_DIR --frames --cues` (host: `frames.py VIDEO --cues`) takes
  one still per sentence, labelled with its text: the sync check for Step 4. The same file can be shipped as subtitles.
- Word-level bookmarks (`<bookmark mark="A"/>` with `self.wait_until_bookmark("A")`) need a
  transcription model (the `transcribe` extra, Whisper), which is not installed. Use separate
  `voiceover` blocks per sentence instead.

## Fallback: one WAV per beat, then mux

Use this when manim-voiceover cannot be installed or imported in the renderer.

**In the container** it is one setting: `"narration": {"enabled": true, "mode": "mux",
"script": "narration.json"}`. The container synthesizes and measures one WAV per beat before
rendering (into `out/audio/`), sets `NARRATION_TIMELINE` so `Timeline()` finds it, renders, then
muxes the clips onto the video and checks the audio. Write the scene as in step 3 below.

**On the host route**, by hand:

1. Write `narration.json` (template: `templates/narration.json`): beat ids, text, optional
   per-beat `gap`.
2. Synthesize and measure: `python3 "$SKILL_DIR/scripts/narrate_mux.py" tts narration.json`.
   This writes `audio/NN_<id>.wav` and `audio/timeline.json` with each beat's start, speech
   duration and slot. Unchanged beats are not re-synthesized.
3. Time the scene from the timeline with `scripts/narration_timeline.py` (on `PYTHONPATH` under
   `render.sh`):

   ```python
   from narration_timeline import Timeline
   TL = Timeline()          # audio/timeline.json, or $NARRATION_TIMELINE in the container
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
files, logs or reports, or pass it on a command line. In the container route,
`render-in-container.sh` passes it to narrated jobs by name only (silent jobs never get it); if it
is not set, it reads only the `KOKORO_API_KEY=` line from `KOKORO_ENV_FILE` (default
`~/.config/agent-stack/gateway.env`, if readable). In job.json, `narration.voice` and
`narration.kokoro.base_url`/`model` override the variables above.

## Checks specific to narration

- The automated checks (`out/report.md`; host: `qa_check.py --expect-audio`): audio stream present, not silent, not clipping, narration not
  cut off at the end, no long gaps in speech.
- `--frames --cues` (host: `frames.py VIDEO --cues`): confirm each sentence's still shows what
  the sentence talks about.
- If a beat feels rushed, lengthen the sentence's animations or add a short pause; if it drags,
  tighten the sentence rather than speeding up the voice.
