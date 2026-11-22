---
name: manim-video
description: Makes explanatory animated videos (math, computer science, ML, engineering) with Manim Community v0.22. Runs a mandatory plan, render, watch-the-frames, judge, fix loop and delivers a reviewed MP4, silent or with Kokoro TTS narration. Use when asked for an animation, animated diagram, explainer video or 3Blue1Brown-style visualisation.
license: MIT
compatibility: Needs Docker (official Manim image) or a local Manim Community 0.22 install, plus ffmpeg/ffprobe and Python 3.11+ on the host. Narration needs an OpenAI-compatible TTS server such as Kokoro.
---

# Manim video

Turn a request like "animate the unit circle and its trig functions" into a short, correct,
intuitive explainer video. You plan it, write Manim code, render a fast preview, **look at the
frames yourself**, judge whether a newcomer would follow it, fix what is wrong, repeat, and only
then render the final file.

`SKILL_DIR` below means the directory that contains this `SKILL.md` (for example
`~/.agents/skills/manim-video`). Set it once in your shell: `SKILL_DIR=/path/to/manim-video`.
Every other path in this file is relative to `SKILL_DIR`.

## Ground rules

- **Manim Community v0.22.1 only.** Start every scene file with `from manim import *`.
  Never use ManimGL (3b1b/manim) idioms; they fail or misbehave here:
  `manimlib`, `ShowCreation`, `CONFIG = {...}`, `self.embed()`, `TexText`, `InteractiveScene`,
  `GraphScene`, `TexMobject`, `TextMobject`, `.fix_in_frame()`. `render.sh` refuses files that
  contain them. The translation table is in [references/api-cheatsheet.md](references/api-cheatsheet.md).
- **Render only with `scripts/render.sh`.** It is headless: never pass `-p` or open a player.
- **Never skip the watch step.** A render that exits 0 can still have overlapping labels,
  clipped equations or objects that never leave. You must look at the stills.
- **Intuition first.** Unless the user asks for rigour, aim for a 3Blue1Brown-style explanation
  (see Step 1). Go deeper only on request.
- **No root.** Install nothing with `sudo`. If a system package is truly required, stop and tell
  the user exactly what is missing.
- **Secrets.** The TTS key, if any, comes from `KOKORO_API_KEY` in the environment. Never print
  it, write it to a file, or put it in scene code.

## Step 0: check the tools and ask about narration

1. Run `"$SKILL_DIR/scripts/check_env.sh"`. If it prints `RESULT: NOT READY`, run
   `"$SKILL_DIR/scripts/setup_env.sh"` (user space only: a static ffmpeg and the Docker image),
   then check again. If it still fails, stop and report the FAIL lines. Recipe and options:
   [references/environment.md](references/environment.md).
2. **Ask the user before planning**, in one short message:
   - "Do you want spoken narration (Kokoro text-to-speech), or a silent video?"
   - Only if unclear from the request: audience, depth, target length.

   If the user does not answer, or nobody can answer (an unattended run), use the defaults and
   say so in the final report: **silent**, newcomer audience with high-school maths, intuitive
   depth, 60 to 150 seconds, 16:9 at 1920x1080, 60 fps.
3. Make a project directory for this video, for example `./manim/<slug>/` in the current
   workspace (or where the user says). The scene file, assets, `storyboard.md` and `review.md`
   live there; renders go to its `media/` folder. Only this directory is visible to the renderer.

## Step 1: plan a storyboard

Copy [templates/storyboard.md](templates/storyboard.md) into the project and fill it in before
writing any code:

