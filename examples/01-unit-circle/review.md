# Review log: Six trig functions on one unit circle

Scene: `scene.py`, class `Explainer`. Narration: silent (skill default; unattended run, nobody
could be asked). Newcomer, high-school maths, intuitive depth, 16:9 1080p60.

History: preview 1 of this job rendered my own 91 s scene. The coordinator then asked me to start
from `examples/01-unit-circle` (scene.py and storyboard.md copied in, length kept at ~139 s). The
iterations below are for that scene. Before the first render I replaced the known `Indicate` on the
moving triangle's sides (beats 12-13; it stretches lines past their ends, see SKILL.md) with a
white `ShowPassingFlash` along each side, same run time.

## Iteration 1 (preview 2 of the job)

- Video: `out/Explainer-preview.mp4`, 139.59 s, 854x480 @ 15 fps; wrapper 244 s (render 183,
  checks 11, stills 50).
- `out/report.md`: **PASS** (stream, blank 1.3 s, holds 37 % over 49 holds, cuts).
- `LAYOUT` warnings: 1. `t=75.4s after animation 63: CROSSED Line ... runs through MathTex('\sin\theta')`
  (the guard counts from 1; in `index.txt` this is `anim 62`, 0-based).
- Stills looked at: all 15 contact sheets (234 tiles). Full 1080p `--still` at anim 62 (flip end),
  65 (stretched triangle), 93 (80 deg limit caption), 103 and 105 (recap). `--frames --at`
  101.43, 101.6, 109.3, 109.45 (caption swaps).

### Visual bugs (references/visual-qa-checklist.md)

| Beat / time | Bug | Fix |
|---|---|---|
| 12 / 75.4-77 s | after the flip, the copy's thick blue side runs straight through the "sin θ" label for ~1.5 s ("sin\|θ", 1080p still anim 62); LayoutGuard CROSSED | fade "sin θ" out with the flip, back in during the 0.8 s hold after the stretch (same timing) |
| every caption change (~16) / e.g. 109.3 s | caption swap is one `play` with a lagged `AnimationGroup(FadeOut, FadeIn)`: mid-swap the old and new captions overlap as a smear ("Toward 90°" over "θ → 90°: tan θ, sec θ → ∞", frame at 109.30 s) | two plays: old out (0.4 s), then new in (0.5 s); same 0.9 s total |
| 13 / ~83 s | the half-turn of the copy sweeps over the "csc θ" label for a few frames | accepted: transient, mid-motion, label readable before and after |

Checked and fine: label placement at 1080p (all labels 34 pt MathTex, readable, none on a line in
the static pose), sec dimension line and its label, right-angle marks, readouts at 80 deg and 20 deg,
recap boxes and flashes stay on their segments, final fade leaves nothing.

### Intuitiveness (references/intuition-rubric.md)

Newcomer summary: a point on a circle of radius 1 at angle θ sits at (cos θ, sin θ): cos is how far
across, sin how far up, and sin² + cos² = 1 by Pythagoras. The line touching the circle at the
point is cut by the axes into tan θ and cot θ; the distances from the centre to those crossings are
sec θ and csc θ. Stretching the small triangle until cos θ (or sin θ) is 1 lands it on the bigger
ones, which is why tan = sin/cos, sec = 1/cos, cot = cos/sin, csc = 1/sin; near 90° tan and sec run
off to infinity, near 0° cot and csc do. Matches the learning goal.

| Criterion | Score 0-2 | Note |
|---|---|---|
| Concrete anchor first | 2 | a circle drawn, a radius 1 turning, a point |
| One idea per beat | 2 | one segment per beat; one relation pair per similarity beat |
| Every step motivated (no leaps) | 2 | "How far across? / up?", "Four more, on one line", "Same shape, just bigger", "Stretch until cos θ is 1" |
| Picture before formula | 2 | every formula is written after its segments are drawn and matched |
| Progressive reveal | 2 | |
| Colour coding consistent | 2 | legend (tan = yellow, declared) in shapes, labels, formulas, readouts, captions |
| Minimal, legible on-screen text | 2 | captions 3-6 words; 1080p stills readable |
| Pacing (holds after reveals, not dragging) | 2 | 1-1.5 s holds after reveals; sweeps 2.5-5 s |
| Payoff and recap | 2 | limits stated at the extremes; recap pairs each segment with its formula |
| Matches the learning goal and requested depth | 2 | intuitive, newcomer |
| **Total** | 20/20 | the open items are visual bugs, not rubric items |

