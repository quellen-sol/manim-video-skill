# Review log: Six trig functions on one unit circle

Scene: `scene.py`, class `Explainer`. Narration: silent (default; the user could not be asked).

## Iteration 1 (preview)

- Render attempt 1 failed (Manim `TypeError: cannot pickle '_thread.lock' object`): label updaters
  were bound methods (`add_updater(self.place_one)`); `FadeIn` deep-copies the label, and deep-copying
  a bound method deep-copies the whole Scene. Fixed by wrapping every updater in a lambda. Not a
  separate iteration (Step 3: fix render errors first).
- Video: `media/videos/scene/480p15/Explainer.mp4` (130.86 s, 854x480, 15 fps), rendered in 188 s.
- `qa_check.py --expect-silent`: PASS stream, blank, cuts, holds (55 % still time over 38 holds);
  WARN holds "nothing moves for 6.3 s at 20.9-27.2 s" and "6.0 s at 41.3-47.3 s".
  Both are false positives: `frames.py --holds` finds four separate holds in 21.4-27.2 s (sin leg
  drawn, label, coordinates assembled) and the 41-47 s stretch is the triangle fill, the identity
  being written and an Indicate. freezedetect at n=0.0005 does not see a thin line growing on a
  dark 480p frame, and qa_check then merges the adjacent holds into one "stall".
- `LAYOUT` warnings: none (no overlaps, clipping or my own safe-area check). Still at animation
  101 reports `LAYOUT END 17 object(s)` as expected (the recap picture).
- Stills looked at: `frames.py --beats --mid` produced wrong beat labels and times (see below), so I
  used `--holds` (51 resting frames, sheets 01-04) plus `--at` (20 frames inside the sweeps, flips,
  zooms and recap, sheets 01-02), and a 1080p still of the recap (`render.sh still -- -n 0,101`).

### Tooling problem found

`frames.py --beats` labelled tile 1 "beat 12" at 0.6 s. Manim keeps at most 100 partial movie
files (`max_files_cached`); this scene plays 111 animations, so 11 partial files were evicted and
`beat_times()` skips missing files without adding their duration, shifting every later timestamp
and losing the last ~14 s. Workaround from iteration 2: render with
`render.sh preview scene.py Explainer -- --max_files_cached 1000`.

### Visual bugs (references/visual-qa-checklist.md)

| Beat / time | Bug | Fix |
|---|---|---|
| 15 / 121-125 s | Circumscribe's travelling stroke hugs the formula rows (buff 0.08); in stills it reads as an overline on "1", "cos θ", "sin θ" (looks like a LaTeX glitch) | replace with a `SurroundingRectangle` drawn around the rows, held, then faded |
| 5 / 31 s, 14 / 99-115 s | θ arc has a fixed 0.5 radius: at 80° it pokes through the sin leg, and after the zoom-out (R 1.4) it is oversized | arc radius 0.16 R (0.4 at home, 0.22 zoomed), θ label at arc + 0.35 |
| 8-15 / from 54 s | the white dot at P is drawn under the tan and cot segments (hidden in the 1080p still) | `set_z_index(5)` on the dot |
| 12-15 / formulas | "sin θ/ cos θ": a thin space after the slash, because `\cos` is an operator | wrap the denominators in braces `{\cos\theta}` |

### Intuitiveness (references/intuition-rubric.md)

Newcomer summary: a point on a radius-1 circle at angle θ sits at (cos θ, sin θ): cos is how far
across, sin how far up, and sin² + cos² = 1 by Pythagoras. The line touching the circle at the
point is cut by the two axes into tan and cot, and the distances from the centre to those
crossings are sec and csc. Flipping and scaling the small triangle shows tan = sin/cos,
sec = 1/cos, cot = cos/sin, csc = 1/sin, and the numbers grow as θ nears 90° or 0°.

| Criterion | Score 0-2 | Note |
|---|---|---|
| Concrete anchor first | 2 | a circle and a point going round it |
| One idea per beat | 2 | beat 4 adds the coordinates, but they are the payoff of beats 3-4 |
| Every step motivated (no leaps) | 1 | beat 7: "The line that just touches" arrives with no reason to draw a line; beat 12: "Same shape, flipped" does not say why we flip |
| Picture before formula | 2 | every symbol labels a segment already drawn |
| Progressive reveal | 2 | one segment per beat |
| Colour coding consistent | 2 | legend followed in shapes, labels, formulas and readouts |
| Minimal, legible on-screen text | 2 | captions of 3-5 words; 1080p still readable |
| Pacing (holds after reveals, not dragging) | 2 | 1.2-1.5 s holds; 131 s total |
| Payoff and recap | 1 | recap is there, but the blow-up message in beat 14 is only implied by the numbers ("Toward 90°") and never stated |
| Matches the learning goal and requested depth | 2 | |
| **Total** | 18/20 | |

Changes for iteration 2: the four visual fixes above; beat 7 caption "The other four live on one
line"; beat 12 caption "Same shape, just bigger"; beat 14 states the limits explicitly
(θ → 90°: tan θ, sec θ → ∞, then θ → 0°: cot θ, csc θ → ∞) at each extreme.

