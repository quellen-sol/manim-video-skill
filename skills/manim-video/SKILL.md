---
name: manim-video
description: Makes explanatory animated videos (math, computer science, ML, engineering) with Manim Community v0.22. Runs a mandatory plan, render, watch-the-frames, judge, fix loop and delivers a reviewed MP4, silent or with Kokoro TTS narration. Use when asked for an animation, animated diagram, explainer video or 3Blue1Brown-style visualisation.
license: MIT
compatibility: Needs Docker with the compose plugin; the bundled image (built on first use) holds Manim Community 0.22.1, LaTeX, ffmpeg and the helpers. Fallback without Docker - a host Manim Community 0.22 install with LaTeX, ffmpeg and Python 3.11+. Narration needs an OpenAI-compatible TTS server such as Kokoro.
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
  `GraphScene`, `TexMobject`, `TextMobject`, `.fix_in_frame()`. The renderer refuses files that
  contain them. The translation table is in [references/api-cheatsheet.md](references/api-cheatsheet.md).
- **Render in the container: `scripts/render-in-container.sh JOB_DIR`.** You write a job
  directory (scene, `job.json`, assets); the container renders it headlessly and writes the
  video, stills and a check report into the job's `out/`. The contract is in
  [references/container.md](references/container.md). `scripts/render.sh` (host-native Manim) is
  only a fallback for when Docker is unavailable; see the end of this file.
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
   `"$SKILL_DIR/scripts/setup_env.sh"` (builds the render image; about 6 minutes the first
   time, no root), then check again. If Docker itself is unusable, see "Host route" at the end.
   If it still fails, stop and report the FAIL lines.
2. **Ask the user before planning**, in one short message:
   - "Do you want spoken narration (Kokoro text-to-speech), or a silent video?"
   - Only if unclear from the request: audience, depth, target length.

   If the user does not answer, or nobody can answer (an unattended run), use the defaults and
   say so in the final report: **silent**, newcomer audience with high-school maths, intuitive
   depth, 60 to 150 seconds, 16:9 at 1920x1080, 60 fps.
3. Make a job directory for this video, for example `./manim/<slug>/` in the current workspace
   (or where the user says): `scene.py`, `job.json` (copy [templates/job.json](templates/job.json)
   and set `scene`), optional `assets/`, plus your `storyboard.md` and `review.md`. The container
   sees only this directory, read-only, and writes only its `out/`.

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
  Mix in the layout checker: `class Explainer(LayoutGuard, Scene)`. After every animation it logs
  clipped, off-screen, overlapping or line-crossed text, text outside the safe area, and at the
  end whatever never left the screen.
- **Geometry (mandatory, measured):** also mix in `GeometryGuard` first
  (`class Explainer(GeometryGuard, LayoutGuard, Scene)`), name the main figure's parts with
  `self.geo_track(circle=..., x_axis=..., figure=...)` and declare what must hold with
  `self.geo_rule(...)`: `concentric("circle", "x_axis", "y_axis")` (same centre; axes cross at it
  and reach equally far both ways), `symmetric("x_axis", about="circle", axis="x")`,
  `within_margin("figure", pct=7)` (at least 7% of the frame on every side) and
  `centered_in("figure", region=(x0, y0, x1, y1))` (centred in its half, panel or the frame).
  They are measured after every animation; nothing on screen may come within 2% of the frame
  edge. `render-in-container.sh JOB_DIR --geometry` re-measures them in seconds without
  rendering. Details: "Geometry" in [references/visual-qa-checklist.md](references/visual-qa-checklist.md).
- Put the colour legend at the top of the file as constants and use only those.
- **Layout:** keep everything inside the safe area (x within ±6.5, y within ±3.5). Position with
  `next_to`, `arrange`, `to_edge(buff=0.5)` and `align_to`, not hard-coded coordinates. Reserve
  zones: title band at the top, main diagram in the middle, formulas to the side. Keep captions
  under 12 units wide.
- **Text:** `Text` for words (set the font as the template does), `MathTex` for maths (LaTeX is
  in the image). Sizes: titles 40 to 48, labels at least 28, never below
  24; maths about 4 points larger than the words beside it. At most two lines per text object.