## Iteration 2 (preview 3 of the job)

- Changes: caption swap in two plays (old out 0.4 s, then new in 0.5 s); "sin θ" fades out with
  the beat-12 flip and back in during the hold after the stretch. No timing change.
- Video: `out/Explainer-preview.mp4`, 139.59 s (unchanged); wrapper 287 s (render 159, checks 15,
  stills 112; machine shared with other runs).
- `out/report.md`: **PASS** (stream, blank 1.3 s, holds 37 % over 49 holds, cuts). `LAYOUT`
  warnings: none (report.md has no "Scene warnings" section, summary.json `scene_warnings: []`).
- Stills looked at: sheets 09, 10, 13 (beat 12 and the 90 deg caption swaps); `--frames --count 16`
  overview of the whole video; 1080p `--still 78` (stretched triangle with "sin θ" back).
- Re-checked iteration-1 findings: no text is crossed after the flip (sheet 09 tiles 8-14); "sin θ"
  returns after the stretch and reads cleanly inside the filled triangle (sheet 10, 1080p still);
  mid-swap frames now show one caption or none, never two (sheets 09, 13). Both marked fixed.

### Visual bugs

None open. Accepted: the beat-13 half-turn sweeps over "csc θ" for a few frames mid-motion.

### Intuitiveness

Newcomer summary unchanged. Rubric unchanged: 20/20 (all criteria 2).

Stop conditions met (no open bugs, no FAIL or WARN, rubric 20/20 >= 18). Rendering the final.

## Final attempt 1 (aborted) and the owner's geometry review

- Final 1 (1080p60) was started after iteration 2. The coordinator then relayed the owner's
  review: the circle is not centred on its axes and the figure hugs the left edge. I interrupted
  the wrapper (Ctrl-C/SIGTERM path; it removed its container). Manim had already finished
  (`out/Explainer-final.mp4`, 138.9 s) but checks and stills never ran. That file is the old
  layout and is superseded.
- Owner's findings, confirmed in the code: x-axis from O - (R + 0.1) to O + R·XR, y-axis from
  O - (R + 0.1) to O + R·YU, with XR/YU 1.25 -> 2.05/1.35 (HOME) and 6.0/3.4 (WIDE): the axes
  reached ~1.1 R on one side and up to 6 R on the other; HOME O at x = -3.8 put the circle's left
  edge ~5% from the frame edge.

## Iteration 3 (preview 4 of the job): symmetric axes, centred layouts, GeometryGuard

- Changes: axes symmetric about O in every state (grow both ways); HOME O = (-2.45, 0), R = 2.0,
  centred in the left region; WIDE O = (0, -0.35), R = 0.95, centred under the caption band, readouts
  in the first quadrant; labels 32 pt, captions 30 pt; sin label lowered/closer (clear of the arc);
  `GeometryGuard` with 9 rules (see storyboard).
- Video: 139.59 s (unchanged). report.md: **PASS** incl. `PASS geometry: all 9 rule(s) and the
  frame-edge rule hold over 137 animations`; every rule checked (17 to 134 times; geometry.json),
  worst margins 7.4% (HOME) and 7.8% (WIDE). LAYOUT warnings: none.
- Stills looked at: all 16 sheets (every beat re-checked after the layout change); 1080p `--still`
  24 (coordinates), 95 (beat 13 stretched), 109 (80° limit with readouts), 124 (recap).
- Item C (owner: ghosted labels at ~25 s): real but transient. `--frames --at` 24.6-26.6 s
  (10 frames) shows, during anim 24 (24.67-26.17 s), each label drawn twice and slightly offset at
  the start of `TransformFromCopy`, then morphing point by point into smeared glyphs, with the empty
  "( , )" brackets already faded in; the end frame (1080p still 24) is clean (one cos θ, one sin θ,
  the coordinates). Same class as the text-transform glitch SKILL.md bans.

