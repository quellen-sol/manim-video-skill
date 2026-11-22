# Review log: How a tiny network learns (gradient descent and backpropagation)

Scene: `scene.py`, class `Explainer` (`LayoutGuard`, `VoiceoverScene`). Narration: Kokoro `af_heart`
through manim-voiceover and `KokoroService`; the 38 sentences live in `job.json`
(`narration.script.beats`) and the scene reads them with `line(id)`.
Rendered only through `scripts/render-in-container.sh` (container route).

## Iteration 0 (preview of my own first scene; abandoned by a change of plan)

- My own 21-sentence scene (114.1 s, x = 2, target 2.5). Report PASS, 1 LAYOUT CROSSED warning;
  render 600 s (incl. first-time TTS), checks 11 s, stills 54 s; 666 s wall.
- Then the owner asked to start from `examples/05-gradient-descent-narrated` (scene and
  storyboard, 158.2 s earlier final) and keep its content and length. This preview is not
  counted against the cap below, but it is reported.

## Changes made to the example before preview 1

| Where | Problem in the example | Change |
|---|---|---|
| narration | 38 sentences inline in scene.py | moved to job.json `narration.script`, read with `line(id)` |
| beats 3, 13 | number line dots, gap and square bases about 25 px below the axis (README known limitation): `NumberLine(include_numbers=True).move_to()` centres line plus numbers | `number_line()` anchors value 0 on `NL_ORIGIN` (`shift(NL_ORIGIN - nl.n2p(0))`), so `nl_point(v) == nl.n2p(v)` |
| beats 3, 13 | a local variable `line = NumberLine(...)` would shadow `line()` from narration_script and crash the next voiceover | renamed to `nline` |
| beat 10 | `Indicate` on the edge arrows (stretches lines; SKILL.md) | orange `ShowPassingFlash` along each link in turn |
| beats 10, 11 | `Circumscribe` on formulas (reads as a glitch; SKILL.md) | `SurroundingRectangle` created, held, faded |
| beat 11 | `ReplacementTransform("dL/dw = ?" -> "dL/dw = -8")` morphs glyphs | `swap_tail`: only the last part fades out, then the value fades in |
| beat 12 | `Transform("w1 = 1" -> "w1 = 1.2")` scrambles glyphs | `swap_tail` |
| beat 13 | `Transform` of node values 2 -> 2.4, 1 -> 2.16, 4 -> 0.71 | fade out, then fade in |
| header | `render.sh` docstring, silent LayoutGuard fallback, ad-hoc probe | container route docstring, fallback prints, probe removed (the guard announces itself) |

## Iteration 1 (preview)

- Video: `out/Explainer-preview.mp4`, 161.13 s, 854x480 @ 15 fps, 1 audio stream.
- Timings (summary.json): render 1101.8 s (includes first-time Kokoro TTS of all 38 sentences from
  inside the container; load average about 15 on 4 cores), checks 16.0 s, stills 39.9 s; 1159 s wall.
- report.md: PASS (stream, audio mean -29.8 dB / peak -7.4 dB, blank, holds 25 %, cuts). LayoutGuard active.
  1 LAYOUT warning: `t=64.1s after animation 44: CROSSED Line ... runs through DecimalNumber(1.5)`.
- Stills looked at: all 15 contact sheets (228 tiles).

### Visual bugs

| Beat / time | Bug | Fix |
|---|---|---|
| 3 / 22-36 s | (check of the README limitation) dots, gap and square now sit ON the axis | fixed by `number_line()`; now measured by geometry rules |
| 11-13 / 132-160 s | "dL/dw1 =" and "dL/dw2 =" stay on screen after their values fade (whole of beat 13). My `swap_tail` bug: `Scene.remove(group)` does not remove members that became top-level after `FadeOut(group[-1])`, so the old "dL/dw = ?" parts stayed under the new ones. LayoutGuard did not flag the exact duplicate | `self.remove(old, *old.submobjects)` |
| 11 / about 128 s | the new highlight boxes around dL/dw1 and dL/dw2 overlap the dL/dh and dL/dy-hat labels below | node slopes one row lower (y -0.6 to -0.8), box buff 0.08 |
| 7 / 64 s | LAYOUT CROSSED: near the valley floor the tangent dips below the axis and through the "1.5" label | each tangent half stops at the axis line |
| 1-2 / 0-20 s | geometry: only x, h, y-hat are on screen; the row sits 1.7 units left of centre for 20 s | the three-node row starts centred and slides into place as the loss box arrives (one play) |
| 2-3 | formula panel 0.75 from the right edge (5.3 % margin) | `buff=0.95` (6.7 %) |
| 4-7 | valley plot not centred in its region left of the side panel | `x_length` 7.2 -> 6.4 and centred on x = -2.26 (region -7.11..2.6); panel at x = 4.2 |

