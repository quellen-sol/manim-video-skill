# Review log: Drawing with spinning arrows (Fourier epicycles)

Scene: `scene.py`, class `Explainer`. Narration: silent (the user chose silent).

Change of plan (owner, mid-run): the scene and storyboard are taken from the earlier run in
`examples/04-fourier-epicycles/` (final 129.5 s, rendered on the host route), kept at the same
content and length, and re-checked here on the container route as a fresh reviewer. My own
shorter draft (78-82 s, 2 previews) is kept in `superseded-own-draft/` for reference only.
Changes to the adopted scene before preview 1: the docstring's render line only.

## Iteration 1 (preview)

- Video: `out/Explainer-preview.mp4` (129.66 s, 854x480 @ 15 fps); render 233.3 s, checks 9.8 s,
  stills 32.0 s (total 275 s, host shared with other test renders).
- Checks: PASS (stream, blank 0.7 s, holds 25 % across 32 holds, cuts). LayoutGuard active, no
  `LAYOUT` lines at all (no OVERLAP, no END leftovers).
- Stills looked at: all 10 contact sheets (160 tiles), full size `frame_041` (caption swap),
  `frame_091`, `frame_105`, `frame_133` (thumbnail moves), `frame_147`/`frame_148`, and
  `--frames --at 118.70,118.76,118.83,118.90` (a suspected flicker; not real, see below).

### Visual bugs (references/visual-qa-checklist.md)

| Beat / time | Bug | Fix |
|---|---|---|
| every caption change (12 swaps: 10.5, 15.6, 26.4, 38, 43, 50, 54, 68, 72, 87, 98, 117 s) | The old and new captions overlap mid-swap: `AnimationGroup(FadeOut, FadeIn, lag_ratio=0.6)` starts the new caption while the old one is still at about 40 % opacity, so the mid-frames show garbled double text ("Each aAdd themtip to tail speed", `frame_041`). The earlier run reported this fixed; it is not. | `caption()` now plays FadeOut (0.45 s) and then FadeIn (0.45 s): same total time, never both on screen |
| 8 / 79.6 s | The 3-arrow result, still large mid-flight, flies across the "1 arrow" thumbnail and its label (`frame_105`) | The result fades out on stage and its thumbnail fades in at its slot with a short 0.4 shift (same 1.2 s) |
| 10 / 108.8 s | The 50-arrow result flies across the "1 arrow" and "10 arrows" thumbnails and labels (`frame_133`) | Same fix |
| 12 / 118.8 s | Suspected: caption missing in the sheet tile for anim 73 | Not a bug: `frame_148` and four extracted frames around it all show the caption (I misread the downscaled sheet) |

### Intuitiveness (references/intuition-rubric.md)

Newcomer summary: one spinning arrow's tip draws a circle; each arrow has a length and a speed
(1 turn, or 2 turns backwards); added tip to tail, a circle riding on a circle draws a new shape,
and more arrows draw fancier curves. To draw a chosen lightning bolt, "Fourier's recipe" gives the
arrows biggest first: 1 arrow draws a circle, 3 a blob, 10 a rough bolt, 50 a sharp bolt. Adding up
spinning arrows like this is a Fourier series; c_k is an arrow and k its turns per loop. Matches
the learning goal.

| Criterion | Score 0-2 | Note |
|---|---|---|
| Concrete anchor first | 2 | one arrow spinning like a clock hand |
| One idea per beat | 2 | |
| Every step motivated (no leaps) | 2 | "Which arrows draw this?" is answered by the recipe, biggest first; how it computes them is left out on purpose |
| Picture before formula | 2 | the formula only labels the chain at the end |
| Progressive reveal | 2 | 1, 2, 5 arrows; then 1, 3, 10, 50 for the bolt |
| Colour coding consistent | 2 | blue chain, orange new arrows, yellow pen, grey target, also in the formula |
| Minimal, legible on-screen text | 1 | captions are short, but every caption change shows two captions garbled on top of each other |
| Pacing (holds after reveals, not dragging) | 2 | 130 s; loops 4 to 10 s; holds 1 to 3 s |
| Payoff and recap | 2 | row of four drawings, then the name and formula |
| Matches the learning goal and requested depth | 2 | |
| **Total** | 19/20 | caption fix needed; thumbnail crossings are visual bugs |