### Visual bugs

| Beat / time | Bug | Fix |
|---|---|---|
| 4 / 24.7-25.9 s | coordinates assembled with `TransformFromCopy`: doubled, smeared labels and an empty "( , )" mid-way | rigid copies of the labels move into place (1.1 s), then the brackets fade in (0.4 s); same 1.5 s |

Checked and fine at 1080p: recap (every label clear, sin θ ~18 px inside the arc), beat 13
stretched triangle, 80° readouts ~35 px above the tangent line, WIDE figure centred.

### Intuitiveness

Unchanged content; rubric 20/20 (geometry PASS, so no cap).

## Iteration 4 (preview 5 of the job)

- Change: coordinates assembled by rigid copies of the labels (1.1 s), then the brackets (0.4 s).
- report.md PASS, geometry PASS (9 rules, 138 animations), no LAYOUT warnings; 139.59 s.
- `--frames --at` 24.6-26.6 s (10 frames): no smear and no empty brackets any more; but with the
  default `smooth` easing the copies leave their originals slowly, so for ~0.25 s each label still
  looks doubled (frame at 24.8 s). Fix: `rate_func=rush_from` for that move (motion change -> preview).

## Iteration 5 (preview 6 of the job, the last allowed)

- Change: `rush_from` on the label move.
- report.md PASS, geometry PASS (9 rules over 138 animations), LAYOUT none; 139.59 s.
- `--frames --at` 24.67-26.17 s: from the first frame of the move the copies are already clear of
  their originals; they travel as clean labels and the brackets close after they land. Fixed.
  `--frames --count 16` overview of the whole video: consistent, nothing new.
- Rubric 20/20; geometry PASS, so no cap. Stop conditions met. Final 2 next.

## Final (final render 2 of 3)

- File: `/home/quellen/dev/manim-video-skill/out/container-runs/01-unit-circle/out/Explainer-final.mp4`
- 138.90 s (earlier final: 138.9 s), 1920x1080, 60 fps, h264, no audio (silent), 6.1 MB.
- report.md: **PASS** (stream, blank 1.5 s, holds 39 %, cuts) and **PASS geometry**: all 9 rules and
  the frame-edge rule over 138 animations, 0 violated, none UNCHECKED. LAYOUT warnings: none.
- Timings (summary.json): render 978.4 s + checks 104.3 s + stills 4.6 s = 1087.3 s.
- The wrapper itself died after the container finished (`line 252: syntax error near unexpected
  token ')'`): the skill's `render-in-container.sh` was rewritten on disk at 23:22 while it ran
  (bash reads scripts lazily). Outputs were complete; no container was left behind.
- Looked at: the 8-still contact sheet; full-size frames at 78.1 s (stretch), 112.9 s (WIDE sweep,
  76°) and 130.2 s (recap). Nothing new, except the known item below.
- Iterations: 6 previews (cap 6; preview 1 was my own scene before the coordinator switched to the
  example scene), 2 finals (final 1 aborted on the old layout), plus 1080p `--still` and
  `--frames --at` checks.
- Bugs found and fixed: Indicate stretching triangle sides (pre-emptive); sin θ crossed by the
  flipped triangle (LayoutGuard CROSSED); caption crossfades smearing two captions; axes not
  symmetric about the circle and figure 5% from the left edge (owner); coordinates assembled with
  TransformFromCopy (doubled, smeared labels and an empty "( , )" at ~25 s, owner's item C); slow
  start of the label move still reading as doubled.
- Rubric: 20/20 (geometry PASS, so no cap).
- Assumptions: silent, newcomer, intuitive, 16:9 1080p60 (skill defaults; unattended run). Length
  kept at the earlier final's ~139 s as the coordinator asked.
- Known limitations: recap boxes are drawn with Create, so for ~0.5 s each box reads as an overline
  above its formula before it closes; the beat-13 half-turn sweeps over "csc θ" for a few frames;
  in beats 1-4 the right panel holds only a caption (the figure is centred in its own left region,
  as the owner asked, not in the frame); first quadrant only; six concept colours at once (labelled).