Geometry rules declared for every main figure (owner's new gate; `GeometryGuard` from the skill):
network (centred in x, 7 % margins), formula panel (6 %), number line (symmetric about its middle,
line where the points are computed, both dots and the gap ON the line, square centred on its base),
valley plot (centred in its region, 7 %), valley curve (symmetric about the minimum), side panel
(6 %), recap loop (symmetric about (0, 0.3), centred, 7 %), loss history (centred). The network's
vertical position is the upper band by design (the lower band holds formulas, the number line and
the gradients), so its centring rule is horizontal only.

### Intuitiveness (preview 1)

Newcomer summary: a two-weight network turns 2 into 1 when 3 was wanted; the squared gap (a square
of area 4) is the loss. Sliding one weight traces a valley; the slope says which way is downhill and
gradient descent steps against it, by learning rate times slope, in shrinking steps. Backprop gets
every weight's slope at once by multiplying local rates from the loss backwards (first seen as a
nudge travelling down the chain); one step on both weights cuts the loss from 4 to 0.71, and the
loop repeats. Matches the learning goal.

| Criterion | Score | Note |
|---|---|---|
| Concrete anchor first | 2 | a number flows through a tiny network; "we wanted three" |
| One idea per beat | 2 | |
| Every step motivated | 2 | valley -> slope -> step; "millions of weights" motivates backprop; nudge before chain rule |
| Picture before formula | 2 | square before L formula, valley before the rule, nudge before the chain rule |
| Progressive reveal | 2 | |
| Colour coding consistent | 2 | signals blue, weights teal, target green, loss red, slopes orange |
| Minimal, legible text | 1 | stuck "dL/dw =" leftovers in beat 13 |
| Pacing | 2 | |
| Payoff and recap | 2 | |
| Right depth | 2 | |
| **Total** | 19/20 | geometry not yet measured (no rules in this preview): capped at 15 until a geometry PASS |

## Iteration 2 (preview, first with GeometryGuard)

- Video 162.13 s. Timings: render 51.7 s (all 38 clips from the voiceover cache), checks 13.9 s,
  stills 115.7 s; 183 s wall. Exit 1: report FAIL because of geometry (all other checks PASS, no LAYOUT warning).
- GeometryGuard: 18 rules, all checked, 2 violated:
  - `within_margin(panel, 6%)` at anims 40-42 (59.0-63.5 s): right margin 5.1 %. The arithmetic line
    `0.5 - 0.05 * (-8) = 0.9` was the widest item. Fix: that line at size 40 (like the other small
    equations), panel centre x 4.2 -> 4.1. Measured after: panel box x 2.39..5.81 (9.2 % margin).
  - `centered_in(loss_hist, frame, axis=x)`: "2.49 left". Not a layout bug: the history line is
    centred on screen; the checker measured only the word "loss" because the equation was faded in
    as two slices (`hist_nums[:3]`, `hist_nums[3:]`) and the checker does not descend into a member
    group whose own children are on screen when another direct member is. Workaround: `self.add(hist)`
    after the last fade, then track it. (Reported as skill feedback.)
- Stills looked at: sheets 2, 3, 6, 11, 12, 14 (changed beats) and all 4 `--frames --cues` sheets.
  Verified fixed: centred three-node row and the slide (beats 1-3); tangent stops at the axis (no
  CROSSED warning); highlight boxes clear of the labels below; no leftover "dL/dw =" in beat 13.
- Sync (`--frames --cues`, 49 cues for 38 blocks): every cue's still shows the visual its words
  name (forward flashes on "Feed in two", valley on "It traces a valley", each x-rate arc on its
  phrase, the boxes on their loop phrases). No lead or lag to fix.
- Full resolution (`--still K`, 1920x1080): anim 23 (end of the loss beat: dots, gap and square base
  exactly on the axis; panel 6.8 % from the right edge), 41 (side panel), 85 (backprop with the
  boxes: about 11 px from the node circles, clear of the labels below), 86, 104 (beat 13: both
  squares on the axis, the moved dot on the line). I first asked for anims 25 and 26 thinking they
  were the end of beat 3; they are the hold and the fade, which `index.txt` shows correctly.

## Iteration 3 (preview)

- Video 162.13 s, render 159.4 s, checks 23.5 s, stills 109.3 s; 295 s wall. Exit 0.
- report.md: **PASS**; geometry PASS, "all 18 rule(s) and the frame-edge rule hold over 117
  animations", no UNCHECKED rule, no LAYOUT warning. Audio mean -29.8 dB, peak -7.2 dB.
