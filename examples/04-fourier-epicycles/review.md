# Review log: Drawing with spinning arrows (Fourier epicycles)

Scene: `scene.py`, class `Explainer`. Narration: silent (the user's answer).

## Iteration 1 (preview)

- Video: `media/videos/scene/480p15/Explainer.mp4` (123.9 s, 854x480 @ 15 fps), rendered in 151 s.
- `qa_check.py --expect-silent`: PASS stream, PASS blank (0.7 s total), PASS holds (34 % still
  across 32 holds), PASS cuts. Overall PASS.
- `LAYOUT` warnings: 2 x OVERLAP at t=119.3 s (formula vs "an arrow", formula vs "spins");
  `END 5 object(s) still on screen: Group x5`.
- Stills looked at: `sheet_01` to `sheet_10` (156 tiles, `--beats --mid`), full size
  `frame_152` (formula), `frame_125` (50-arrow pass), `frame_139`/`frame_141` (recap, caption
  crossfade), `frame_066` (beat 5 curve).

### Visual bugs (references/visual-qa-checklist.md)

| Beat / time | Bug | Fix |
|---|---|---|
| 12 / 119 s | "an arrow" label sits on the sum's subscript `k` (LAYOUT OVERLAP confirmed in `frame_152`); braces under `c_k` and `e^{ikt}` are tiny and crowded | Two formula lines (`pen = arrow1 + arrow2 + ...`, then `= sum c_k e^{ikt}` aligned on `=`) and a one-row legend below, clear of the subscript |
| 12 / 119 s | The `k` inside "spins k turns per loop" renders much smaller than the words around it | Legend uses `MathTex` at formula size for `c_k` and `k` |
| 12 / 117 s | `TransformMatchingTex` from the arrow sum to the sigma form: mid-frame is a cluttered crossfade of two equations on the same spot | Keep line 1 and write line 2 under it (no morph) |
| 11 / 108 s | Thumbnails cross each other while moving from the 2x2 panel to the recap row (3-arrow thumbnail passes over the 10-arrow one and its label) | Move them one after another (`LaggedStart`, lag 0.3) |
| all captions | Caption change is a simultaneous crossfade: both captions overlap at half opacity (`frame_141`) | Old caption fades out first, new one follows (lag 0.6) |
| 5 / 46 s | The three new orange arrows (0.35, 0.2, 0.12 long) are barely visible at 480p | Lengths 0.4, 0.25, 0.15 (extent check: y stays in -3.14..2.34) |
| end | `LAYOUT END ... Group x5`: not visible objects, but the `LaggedStart` groups of ValueTrackers (one per arrow-growing play), which LayoutGuard counts as visible | Grow arrows with per-tracker lagged rate functions (no wrapper Group); see notes.md, skill feedback |

### Intuitiveness (references/intuition-rubric.md)

Newcomer summary: a spinning arrow's tip draws a circle; an arrow has a length and a speed; adding
a second arrow tip to tail makes the tip draw a new shape, and more arrows make fancier curves.
A chain of arrows then draws a lightning bolt, roughly with 3 arrows and sharply with 50, and the
sum is called a Fourier series. Matches the goal, except the viewer is never told where the bolt's
arrows come from (they just appear).

| Criterion | Score 0-2 | Note |
|---|---|---|
| Concrete anchor first | 2 | A single spinning arrow, like a clock hand |
| One idea per beat | 2 | |
| Every step motivated (no leaps) | 1 | "Which arrows draw this?" is answered by arrows that simply appear; no hint that Fourier's recipe chooses them, biggest first |
| Picture before formula | 2 | The formula only labels what was seen |
| Progressive reveal | 2 | |
| Colour coding consistent | 2 | Blue chain, orange new arrows, yellow pen, grey target, also in the formula |
| Minimal, legible on-screen text | 1 | Formula labels collide and the inline `k` is tiny |
| Pacing (holds after reveals, not dragging) | 2 | 124 s; loops 4 to 10 s; 1 to 2.5 s holds |
| Payoff and recap | 2 | Row of 1/3/10/50-arrow drawings, then the name and formula |
| Matches the learning goal and requested depth | 2 | |
| **Total** | 18/20 | Fix the two 1s |

Leap fix: after the bolt appears, a caption naming Fourier's recipe (first drafted as "Fourier's
recipe: measure the shape, get the arrows", shortened to "Fourier's recipe gives the arrows"
because the long one is about 13.8 units wide at font 40, wider than the 12.8-unit safe area);
pass captions say "Biggest arrow alone", "3 biggest arrows", "small fast ones add detail".

## Iteration 2 (preview)

Changes: formula as two lines plus a legend row (no braces, no `TransformMatchingTex`); captions
change one after the other; recap thumbnails move one after another; beat-5 arrows 0.4/0.25/0.15;
arrows grow with per-tracker lagged rate functions (no `LaggedStart` wrapper); new caption
"Fourier's recipe gives the arrows" after the bolt appears; pass captions "Biggest arrow alone: a
circle", "3 biggest arrows: a rough blob", "10 arrows: small fast ones add detail".

- Video: `media/videos/scene/480p15/Explainer.mp4` (129.7 s), rendered in 285 s (machine shared
  with parallel renders, load about 8).
- `qa_check.py --expect-silent`: PASS stream, PASS blank (0.6 s), PASS holds (35 % across 33
  holds), PASS cuts. Overall PASS.
- `LAYOUT` warnings: none (no OVERLAP, no CLIPPED, and no END line: nothing is left on screen).
- Stills looked at: `sheet_01` to `sheet_10` (160 tiles), full size `frame_141` (recap mid-move),
  `frame_129` (50-arrow pass), and a 1080p still of the formula frame
  (`render.sh still ... -- -n 0,77`).