## Iteration 2 (preview)

- Changes: the four iteration-1 visual fixes; captions "Four more, on one line" (beat 7) and
  "Same shape, just bigger" (beat 12); explicit limit captions in beat 14; recap highlights with
  `SurroundingRectangle`; `config.max_files_cached = 1000` in the scene (render.sh/manim 0.22.1
  has no `--max_files_cached` CLI flag: `Error: No such option`, so it goes in the file).
- Video: `media/videos/scene/480p15/Explainer.mp4` (135.79 s), rendered in 147 s; 118 animations,
  all 118 partial movies kept.
- `qa_check.py --expect-silent`: PASS stream, blank, cuts, holds (55 %, 41 holds); the same two
  WARN holds (20.9-27.1 s, 41.3-47.3 s), same explanation as iteration 1 (false positives).
- `LAYOUT` warnings: none.
- Stills looked at: `frames.py --beats --mid`, now correct (234 tiles, beat 1 at 0.6 s to beat 118
  at 135.3 s): all 15 contact sheets, plus full-size `frame_225` (recap).
- Re-checked iteration-1 fixes: arc no longer crosses the sin leg at 80° and shrinks with the
  zoom (sheets 04, 12, 13); dot on top of tan/cot (sheet 14); "sin θ/cos θ" spacing even
  (sheet 09); recap boxes render cleanly (sheets 14-15). All four marked fixed.

### Visual bugs

| Beat / time | Bug | Fix |
|---|---|---|
| 15 / 129.8 s | `Indicate` scales segments by 1.15 about their centre: the sec dimension line pokes left of O and runs into its own "sec θ" label; csc pokes below the x-axis; tan past P and E (full-size `frame_225`) | segments get a white `ShowPassingFlash` along a fresh copy (nothing moves); only labels keep `Indicate` |
| every caption change | old and new caption crossfade in place, so mid-transition frames show two texts on top of each other (sheets 02, 03, 05, 12, 13) | `AnimationGroup(FadeOut(old), FadeIn(new), lag_ratio=0.6)` so the old caption is mostly gone first |
| 14 / 106 s, 113 s | "θ → 90° : tan θ": TeX treats ":" as a relation and spaces it on both sides | `\colon` |
| 14 / 99-117 s | the right-angle mark keeps 0.22 units while the circle shrinks to R = 1.4, crowding the tiny triangle at 20° and 80° | side 0.09 R |

### Intuitiveness