- Measured (geometry.json): network centre x 0.00 (also in beats 1-2), dots at y -2.85 = the
  number-line tick centreline, square base at -2.85, valley curve symmetric about w2 = 1.5, valley
  plot centre x -2.255 (region centre), loop centred at (0, 0.3), loss history centre x 0.00.
- Stills: sheets 5, 6, 15 (changed beats) and a 16-frame `--frames --count 16` overview.

| Criterion | Score | Note |
|---|---|---|
| Concrete anchor first | 2 | |
| One idea per beat | 2 | |
| Every step motivated | 2 | |
| Picture before formula | 2 | |
| Progressive reveal | 2 | |
| Colour coding consistent | 2 | |
| Minimal, legible text | 2 | leftovers fixed; text checked at 1080p |
| Pacing | 2 | narration sets the pace; holds 25 % |
| Payoff and recap | 2 | |
| Right depth | 2 | |
| **Total** | **20/20** | geometry PASS, so no cap |

## Final 1 (1080p60) - superseded

- `out/Explainer-final.mp4`, 161.20 s, 1920x1080 @ 60 fps. report.md PASS (stream, audio mean
  -29.8 dB / peak -7.1 dB, blank, holds, cuts, geometry 18 rules + frame edge). Timings: render
  1082.4 s, checks 177.5 s, stills 4.2 s (total 1264.2 s).
- The wrapper crashed after the container finished: `render-in-container.sh: line 252: syntax
  error near unexpected token ')'`, exit 2, no VIDEO/SHEET/REPORT lines. Cause: the script was
  edited in place (23:18:05) while this run was executing it; bash reads scripts incrementally.
  The file on disk parses (`bash -n`). Outputs were complete; no container was left behind.
- Stills: the 8-frame contact sheet and 3 full-size frames (30.2 s, 90.7 s, 131.0 s): clean.
- **Defect:** AAC LC 48 kHz stereo audio lasts 157.23 s, video 161.20 s (`ffprobe`, read-only on
  the host; report.md does not show codec or audio length). Manim's audio ends with the last
  sentence; the 4 s silent outro has no audio. The owner's bar asks for matching durations.
  Fix: `cover_outro_with_silence(END_HOLD + END_FADE + END_TAIL)` lays a 4.0 s silent WAV (written
  to the container's /tmp) under the outro with `self.add_sound`.

## Iteration 4 (preview, audio check)

- Video 162.13 s, audio (AAC) 162.18 s: match. report.md PASS, geometry PASS (18 rules + frame
  edge, none unchecked), no LAYOUT warnings. Render 95.7 s, checks 13.3 s, stills 65.0 s (179 s wall,
  after an automatic image rebuild because the skill's sources had changed again).
- Visual timeline unchanged (117 animations, same length as iteration 3); audio-only change.

## Final (final 2 of max 3)

- File: `/home/quellen/dev/manim-video-skill/out/container-runs/05-gradient-descent-narrated/out/Explainer-final.mp4`
- 161.20 s (earlier final 158.2 s; +1.0 s from the beat-3 slide, the rest from the new value
  swaps), 1920x1080 @ 60 fps h264 High; audio AAC LC 48 kHz stereo, 161.24 s (matches).
- report.md: **PASS** (stream, audio mean -29.9 dB / peak -7.1 dB, blank, holds 22 %, cuts,
  geometry: all 18 rules + frame edge over 117 animations, none unchecked; no LAYOUT warnings).
- summary.json timings: render 349.4 s, checks 81.4 s, stills 3.5 s (total 434.3 s).
- Looked at: the 8-still contact sheet, full-size frames at 50.4, 110.9, 151.2 s, and
  `--frames --at 144.5,157.5` (beat 13 and the finished recap). All clean.
- Iterations: 4 previews of this scene (cap 6) plus 1 preview of my own first scene before the
  change of plan; 7 full-resolution `--still` checks; 2 finals (the first had a 4 s short audio track).
- Rubric: 20/20, geometry PASS (no cap).
- Assumptions: narration on (Kokoro af_heart via manim-voiceover, sentences in job.json); content,
  numbers and length kept from examples/05 on the owner's request; newcomer audience, intuitive depth.
- Known limitations: the network lives in the upper band, so in beats 1-2 and 8 the lower half is
  empty for about 15 s (its centring rule is horizontal only, by design); the network is linear (no
  activation), said in the storyboard, not in the video; `self.add(hist)` works around a
  GeometryGuard measuring limitation.