- **Learning goal:** one sentence the viewer could say afterwards ("tan is the length of the
  tangent segment, which is why it blows up at 90 degrees").
- **Colour legend:** each concept gets one colour for the whole video (sin = blue, cos = red...).
- **Beats:** a table of 5 to 15 beats. Each beat has one idea, its visual metaphor, what appears
  and leaves, at most one short line of on-screen text, its duration and (if narrated) the
  narration sentence(s).
- **Total duration** and what you are deliberately leaving out.

Intuition principles (the default; check them again in Step 5):

1. **Start from a concrete picture** the viewer already understands, not a definition.
2. **One idea per beat.** If a beat needs "and", split it.
3. **Show why before the formula.** The symbol arrives as a label for something already seen.
4. **Visual metaphor before formalism:** lengths, areas, motion, flow, before notation.
5. **Progressive reveal:** build the diagram piece by piece; never show the finished picture first.
6. **Consistent colour coding** that matches the legend, in shapes, labels and equations alike.
7. **Minimal on-screen text:** labels and key formulas, not sentences. Let motion explain.
8. **Every step is motivated:** each beat answers a question the previous beat raised.
9. **Pause after each reveal** (1 to 2 s) and end with a recap that ties the pieces together.

**Depth on request.** When the user asks for derivations, rigour, edge cases or notation, keep
the same picture-first spine and add beats: the derivation steps (with `TransformMatchingTex`),
the edge cases shown visually, and precise notation once the picture is established.

**Scope.** Broad prompts ("git: commit, branching, merging, rebasing, conflict strategies, in an
enterprise") need a narrative, not a catalogue: group them into 3 to 6 chapters of 20 to 40 s,
each with its own small diagram, and keep the whole under about 3 minutes unless asked for more.
List what you cut in the final report. Patterns for common subjects (trig on a circle, neural
networks, commit graphs, rotating-vector series, gradient descent):
[references/scene-patterns.md](references/scene-patterns.md).

## Step 2: write the scene

Start from [templates/scene_silent.py](templates/scene_silent.py) or
[templates/scene_narrated.py](templates/scene_narrated.py). Follow
[references/style-guide.md](references/style-guide.md) (palette, fonts, sizes, margins) and use
[references/api-cheatsheet.md](references/api-cheatsheet.md) for the API.

- One `Scene` class for the whole video, with one method per beat (`def beat_unit_circle(self)`).
  Mix in the layout checker: `class Explainer(LayoutGuard, Scene)`. It logs clipped, off-screen
  and overlapping text after every animation.
- Put the colour legend at the top of the file as constants and use only those.
- **Layout:** keep everything inside the safe area (x within ±6.4, y within ±3.4). Position with
  `next_to`, `arrange`, `to_edge(buff=0.5)` and `align_to`, not hard-coded coordinates. Reserve
  zones: title band at the top, main diagram in the middle, formulas to the side.
- **Text:** `Text` for words (set the font as the template does), `MathTex` for maths (needs
  LaTeX, available in the Docker image). Sizes: titles 40 to 48, labels at least 28, never below
  24. At most two lines per text object.
- **Lifecycle:** every object that appears must leave (`FadeOut`) or be deliberately kept for the
  next beat. Clear the stage between chapters. With `Transform(a, b)`, keep animating `a`
  afterwards (it now looks like `b`); with `ReplacementTransform(a, b)`, use `b`. Mixing these
  up leaves ghost copies.
- **Live diagrams:** drive moving values with `ValueTracker` and rebuild dependent shapes with
  `always_redraw`, so labels and lines stay attached. Remove updaters (or the redrawn objects)
  when the beat ends.
- **Timing:** `run_time` 1 to 2 s for most animations, `self.wait(1)` to `self.wait(2)` after
  each key reveal, `LaggedStart` for groups. The total should match the storyboard.
- **Determinism:** no unseeded randomness; no network access in silent scenes.

## Step 3: render a fast preview

```bash
"$SKILL_DIR/scripts/render.sh" preview scene.py Explainer
```

This renders 854x480 at 15 fps (seconds to a minute or two) and prints `VIDEO: <path>` plus any
`LAYOUT` warnings. Fix render errors first ([references/troubleshooting.md](references/troubleshooting.md)).
To iterate on one section, render only some animations: `render.sh preview scene.py Explainer -- -n 12,20`.

## Step 4: watch it (mandatory)

1. Run the headless checks:
   `python3 "$SKILL_DIR/scripts/qa_check.py" <video> [--expect-audio | --expect-silent]`.
   It reports empty-screen stretches, stalls, abrupt pop-ins or flicker, audio problems and
   stream sanity. Treat every FAIL as a bug; explain or fix every WARN.
2. Extract stills: `python3 "$SKILL_DIR/scripts/frames.py" <video> --beats --mid`.
   This saves the resting frame after every animation (and the midpoint of each transition),
   contact sheets `sheet_NN.png`, and `index.txt` mapping tiles to times and beats.
3. **Open and look at every contact sheet image**, then open the full-size still for any beat
   where text is small, objects are close together, or something looks off. Judge small text at
   full resolution: `render.sh still scene.py Explainer -- -n 0,K` renders the frame after
   animation K at 1920x1080.
4. Go through [references/visual-qa-checklist.md](references/visual-qa-checklist.md) beat by
   beat: overlaps, clipping, off-screen content, leftovers that never leave, unreadable text,
   LaTeX glitches, wrong or inconsistent colours, flicker or pop-ins, and pacing. Log every
   finding in `review.md` (from [templates/review.md](templates/review.md)) with its beat and time.

If you cannot view images in this environment, say so to the user and do not claim a visual
review; rely on the headless checks and ask the user to watch the preview.

## Step 5: judge intuitiveness

Score the preview against [references/intuition-rubric.md](references/intuition-rubric.md):
write the newcomer summary (what a first-time viewer would take away) and score each criterion
0 to 2 in `review.md`. A leap (a step that is not motivated or not shown) is a bug, the same as
an overlap.

## Step 6: fix and re-render, until you are confident the user will approve

Fix every bug and every rubric item below 2 that a change can fix, then go back to Step 3.
Re-watch at least the changed beats and the full contact sheet each time. Stop iterating when:

- no open visual bugs remain in `review.md`,
- `qa_check.py` reports no FAIL, and every WARN is explained,
- the rubric passes (no criterion at 0, total at least 15 of 20), and
- you would show it to the user without caveats.

**Cap:** 6 preview iterations. If it is still not right by then, stop, render nothing final, and
report to the user what remains and what you would try next. Never ship a known-broken video
silently.

## Step 7: final render and report

```bash
"$SKILL_DIR/scripts/render.sh" final scene.py Explainer
python3 "$SKILL_DIR/scripts/qa_check.py" <final.mp4> --expect-res 1920x1080 [--expect-audio]
python3 "$SKILL_DIR/scripts/frames.py" <final.mp4> --count 8
```

Look at the final contact sheet once more (high resolution can reveal thin strokes or tiny text
that the preview hid). Then deliver: the absolute path of the MP4, its duration and resolution,
and the final report from `review.md`: assumptions (including the narration choice), the
storyboard in one paragraph, iterations used, bugs found and fixed, what was checked
(automated and visual), rubric scores, and known limitations.

## Narration (only if the user said yes)

- Write the narration in the storyboard beat by beat: conversational, about 2.5 words per
  second, sentences under 20 words. The voice says *why*; the screen shows *what*. Do not put
  the narration on screen as text.
- Use manim-voiceover with the bundled Kokoro service (`templates/scene_narrated.py`):
  `self.set_speech_service(KokoroService())`, then animate inside
  `with self.voiceover(text=...) as tracker:` using `run_time=tracker.duration`, so the animation
  follows the audio. `render.sh` gives the renderer network access to the TTS server only for
  narrated scenes.
- If manim-voiceover is unavailable, use the fallback: `scripts/narrate_mux.py` synthesizes one
  WAV per beat, measures it, and muxes the clips after rendering.
- In Step 4, run `qa_check.py --expect-audio` and listen-check by reading the clip list: every
  beat's narration must start while its visual is on screen.
- Settings: `KOKORO_BASE_URL` (default `http://127.0.0.1:8880/v1`), `KOKORO_MODEL` (`kokoro`),
  `KOKORO_VOICE` (`af_heart`), optional `KOKORO_API_KEY`. Details and timing patterns:
  [references/narration.md](references/narration.md).

## Files

| Path | Use |
|---|---|
| `scripts/check_env.sh` | read-only check of renderer, LaTeX, ffmpeg, Python, Kokoro (`--tts` for a test clip) |
| `scripts/setup_env.sh` | user-space install: static ffmpeg, Docker image with manim-voiceover |
| `scripts/render.sh` | `preview`, `final` or `still` render; prints `VIDEO:`/`IMAGE:` paths and layout warnings |
| `scripts/qa_check.py` | headless checks: streams, audio, empty screen, stalls, pop-ins and flicker |
| `scripts/frames.py` | stills at every beat, evenly spaced or at given times, plus contact sheets |
| `scripts/manim_qa.py` | `LayoutGuard` scene mixin: clipped, off-screen and overlapping text |
| `scripts/kokoro_service.py` | `KokoroService` for manim-voiceover |
| `scripts/narrate_mux.py`, `scripts/narration_timeline.py` | narration fallback: WAV per beat, timeline, mux |
| `references/api-cheatsheet.md` | Manim Community API, ManimGL translation table |
| `references/scene-patterns.md` | reusable patterns for common explainer subjects |
| `references/style-guide.md` | palette, fonts, sizes, layout grid, timing |
| `references/visual-qa-checklist.md` | the bug hunt for Step 4 |
| `references/intuition-rubric.md` | the scoring rubric for Step 5 |
| `references/narration.md` | narration writing, voiceover sync, fallback |
| `references/troubleshooting.md` | LaTeX, fonts, Cairo/Pango, Docker, audio problems |
| `references/environment.md` | the render recipe and its options |
| `templates/` | storyboard, review log, silent and narrated scene skeletons, narration JSON |
