# Review log: Inside a large language model, weights and neurons (container-route run)

Scene: `scene.py`, class `Explainer` (started from `examples/02-llm-weights/scene.py` on the
owner's instruction; same content and length, 150 s). Narration: silent (skill default; unattended
run). Rendered only with `scripts/render-in-container.sh`. My own discarded first attempt (an
85-95 s scene) and its review are in `own-attempt/`.

Fixed before the first preview (the known limitation in `examples/README.md`): titles and captions
crossfaded, so old and new text overlapped for about 1 s. `swap_title`/`swap_caption` now fade the
old text out in the first half of the play and the new text in during the second half (same play
time, so the length stays 150.0 s).

## Iteration 1 (preview)

- `out/Explainer-preview.mp4`, 150.0 s, 854x480 @ 15. report.md: PASS (stream, blank, holds 30 %
  across 40 holds, cuts). Wrapper 186 s (render 151, checks 3, stills 32).
- LAYOUT: 1 UNSAFE caption, 10 CROSSED (weight labels on their edges).
- Looked at: all 16 sheets; full-res `--still 48` (prediction), `--still 69` (q/k + W matrices),
  `--still 93` (neuron complete).

| Beat / time | Bug | Fix |
|---|---|---|
| 1 / 4.5 s | "?" FadeTransforms into "mat": garbled glyphs mid-swap | "?" out in the first half, "mat" in during the second |
| 1 / 7 s | `Indicate` fills the LLM box yellow; "LLM" unreadable for 0.5 s | flash of the box outline (`ShowPassingFlash`) |
| 5 / 27.9 s | old caption "each vector flows upward" overlaps "attention: across tokens" (this beat fades captions by hand) | same out-then-in split |
| 7 / 39 s | LAYOUT UNSAFE: caption "each block adds an update" past x = 6.5 | "blocks add updates" |
| 9 / 58 s | `Circumscribe` leaves a stray yellow underline under block 1 | `SurroundingRectangle` created, cleared with the stage |
| 10 / 79 s | scores FadeTransform into % with overlapping digits ("5%8") | out-then-in split |
| 11 / 95, 100 s | input digits crossfade ("-0.87") | out-then-in split |
| 11 / 84-108 s | LAYOUT CROSSED x10: weight labels sit on their edges (intended, background plate) | `qa_ignore` |
| 12 / 113-116 s | edges morph into W_up rows: ragged polygons for 1.4 s (known limitation of the example) | each neuron's edges flash, then its row slides in (same colours, same order) |

## Iteration 2 (preview)

- 150.0 s; PASS; LAYOUT none. Wrapper 298 s (render 173, checks 22, stills 104; host busy).
- Looked at: sheets 1, 4, 6, 8, 9, 11, 13 (changed beats) and the overview.
- All fixes visible except beat 5: the caption overlap at 27.9 s was still there.
  **Cause: Manim reused the cached segment (`Animation 29 : Using cached data`).** Its cache key
  replaces any object already seen in the same `play()` by a placeholder; the caption's new rate
  function (`first_half`) was already used by the title in that play, and the old one (`smooth`)
  by other animations, so both versions hashed the same. Fix: captions get their own rate
  functions (`cap_out`/`cap_in`, different source), which changes the key.