- **Swapping text:** never fade old and new text in the same `play`, and never `Transform` one
  string into a different one (both look garbled mid-transition): fade the old out, then the new
  in (the template's `swap` helper, pattern 11).
- **Highlighting:** `Indicate` stretches lines and `Circumscribe` reads as a glitch in stills.
  Flash a segment with `ShowPassingFlash(line.copy().set_stroke(YELLOW, width=8))`; box a
  formula with `SurroundingRectangle` (create, hold, fade).
- **Lifecycle:** every object that appears must leave (`FadeOut`) or be deliberately kept for the
  next beat. Clear the stage between chapters. With `Transform(a, b)`, keep animating `a`
  afterwards (it now looks like `b`); with `ReplacementTransform(a, b)`, use `b`. Mixing these
  up leaves ghost copies.
- **Live diagrams:** drive moving values with `ValueTracker` and rebuild dependent shapes with
  `always_redraw`, so labels and lines stay attached. Updaters must be lambdas or plain functions,
  never bound methods (`add_updater(self.place)` crashes the render). Call `clear_updaters()`
  before you fade or transform a redrawn object, and remove it when the beat ends.
- **Timing:** `run_time` 1 to 2 s for most animations, `self.wait(1)` to `self.wait(2)` after
  each key reveal, `LaggedStart` for groups. The total should match the storyboard.
- **Determinism:** no unseeded randomness; no network access in silent scenes.

## Step 3: render a fast preview

```bash
"$SKILL_DIR/scripts/render-in-container.sh" ./manim/<slug>      # job.json "quality": "preview"
```

This renders 854x480 at 15 fps (seconds to a few minutes; a 1080p60 final of a 2-minute video
takes 15 to 25 minutes on 4 cores), runs the automated checks and extracts stills, and prints `VIDEO:`, `SHEET:`, `INDEX:`, `REPORT:` and `LOG:` paths. Exit
status 4 means the render failed (the log tail is printed; LaTeX errors are flagged); 1 means a
check FAILed. `out/report.md` says whether the layout guard ran and lists its `LAYOUT` warnings
(`CLIPPED`, `UNSAFE`, `OFFSCREEN`, `OVERLAP`, `CROSSED`, `END`). Treat each warning as a bug
unless you can see it is intended (then `self.qa_ignore(mob)`). Fix render errors first
([references/troubleshooting.md](references/troubleshooting.md)). After the first preview, update
the storyboard's times to match the real length. To iterate on one section, render only some
animations: `--animations 12,20` (or `"animations": "12,20"` in job.json).

## Step 4: watch it (mandatory)

1. Read `out/report.md`: the headless checks already ran (stream sanity, empty-screen
   stretches, stalls, abrupt pop-ins or flicker, audio, the layout warnings, and the measured
   **geometry** check with the animation and time of each violation). Treat every FAIL as a bug;
   explain or fix every WARN. A geometry FAIL is never "intended": fix the layout.
2. The stills are already extracted in `out/stills/`: the resting frame after every animation
   and the midpoint of each transition, contact sheets `sheet_NN.png`, and `index.txt` mapping
   tiles to times and animation numbers. More, without re-rendering:
   `render-in-container.sh JOB_DIR --frames --from S --to S` (a time window), `--frames --count 16`
   (an overview) or `--frames --at 12.5,31`; they go to `out/frames/`.
3. **Open and look at the contact sheet images.** First preview: every sheet. Later previews:
   the sheets for what you changed plus an overview of the whole video. Open the full-size still
   for any frame where text is small, objects are close together, or something looks off.
4. **Check the busiest 2 or 3 frames at full resolution every iteration:** the 480p preview hides
   collisions of a few pixels. `render-in-container.sh JOB_DIR --still K` renders the frame after
   animation K (the `anim K` number in `index.txt`) at 1920x1080 into `out/stills-full/`.
5. Go through [references/visual-qa-checklist.md](references/visual-qa-checklist.md) beat by
   beat: overlaps, clipping, off-screen content, leftovers that never leave, unreadable text,
   LaTeX glitches, wrong or inconsistent colours, flicker or pop-ins, and pacing. Log every
   finding in `review.md` (from [templates/review.md](templates/review.md)) with its beat and time.

If you cannot view images in this environment, say so to the user and do not claim a visual
review; rely on the headless checks and ask the user to watch the preview.

## Step 5: judge intuitiveness

Score the preview against [references/intuition-rubric.md](references/intuition-rubric.md):
write the newcomer summary (what a first-time viewer would take away) and score each criterion
0 to 2 in `review.md`. A leap (a step that is not motivated or not shown) is a bug, the same as
an overlap. **A geometry FAIL in `out/report.md` (or no geometry rules for the main figure) caps
the total at 15 of 20.**

## Step 6: fix and re-render, until you are confident the user will approve

Fix every bug and every rubric item below 2 that a change can fix, then go back to Step 3.
Each time, re-watch the changed beats (stills and full-resolution frames) and an overview of the
whole video. Stop iterating when:

- no open visual bugs remain in `review.md`,
- `out/report.md` shows no FAIL (geometry included, with no `UNCHECKED` rule), and every WARN is
  explained,
- the rubric passes (no criterion at 0, total at least 15 of 20), and
- you would show it to the user without caveats.

**Cap:** 6 preview iterations. If it is still not right by then, stop, render nothing final, and
report to the user what remains and what you would try next. Never ship a known-broken video
silently. A fix that changes a single static frame (a nudged label) may be verified with a
full-resolution `--still K` instead of a whole preview; anything that changes motion or timing
needs a preview.

## Step 7: final render and report

```bash
"$SKILL_DIR/scripts/render-in-container.sh" ./manim/<slug> --quality final
```

This writes `out/<Scene>-final.mp4` (1920x1080 at 60 fps), checks it (including the resolution
and, if narrated, the audio) and extracts 8 evenly spaced stills. Look at the final contact sheet once more, and open 2 or 3 of its frames at full size (high
resolution can reveal thin strokes or tiny text that the preview hid). If the final shows a bug,
go back to Step 6 (it counts as an iteration) and render the final again. Then deliver: the
absolute path of `out/<Scene>-final.mp4`, its duration and resolution, and the final report from `review.md`: assumptions (including the narration choice), the
storyboard in one paragraph, iterations used, bugs found and fixed, what was checked
(automated and visual), rubric scores, and known limitations.

## Narration (only if the user said yes)

- Write the narration in the storyboard beat by beat: conversational, about 2.5 words per
  second, sentences under 20 words. The voice says *why*; the screen shows *what*. Do not put
  the narration on screen as text.
- In job.json set `"narration": {"enabled": true, "voice": "af_heart"}` and put the sentences in
  `narration.script` as `{"beats": [{"id": "intro", "text": "..."}]}`. Only narrated jobs get
  network access (to the TTS server, as `host.docker.internal`) and the key; the wrapper passes
  `KOKORO_API_KEY` by name and never prints it.
- Use manim-voiceover with the bundled Kokoro service (`templates/scene_narrated.py`):
  `self.set_speech_service(KokoroService())`, then animate inside
  `with self.voiceover(text=line("intro")) as tracker:` (`from narration_script import line`
  reads the words from job.json) using `run_time=tracker.duration`, so the animation follows
  the audio. Use one `voiceover` block per clause that has its own visual change, rather than
  splitting one long sentence by guessed fractions. Narrated renders always disable Manim's
  animation cache, which would let the picture drift from the audio.
- If manim-voiceover is unavailable, use the fallback: `"mode": "mux"` synthesizes one WAV per
  beat first, the scene paces itself with `narration_timeline.Timeline()`, and the clips are
  muxed after rendering.
- In Step 4, the report checks the audio; then check sync with the subtitle file manim-voiceover
  writes: `render-in-container.sh JOB_DIR --frames --cues` takes one still in the middle of every
  sentence, labelled with its text, so you can see each sentence's visual.
- Details and timing patterns: [references/narration.md](references/narration.md).

## Files

| Path | Use |
|---|---|
| `scripts/render-in-container.sh` | **the renderer**: job dir in, `out/` with video, report, stills; `--frames`, `--still K`, `--doctor`, `--build` |
| `docker/` | the image (`Dockerfile`, pinned `requirements.lock`), `compose.yml` and the opt-in `compose.gpu.yml` |
| `scripts/check_env.sh` | read-only check of the container route (`--host`: host route; `--gpu`; `--tts`; `--fonts`) |
| `scripts/setup_env.sh` | builds the image (`--host`: the host-route venv) |
| `scripts/render.sh` | host route only: `preview`, `final` or `still` with a host-native Manim |
| `scripts/qa_check.py` | headless checks (run for you in the container): streams, audio, empty screen, stalls, pop-ins |
| `scripts/frames.py` | stills (run for you in the container): per animation, evenly spaced, at times, per hold or subtitle cue |
| `scripts/manim_qa.py` | `LayoutGuard` scene mixin: clipped, unsafe, off-screen, overlapping and crossed text, leftovers |
| `scripts/geometry_qa.py` | `GeometryGuard` scene mixin: measured `concentric`, `symmetric`, `within_margin`, `centered_in` rules |
| `scripts/kokoro_service.py`, `scripts/narration_script.py` | `KokoroService` for manim-voiceover; `line(id)` reads narration from job.json |
| `scripts/narrate_mux.py`, `scripts/narration_timeline.py` | narration fallback: WAV per beat, timeline, mux |
| `references/api-cheatsheet.md` | Manim Community API, ManimGL translation table |
| `references/scene-patterns.md` | reusable patterns for common explainer subjects |
| `references/style-guide.md` | palette, fonts, sizes, layout grid, timing |
| `references/visual-qa-checklist.md` | the bug hunt for Step 4 |
| `references/intuition-rubric.md` | the scoring rubric for Step 5 |
| `references/narration.md` | narration writing, voiceover sync, fallback |
| `references/troubleshooting.md` | LaTeX, fonts, Cairo/Pango, Docker, audio problems |
| `references/container.md` | the job contract, job.json keys, narration and GPU in the container, benchmarks |
| `references/environment.md` | the host route (fallback) and environment variables |
| `templates/` | job.json, storyboard, review log, silent and narrated scene skeletons, narration JSON |

## Host route (fallback, only without Docker)

If Docker is unavailable, `"$SKILL_DIR/scripts/setup_env.sh" --host` sets up a host-native Manim
(it needs system packages it cannot install; it lists them). Then the same loop works on a plain
project directory: `scripts/render.sh preview|final scene.py Explainer` (add `-- -n 12,20` for a
section), `python3 scripts/qa_check.py <video> [--expect-audio | --expect-silent]`,
`python3 scripts/frames.py <video> --anims --mid`, and `render.sh still scene.py Explainer -- -n 0,K`.
Details: [references/environment.md](references/environment.md).