### Visual bugs

| Beat / time | Bug | Status |
|---|---|---|
| 12 / 119 s | Formula label collision | Fixed: two lines and a legend, clean at 1080p (`stills/02`) |
| 12 / 119 s | Tiny inline `k` | Fixed: `k` in the legend at formula size |
| 12 / 117 s | Cluttered equation morph | Fixed: line 2 is written under line 1 |
| 11 / 113 s | Thumbnails crossing | Fixed: staggered moves, no crossing in the mid-frame (`stills/04`) |
| all | Caption crossfade overlap | Fixed: only one caption visible at a time in every mid-frame |
| 5 / 46 s | New arrows too small | Fixed: visible as three small orange arrows at 480p |
| end | False `LAYOUT END Group x5` | Gone (no wrapper groups) |
| 12 / 125 s | New, minor: legend items sat on different baselines ("an arrow" about 8 px higher than "turns per loop" at 1080p) | Fixed after this preview by aligning both to the bottom of `c`; checked with a second 1080p still of that frame (the only changed frame), then went to the final |

### Intuitiveness

Newcomer summary: one spinning arrow draws a circle; each arrow has a length and a whole number of
turns per loop; adding a second one tip to tail (a circle riding on a circle) bends the circle
into a new shape, and chaining more gives fancier closed curves. To draw a chosen shape, Fourier's
recipe gives the arrows, biggest first: the biggest alone draws a circle, 3 draw a blob, 10 a rough
bolt (small fast arrows add the detail) and 50 a sharp bolt. Adding up spinning arrows like this is
a Fourier series, `c_k` is an arrow and `k` its turns per loop. This matches the learning goal.

| Criterion | Score 0-2 | Note |
|---|---|---|
| Concrete anchor first | 2 | One spinning arrow, like a clock hand |
| One idea per beat | 2 | |
| Every step motivated (no leaps) | 2 | Each beat answers the previous one; the recipe is named and its output ordered biggest first (how it is computed is deliberately left out) |
| Picture before formula | 2 | Formula only at the end, as a label for the chain |
| Progressive reveal | 2 | One arrow, two, five; then 1, 3, 10, 50 for the bolt |
| Colour coding consistent | 2 | Blue chain / orange new arrows / yellow pen / grey target, same in the formula |
| Minimal, legible on-screen text | 2 | Captions of 3 to 7 words; formula and legend checked at 1080p |
| Pacing (holds after reveals, not dragging) | 2 | 130 s; loops 4 to 10 s; holds 1 to 3 s; no stall over about 4.5 s |
| Payoff and recap | 2 | Row of four drawings, then the name and the formula with the row above it |
| Matches the learning goal and requested depth | 2 | Intuitive, newcomer level |
| **Total** | 20/20 | Pass |

Accepted as is: pass captions name the result ("a circle", "a rough blob") while it is being drawn
rather than after; this guides the eye and avoids doubling the caption changes.

## Final

- File: `/home/quellen/dev/manim-video-skill/out/04-fourier-epicycles.mp4` (render:
  `media/videos/scene/1080p60/Explainer.mp4`, `render.sh final`, 1320 s on the shared machine).
- Duration / resolution / audio: 129.5 s, 1920x1080 @ 60 fps, h264, no audio stream (silent).
- Iterations: 2 previews + 2 full-resolution stills of the one frame changed after preview 2 + 1 final.
- Bugs found and fixed: formula labels on the sum's subscript and a tiny inline `k`; cluttered
  `TransformMatchingTex` morph; recap thumbnails crossing; overlapping caption crossfades;
  beat-5 arrows too small; the leap "where do the bolt's arrows come from"; legend baselines;
  plus a false `LAYOUT END` report (LaggedStart groups of ValueTrackers), worked around.
- Checked: `qa_check.py --expect-res 1920x1080 --expect-silent` on the final: PASS stream
  (h264 1920x1080 @ 60 fps, 129.50 s, 0 audio streams), PASS blank (0.8 s incl. start/end),
  PASS holds (35 % still across 33 holds), PASS cuts; overall PASS. No `LAYOUT` lines in the
  final render log. `frames.py --count 8` contact sheet looked at (`stills/06`), plus full-size
  1080p frames at 24.3 s (length and speed) and 105.2 s (50-arrow pass): thin circles visible,
  text crisp, arrow angles consistent with speeds +1 and -2. Rubric 20/20.
- Assumptions: silent (the user's answer); newcomer with high-school maths, intuitive depth,
  16:9 1080p60 (skill defaults). Target shape chosen by me: a lightning bolt.
- Storyboard in one paragraph: one spinning arrow draws a circle; each arrow has a length and a
  whole number of turns per loop (1 turn vs 2 turns backwards); added tip to tail, a circle riding
  on a circle draws a rounded triangle, and more arrows draw fancier closed curves. Asked "which
  arrows draw this bolt?", Fourier's recipe gives them biggest first: 1 arrow draws a circle,
  3 a blob, 10 a rough bolt, 50 a sharp bolt, kept side by side as thumbnails; the recap lines them
  up ("more arrows, sharper drawing") and names the sum: pen = arrow1 + arrow2 + ... = sum c_k e^{ikt},
  with `c_k` an arrow and `k` its turns per loop.
- Left out on purpose: how the arrow lengths and start angles are computed (the averaging
  integral), complex-number algebra, convergence and overshoot at corners.
- Known limitations: pass captions name the result while it is being drawn; with 50 arrows the
  smallest ones are sub-pixel, so the chain near the pen reads as a small tangle (as in any
  epicycle drawing); `t` in `e^{ikt}` is not separately labelled.