## Iteration 2 (preview)

Changes: `caption()` swaps in two plays (old out 0.45 s, then new in 0.45 s); pass results no
longer fly into the panel: the stage curve fades out while the thumbnail fades in at its slot
with a 0.4 shift (same 1.2 s). Length unchanged.

- Video: `out/Explainer-preview.mp4` (129.67 s); render 41.5 s (Manim's cache kept the
  unchanged animations), checks 13.8 s, stills 77.3 s (12 sheets, 186 tiles).
- Checks: PASS (stream, blank 0.7 s, holds 25 % across 32 holds, cuts). LayoutGuard active, no
  `LAYOUT` lines.
- Stills looked at: sheets 03, 07, 08, 09, 10, 11, 12 (every caption swap and every thumbnail
  step), the sheet-11 tile for anim 86 cropped at full tile size (it looked caption-less in the
  downscaled sheet; it is not), full size 1080p `--still 91` (formula and legend) and
  `--still 76` (end of the 50-arrow pass with three thumbnails).

### Visual bugs

| Beat / time | Bug | Status |
|---|---|---|
| all caption swaps | two captions overlapping mid-swap | Fixed: only one caption (or none, for 0.45 s) in every mid-frame |
| 8 / 79.6 s, 10 / 108.8 s | result flying across earlier thumbnails | Fixed: no crossing; the new thumbnail appears in its own slot |
| 12 / 125 s | (1080p check) formula, legend baselines, colours | Clean: no overlap, legend on one baseline, `c_k` blue in both places |
| 10 / 107 s | (1080p check) 50-arrow chain | The smallest arrows form a small tangle near the pen (sub-pixel arrows); accepted, as in any epicycle drawing |

### Intuitiveness

Same newcomer summary as iteration 1; it matches the learning goal.