- Geometry (owner's new gate), measured on the stills: hook row centred on "?" so "mat" pushed it
  0.35 right; neuron figure symmetric about x = -0.8 instead of the centre; MLP-matrix chapter
  0.3 right (margins 1.0 / 1.6). All re-centred.

## Iteration 3 (preview)

- 150.0 s; PASS + WARN (GeometryGuard not used yet). Wrapper 270 s.
- Checked: anim 29 mid-frame (both captions gone at mid-swap: fixed), neuron and matrix frames.

## Iteration 4 (preview, first with GeometryGuard)

23 rules: hook `centered_in` frame; stack chapter: lane diagram `symmetric` about the centre of its
zone (x -7.11..1.8), embedding table and prediction bars `symmetric` about the panel centre
(x 1.8..7.11); attention row, neuron, neuron in/out vectors, MLP figure, one-block chart, model
bar `symmetric`/`centered_in` the frame; activation x-axis symmetric about its origin; recap
centred; `within_margin` 7 % for every figure. Rules are declared once a figure is complete and
the name is retired before the figure is taken apart.
Lanes moved 0.155 left to the zone centre (chips keep 7.8 %), table and bars into the panel centre
(bars 1.9/0.9/0.4 long to keep 7 %), hook row to y = 0.

- report.md: **FAIL geometry**, 3 violations (exit 1):
  - `centered_in(hook)` 2.46 right and `symmetric(prediction)` "-1.43 right": measuring artefact.
    GeometryGuard measures a tracked group's first-level members that are on screen; nested groups
    whose items were added one by one (the words, the bar rows) were dropped silently. Fix: track
    flattened leaf mobjects (`leaves(...)`).
  - `within_margin(plot, 7%)`: right margin 6.4 % (the "sum" label): plot 0.2 left.

## Iteration 5 (preview)

- 150.0 s. report.md: **PASS** (stream, blank, holds 30 % / 39, cuts, geometry: all 23 rules and
  the frame-edge rule hold over 131 animations; no UNCHECKED). LAYOUT none. Wrapper 213 s.
- geometry.json: every figure centred within 0.15 of its zone, minimum margins 7.5-17 %.
- Looked at: sheets 6, 10, 14 plus hook, table, prediction and neuron stills.
- Found one collision the checkers missed: at 96 s the readout "out -0.09" touches the footnote
  "Llama-style MLPs: gated (SwiGLU)" (re-centring moved the neuron right; LayoutGuard's overlap
  threshold is 12 %). Fix: footnote on two short lines under the plot. Static label only, so
  verified with full-res `--still 85` (clear), plus `--still 48` and `--still 93`.

### Intuitiveness (references/intuition-rubric.md)

Newcomer summary: text is cut into tokens, each token becomes a vector that rides up its own lane
through 32 blocks; in each block attention lets a token pull information from earlier tokens (how
much is set by query-key match scores) and an MLP of neurons, each a weighted sum and a bend,
writes an update back. Every connection is a learned weight stored in matrices: about 8 billion
numbers in an 8B model. Matches the learning goal.

| Criterion | Score 0-2 | Note |
|---|---|---|
| Concrete anchor first | 2 | "The cat sat on the" -> "mat" |
| One idea per beat | 1 | the q/k beat and the neuron beat each carry 2-3 sequenced ideas (one caption each) |
| Every step motivated (no leaps) | 2 | each zoom answers "what happens inside"; values and area explained |
| Picture before formula | 2 | no formulas; names after pictures |
| Progressive reveal | 2 | built piece by piece; rows now appear neuron by neuron |
| Colour coding consistent | 2 | legend followed, text tints included |
| Minimal, legible on-screen text | 2 | no overlapping text at rest or mid-swap; crisp at 1080p |
| Pacing (holds after reveals, not dragging) | 2 | 150.0 s, 39 holds |
| Payoff and recap | 2 | 8.0 B bar, then the recap with icons |
| Matches the learning goal and requested depth | 2 | intuitive, Llama 3 8B numbers |
| **Total** | **19/20** | geometry PASS, so no cap |

## Final (render 1 of at most 3)

- File: `/home/quellen/dev/manim-video-skill/out/container-runs/02-llm-weights/out/Explainer-final.mp4`
  (9.8 MB). 150.00 s (the earlier final: 150.0 s), 1920x1080 @ 60 fps, H.264, no audio (silent).
- out/report.md: **PASS**: stream, blank (0.0 s), holds (30 % across 37), cuts, geometry (all 23
  rules and the frame-edge rule over 131 animations, none unchecked). LAYOUT lines: none.
- Timings (summary.json): render 1217.3 + checks 219.5 + stills 8.7 = 1445.5 s (host load ~11 on
  4 cores). The wrapper then died with `line 252: syntax error` and exit 2: the script file was
  replaced on disk (mtime 23:18:05) while this run was still executing; the container had already
  finished and every output in `out/` is complete.
- Looked at: the final contact sheet (8 even stills, mid-transition frames: no overlapping text),
  full-size 103.1 s, and `--frames --at 52,96.3,128,146` (prediction, negative-sum neuron with the
  two-line footnote, matrices, recap): clean.
- Iterations: 5 previews of this scene (plus 2 previews and 1 failed render of my discarded own
  scene), 13 full-res `--still` frames, 1 final.
- Rubric: 19/20 (one idea per beat 1/2). Geometry PASS.
- Assumptions: silent; newcomer, high-school maths, intuitive; 1920x1080 at 60 fps; Llama 3 8B
  as the reference model (as in the example).
- Known limitations: toy values for probabilities, attention scores and weights; the row-to-column
  morphs (table row into a token vector, x into a row) pass through a diagonal staircase for about
  1 s, which reads as a rotation; about 1 s of sparse stage at the start of the scale chapter.