Newcomer summary: as in iteration 1, plus the two limits are now stated in words-and-symbols at
the moment the numbers are largest, and the tangent line arrives with a reason ("Four more, on
one line").

| Criterion | Score 0-2 | Note |
|---|---|---|
| Concrete anchor first | 2 | |
| One idea per beat | 2 | |
| Every step motivated (no leaps) | 1 | beat 12/13: "Scale it by 1/cos θ" gives the factor but not why; the reason (the cos side must become the radius, 1) is only visible to an attentive viewer |
| Picture before formula | 2 | |
| Progressive reveal | 2 | |
| Colour coding consistent | 2 | |
| Minimal, legible on-screen text | 2 | |
| Pacing | 2 | 136 s; holds 1-1.5 s after reveals |
| Payoff and recap | 2 | limits stated; recap pairs each segment with its formula |
| Matches the learning goal and requested depth | 2 | |
| **Total** | 19/20 | |

Change for iteration 3: captions "Stretch until cos θ is 1" / "Stretch until sin θ is 1" so the
scale factor is motivated, plus the four fixes above.

## Iteration 3 (preview)

- Changes: recap segments flash (white `ShowPassingFlash` on a fresh line) instead of `Indicate`;
  lagged caption swaps; `\colon` in the limit captions; right-angle mark 0.09 R; captions
  "Stretch until cos θ is 1" / "Stretch until sin θ is 1".
- Video: `media/videos/scene/480p15/Explainer.mp4` (139.59 s), rendered in 216 s.
- `qa_check.py --expect-silent`: PASS stream, blank, cuts, holds (52 %, 41 holds); WARN holds
  21.7-27.7 s and 42.3-48.3 s: the same two false positives as before (moved by 0.8 s because the
  caption swaps now take 0.9 s).
- `LAYOUT` warnings: none.
- Stills looked at: all 15 `--beats --mid` sheets (234 tiles); 1080p stills after animation 94
  (limit caption at θ = 80°, all readouts) and 65 (stretched triangle with the new caption).
- Re-checked iteration-2 findings, all fixed: recap flashes stay on the segments and the sec
  label is never touched (sheets 14-15); caption swaps show only a faint residue mid-transition
  (sheets 02-13); "θ → 90°: tan θ, sec θ → ∞" spaced as punctuation (sheet 12, 1080p still);
  right-angle mark small at R = 1.4 (sheets 12-13).

### Visual bugs

| Beat / time | Bug | Fix |
|---|---|---|
| 12-13 / ~79 s, ~95 s | `Indicate` on the moving triangle's sides stretches them ~0.3 units past their ends for 1.3 s (white side briefly crosses the y-axis) | accepted: a deliberate pulse on a temporary demonstration object; it touches no label or other text |

No other findings.

### Intuitiveness

Newcomer summary: a point on a circle of radius 1 at angle θ sits at (cos θ, sin θ), so
sin² + cos² = 1. The line that touches the circle there is cut by the axes into tan θ (down to
the x-axis) and cot θ (up to the y-axis); from the centre to those crossings are sec θ and
csc θ. Stretching the small triangle until cos θ (or sin θ) becomes 1 turns it into the big
ones, which is why tan = sin/cos, sec = 1/cos, cot = cos/sin, csc = 1/sin. Near 90° tan and
sec grow without bound; near 0° cot and csc do. This matches the learning goal.

| Criterion | Score 0-2 | Note |
|---|---|---|
| Concrete anchor first | 2 | a circle and a point going round it |
| One idea per beat | 2 | beats 12-13 each give one similarity with its two consequences |
| Every step motivated (no leaps) | 2 | "Four more, on one line"; "Same shape, just bigger"; "Stretch until cos θ is 1" |
| Picture before formula | 2 | every formula is written after its segments are shown and matched |
| Progressive reveal | 2 | one segment per beat |
| Colour coding consistent | 2 | shapes, labels, formulas, readouts, captions |
| Minimal, legible on-screen text | 2 | captions of 3-6 words; 1080p stills checked |
| Pacing | 2 | 140 s (storyboard 124 s, +13 %); 1-1.5 s holds after each reveal |
| Payoff and recap | 2 | limits stated at the extremes; recap pairs each segment with its formula |
| Matches the learning goal and requested depth | 2 | intuitive, newcomer level |
| **Total** | 20/20 | |

Stop conditions met: no open visual bugs, no FAIL, both WARNs explained, rubric 20/20 with no
criterion below 2. Rendering the final.

## Final

- File: `/home/quellen/dev/manim-video-skill/out/01-unit-circle.mp4` (copy of
  `media/videos/scene/1080p60/Explainer.mp4`), 6.4 MB.
- Duration / resolution / audio: 138.9 s, 1920x1080, 60 fps, h264, no audio stream (silent).
- Render: `render.sh final scene.py Explainer`, ok in 1060 s (load average ~10 on 4 cores from
  parallel test runs); no `LAYOUT` lines.
- Iterations: 3 previews (cap 6) + 1 final; plus one render-error fix before preview 1 and three
  1080p `still` spot checks.
- Bugs found and fixed: bound-method updaters crashing the render; frames.py beat times broken by
  evicted partial movies (worked around with `config.max_files_cached`); Circumscribe reading as
  an overline; fixed-size arc and right-angle mark; dot hidden under segments; operator spacing
  after "/"; Indicate stretching segments into labels; overlapping caption crossfades; ":" spacing;
  three motivation leaps (tangent line, flip, scale factor) and an implied-only payoff.
- Checked on the final: `qa_check.py --expect-res 1920x1080 --expect-silent`:
  PASS stream (h264 1920x1080 @ 60 fps, 138.90 s, 0 audio streams), PASS blank (1.4 s incl.
  start/end), PASS holds (53 % still time, 43 holds), PASS cuts; WARN holds at 21.4-27.5 s and
  92.5-98.6 s. Both are the known false positive: 21-27 s is the sin leg, its label and the
  coordinates appearing; 92.5-98.6 s is the cot and csc formulas being written while the
  triangle's sides pulse (checked with `frames.py --at` at eight times in that window).
  `frames.py --count 8` contact sheet viewed, plus the full 1080p frame at 130.2 s (recap):
  strokes and text crisp, nothing new.
- Rubric: 20/20 on iteration 3 (18 and 19 before).
- Assumptions: silent, because the narration question could not be asked (skill default);
  newcomer audience, intuitive depth, 16:9 1080p60.
- Storyboard in one paragraph: a point on a radius-1 circle at angle θ gives cos θ (across) and
  sin θ (up), so it sits at (cos θ, sin θ) and sin² + cos² = 1; the tangent line at the point is cut
  by the axes into tan θ and cot θ, and the centre-to-crossing distances are sec θ and csc θ; the
  small triangle, flipped and stretched until cos θ (or sin θ) is 1, becomes the big ones, giving
  tan = sin/cos, sec = 1/cos, cot = cos/sin, csc = 1/sin; a zoomed-out sweep shows tan and sec
  blowing up near 90° and cot and csc near 0°; recap pairs every segment with its formula.
- Known limitations: first quadrant only (no signs in other quadrants, no radians, no graphs, no
  1 + tan² = sec²); six concept colours on screen at once in the full picture (the request needs
  six; every colour is labelled); during the two big sweeps the on-diagram labels are hidden and
  colour-coded live readouts take over; the triangle-side `Indicate` pulse in beats 12-13
  overshoots the side ends by ~0.3 units for about a second; 140 s against a 124 s plan (+13 %).