| Criterion | Score 0-2 | Note |
|---|---|---|
| Concrete anchor first | 2 | |
| One idea per beat | 2 | |
| Every step motivated (no leaps) | 2 | |
| Picture before formula | 2 | |
| Progressive reveal | 2 | |
| Colour coding consistent | 2 | |
| Minimal, legible on-screen text | 2 | captions now swap cleanly; all text at least 28 and checked at 1080p |
| Pacing (holds after reveals, not dragging) | 2 | |
| Payoff and recap | 2 | |
| Matches the learning goal and requested depth | 2 | |
| **Total** | 20/20 | pass (owner's bar 18/20) |

Accepted as is: pass captions name the result while it is drawn ("a rough blob"); thumbnails
appear in place rather than flying (less continuity, but the same shape and a count label).

## Final attempt 1 (aborted)

Started after iteration 2 (22:28); interrupted at animation 58 of 93 (22:39) with the wrapper's own
Ctrl-C path (it removed its container), because the owner made geometry part of the acceptance
gate. No output kept.

## Iteration 3 (preview, geometry gate)

Added `GeometryGuard` (geometry_qa) with 13 rules: `concentric(ring1, pivot)` and
`concentric(ring1b, pivotb)` (each first epicycle circle on its pivot, both chains);
`within_margin(..., 7%)` for the main figure, the panel, the recap row and the formula block;
`centered_in` for the title card (frame), the chain's anchor circle (stage, beats 2/4/5), the
beat-3 pair (stage), the bolt (left zone x -6.4..1.0), the complete thumbnail panel (right zone
x 1.0..6.4), the recap row and the formula block (stage = frame below the caption band,
y -3.4..2.6). Names are re-pointed as beats change layout (`geo_off` points a name at an object
that is never on screen, which pauses its rules).

Fixed before rendering, by computing the rule: in beat 3 the two rigs with their labels below sat
0.33 below the stage centre (rigs at y -0.4, box y -2.95..1.5). The rigs now slide to y -0.075
for that beat (and back to -0.4 for tip to tail); measured pair centre: (-0.04, -0.40).

- Render 182.3 s; checks FAIL (geometry only); 129.67 s.
- `GEOMETRY FAIL centered_in(title_card, frame) at anim 0`: only the title was on screen yet (the
  subtitle arrives 1 s later); the complete card is centred. Rule now tracked from the moment the
  card is complete.
- `GEOMETRY FAIL centered_in(block, ...) at anim 91: 0.46 up`: a measurement gap, not a layout
  bug: the legend `VGroup` was never added itself (its two halves were), so the checker dropped it
  and measured only thumbnails + formula. Tracked the on-screen pieces instead.
- Panel centre was 0.135 below its zone centre (tolerance 0.15): slots moved up 0.1.

## Iteration 4 (preview)

- Render 183.0 s, checks 11.4 s, stills 46.1 s; 129.67 s; overall PASS.
- Geometry: PASS, all 13 rules checked (none UNCHECKED) plus the frame-edge rule, over 94
  animations. Measured centres: title card (0, 0); anchor ring (0, -0.4); pair (-0.04, -0.40);
  bolt (-2.70, -0.45) in a zone centred at (-2.7, -0.4); panel (3.70, -0.44) in (3.7, -0.4);
  recap row (-0.01, -0.46); formula block (0, -0.49). Figure extent x -5.1..5.03, y -3.03..2.23
  (margins at least 0.97 and 0.97 units, 7 % needs 1.0 and 0.56: x margin is 2.0 at worst).
- Stills looked at: sheets 03, 04 (beat 3 lift and the diagonal slides), 11 (panel, recap,
  formula), 1080p `--still 19` (beat 3 pair: orange circle on its pivot, pair centred) and
  `--still 78` (complete panel next to the bolt).
- Rubric unchanged: 20/20.

## Final

- File: `/home/quellen/dev/manim-video-skill/out/container-runs/04-fourier-epicycles/out/Explainer-final.mp4`
  (6.2 MB).
- Duration / resolution / audio: 129.50 s (earlier final: 129.5 s), 1920x1080 @ 60 fps, h264, no
  audio stream (silent).
- `out/report.md`: overall PASS: stream, blank (0.8 s incl. start/end), holds (26 % across 32),
  cuts, geometry (all 13 rules and the frame-edge rule over 94 animations). No LAYOUT lines.
- Timings (`out/summary.json`): render 1407.5 s, checks 193.7 s, stills 8.4 s, total 1609.6 s
  (host load 11 to 15 on 4 cores). Manim's cache reused the animations finished by the aborted
  attempt 1.
- The wrapper itself then failed after the job had finished: `render-in-container.sh: line 252:
  syntax error near unexpected token ')'`, exit 2, no VIDEO/SHEET lines. The script had been
  rewritten on disk at 23:18:05 while it was running (bash reads scripts as it goes). The job's
  outputs are complete; no container of this job was left running.
- Stills looked at: the final sheet (8 even stills) and full size 24.3 s (beat 3 pair), 105.2 s
  (50-arrow pass with three thumbnails: each circle centred on the previous tip, rings thin but
  visible) and 121.4 s (formula line 1 under the thumbnails). No new issue.
- Iterations: 4 previews of the adopted scene (plus 2 of my own superseded draft), 2 final
  attempts (1 aborted at the owner's request, 1 completed).
- Bugs found and fixed: overlapping caption swaps (every caption change); result thumbnails flying
  across earlier thumbnails (passes 2 and 4); beat-3 pair 0.33 low on the stage (geometry); panel
  0.135 below its zone centre (geometry, near the tolerance). Measurement-only fixes: title card
  tracked once complete; formula block tracked as on-screen pieces.
- Rubric: 20/20 (no geometry FAIL).
- Assumptions: silent (the user's answer); newcomer, intuitive, 16:9 1080p60 (defaults); content
  and length kept from the earlier run at the owner's request.
- Known limitations: pass captions name the result while it is drawn; the smallest of the 50
  arrows form a tangle near the pen; thumbnails appear in place rather than flying; the
  tip-to-tail triangle's bounding box is 0.6 right of the chain's centre by nature (a 3-fold shape),
  so only the anchor circle is held to `centered_in` in beats 2, 4 and 5; the drawn curve is held to
  the 7 % margin.
