# Review log: Inside a large language model, weights and neurons

Scene: `scene.py`, class `Explainer`. Narration: silent (skill default; the user could not be asked).

## Iteration 1 (preview)

- Video: `media/videos/scene/480p15/Explainer.mp4` (154.5 s, 854x480 @ 15 fps), render 229 s, 131 animations.
- `qa_check.py --expect-silent`: PASS stream, PASS blank (0.0 s), PASS holds (42 % still, 54 holds), PASS cuts. Overall PASS.
- `LAYOUT` warnings: none printed (and no `LAYOUT END` line, consistent with the stage being cleared at the end).
- Stills looked at: `frames.py --beats --mid` gave **wrong times and labels** (see the tooling note below), so I used
  `--holds` (43 resting stills, `media/frames_it1/sheet_01..03`) and `--count 48` (`media/frames_it1_even/sheet_01..03`),
  plus full-size stills at 64.9 s (attention), 78.6 s (q/k + matrices), 92.9 s (neuron + activation), 139.4 s (scale).

Tooling note: Manim's segment cache keeps 100 files (`max_files_cached`), and this scene has about 200 segments, so it
evicted the first 31 partial movies. `frames.py` skips missing segments without adding their duration, so every beat
time was shifted and labelled from "beat 32", and the last 30 s were never sampled. Workaround for later iterations:
`config.max_files_cached = 1000` in the scene.

### Visual bugs (references/visual-qa-checklist.md)

| Beat / time | Bug | Fix |
|---|---|---|
| 9 / 61.7-65 s, 10 / 77-80 s | Two-line footer captions touch the bottom of the token chips (the attention diagram sits too low). | Move the whole attention diagram up 0.35; lower the query chip; move the matrices row up and left so the dashed q-k lines stay clear. |
| 9, 10 / 58-80 s | Percentages, scores and the `W_Q`..`W_O` labels are thin MathTex in `PURPLE` on near-black: low contrast, hard to read at 480p. | Text-weight purple (`PURPLE_A`) for purple labels, font 34-38. |
| 11 / 84-108 s | MathTex numbers (cell values 28, weight labels 26, sum/out readouts 30) look smaller than the Text beside them. | Cell numbers 30, edge weights 30, readouts 34. |
| 13 / 135-140 s | `W_Q`..`W_down` labels under the to-scale rectangles: thin, purple ones low contrast. | Font 36, `PURPLE_A` for the attention labels. |
| 8 / 50-58 s | The top probability bar sits close to the title band. | Bars 0.05 lower. |
| all | Captions and titles cross-fade in place, so mid-transition stills show two overlapping lines for about 1 s. | Kept: a normal cross-fade, never visible at rest. |

### Intuitiveness (references/intuition-rubric.md)

Newcomer summary: text is cut into tokens, each token becomes a vector of numbers that rides up a lane through 32
blocks; in each block attention lets a token pull information from earlier tokens (how much is decided by
query · key match scores) and an MLP of neurons, each a weighted sum followed by a bend, writes updates back. All
the connections are weights stored in matrices, about 8 billion numbers in an 8B model, most of them in the MLPs.
This matches the learning goal.

| Criterion | Score 0-2 | Note |
|---|---|---|
| Concrete anchor first | 2 | "The cat sat on the" goes in, "mat" comes out |
| One idea per beat | 2 | each caption carries one idea; the neuron beat is long (24 s) but sequenced |
| Every step motivated (no leaps) | 1 | "value" appears in the matrices beat but was only called "information"; the to-scale rectangles never say that area means count |
| Picture before formula | 2 | no formulas; matrix names arrive after the pictures |
| Progressive reveal | 2 | stack, block, neuron and matrix are all built piece by piece |
| Colour coding consistent | 2 | legend followed (sign = blue/orange, attention purple, MLP teal, prediction green) |
| Minimal, legible on-screen text | 1 | short labels, but thin purple MathTex and small numbers; caption/chip collision |
| Pacing (holds after reveals, not dragging) | 2 | holds after every reveal; 154.5 s is 10 % over the 140 s plan |
| Payoff and recap | 2 | "≈ 8.0 billion weights" bar, then a four-line recap with icons |
| Matches the learning goal and requested depth | 2 | intuitive, technically accurate (Llama 3 8B numbers) |
| **Total** | 18/20 | passes, but the bugs above must be fixed |

Also planned: trim about 5 s of waits to get under the 150 s default.

## Iteration 2 (preview)

Changes: attention diagram up 0.35, `PURPLE_A` for purple text and maths, larger numbers (cells 30, edge weights 30,
readouts 34, scores and % 34, matrix labels 36-38), "(values)" named in the attention caption, "(drawn to scale: area =
number of weights)" added, bars 0.05 lower, waits trimmed, `config.max_files_cached = 1000` (so `frames.py --beats`
works), and the `LayoutGuard` import fallback now prints a `LAYOUT WARNING` (so "no LAYOUT lines" can be trusted).

- Video: 151.7 s, render 196 s. `qa_check.py --expect-silent`: all PASS (40 % still, 55 holds, no cuts).
- `LAYOUT` warnings: none, and no fallback warning, so the guard is active and found nothing.
- Stills looked at: `frames.py --beats --mid` now correct (131 of 131 segments present): all 16 sheets
  (`media/frames_it2/sheet_01..16`), plus full-size 480p stills at 67.8, 78.6, 82.0, 97.7 and 134.9 s.

| Beat / time | Bug | Fix |
|---|---|---|
| 9-10 (re-check) | caption/chip collision and purple contrast | **fixed** (seen at 67.8 and 78.6 s) |
| 13 (re-check) | scale labels thin | **fixed** (seen at 134.9 s) |
| 6 / 37-38 s | "block 1" morphs through garbled glyphs into "block 32" (`TransformFromCopy` of the label) | Copy only the shapes; fade the new label in. |
| 10 / 73-77 s | The five dashed q-k lines bunch into one band that skims the tops of the key chips (about 0.06 units of clearance). | Replace the lines with copies of q that slide above each key and fade when the scores become %. Real q raised so its copy above "the" does not overlap it. |
| 11 / 95-101 s | Changing the input digits with `Transform` ("0.8" to "−0.7", different glyph counts) shows garbled glyphs for about 1 s. | Cross-fade old and new numbers (and swap them in the vector group). |
| 12 / 118-125 s | The `matrix × vector` sweep lights only neuron 1 (random rows give the other neurons sums ≤ 0), which undercuts "every neuron at once". | Explicit rows: two fire, one partly, one faintly, two quiet; new caption "some neurons fire, others stay quiet". |
| 10 / 70 s | The semicolon after "query" is coloured purple. | `t2c` key "query" instead of "query;". |

Rubric: criterion 3 now 2 (values named, area explained), criterion 7 now 2 (text legible at 480p). Total 19/20
(criterion 2 at 1: the q/k beat carries "match score" and "made by weight matrices", the neuron beat carries sum,
bend and write-back, each with its own caption).

## Iteration 3 (preview)

- Video: 150.0 s, render 180 s. `qa_check.py --expect-silent`: PASS stream, PASS blank (0.0 s), PASS holds (39 %
  still, 55 holds), PASS cuts. Overall PASS.
- `LAYOUT` warnings: none (guard active).
- Stills looked at: changed beats in `media/frames_it3/sheet_05, 08, 09, 11, 13, 14` (`--beats --mid`), the whole
  video at rest in `media/frames_it3_holds/sheet_01..03`, and two 1080p stills from `render.sh still -- -n 0,93`
  (final neuron state) and `-n 0,118` (matrix sizes and footnote): every label, including the 24 pt footnotes and
  the MathTex subscripts, is crisp.

| Beat / time | Check | Result |
|---|---|---|
| 6 / 37 s | "block 32" label | fades in cleanly, **fixed** |
| 10 / 71-76 s | copies of q above each key, scores, then % | clear, no line clutter, **fixed** |
| 11 / 95-101 s | input numbers change | clean cross-fade, **fixed** |
| 12 / 120-126 s | sweep: neurons 1 and 5 fire, 2 partly, 4 faintly, 3 and 6 quiet | **fixed**, matches the caption |
| 11 / 104.9 s | numbers: 0.8·0.9 − 0.5·(−0.6) + 0.3·0.1 + 0.9·0.7 − 0.2·0.4 = 1.60; GELU(1.60) = 1.51; 1.51 × (0.5, −0.3, 0.8, 0.2, −0.6) = (0.76, −0.45, 1.21, 0.30, −0.91) | correct |
| 10 | softmax of the shown scores (−0.8, 0.6, 1.0, 1.1, −0.1) = 5, 20, 31, 34, 10 % (sums to 100) | correct |
| 13 | 42 M + 176 M = 218 M per block; 5.6 + 1.3 + 1.1 = 8.0 B (Llama 3 8B: 8.03 B) | correct |
| all | cross-fading titles and captions overlap for about 1 s mid-transition; edges morphing into matrix rows look ragged mid-morph (1.4 s) | accepted: never visible at rest |
| 13 / 131 s | about 0.5 s of near-empty stage while the rectangles start growing (`smooth` starts slowly) | accepted: soft start, qa_check finds no stall |

Newcomer summary: unchanged from iteration 1 and matching the learning goal; the attention chapter now also says
that what flows along the arcs are "values", and the scale chapter says that area means count.

| Criterion | Score 0-2 | Note |
|---|---|---|
| Concrete anchor first | 2 | "The cat sat on the" -> "mat" |
| One idea per beat | 1 | q/k beat and neuron beat each carry two or three sequenced ideas (one caption each) |
| Every step motivated (no leaps) | 2 | each zoom answers "what happens inside"; values and area explained |
| Picture before formula | 2 | no formulas; names after pictures |
| Progressive reveal | 2 | built piece by piece throughout |
| Colour coding consistent | 2 | legend followed, including text tints |
| Minimal, legible on-screen text | 2 | short captions; legible at 480p and crisp at 1080p |
| Pacing (holds after reveals, not dragging) | 2 | 150 s; holds after every reveal |
| Payoff and recap | 2 | 8.0 B bar, then the recap with icons |
| Matches the learning goal and requested depth | 2 | intuitive and accurate |
| **Total** | 19/20 | passes; no open visual bugs |

Decision: stop iterating (3 of 6 previews used); render the final.

## Final render 1 (rejected at Step 7)

- `render.sh final` (1059 s): 1920x1080 @ 60 fps, 150.0 s; `qa_check.py --expect-res 1920x1080 --expect-silent`:
  all PASS; no `LAYOUT` lines.
- Step 7 high-resolution look (`frames.py --count 8`, plus full-size frames at 51.0 and 107.0 s, and a 2x crop of
  the output panel): **the word "bed" touches the tip of the "block 32" brace** in the prediction beat (8 / 48-52 s).
  It was invisible at 480p and LayoutGuard does not check text against shapes. Not shipped; back to Step 6.

## Iteration 4 (preview)

- Fix: output rows 0.4 apart instead of 0.45 (the lowest row ends 0.15 higher), and the bar group 0.2 to the right.
- Render 163 s, 150.0 s. **New `LAYOUT END 1 object(s) still on screen: Rectangle`**: the last frame shows a small
  purple rectangle (`W_K`/`W_V` from the scale chapter) that stays through the bar chart and the recap.
- Cause: my `clear_stage` remembered titles by `id()` only. Once an old title was garbage-collected, a new Rectangle
  could get the same id and was then kept on stage as if it were a title. It is nondeterministic: the layout edit
  changed allocation, so it showed up only now. (Final render 1 happened to be clean: its log has no `LAYOUT END` line.)

## Iteration 5 (preview)

- Fix: keep the title objects themselves in a list, so their ids cannot be reused.
- Render 119 s (cached segments), 150.0 s. `qa_check.py --expect-silent`: all PASS (39 % still, 55 holds, no cuts).
  `LAYOUT`: none (no `END` line). Last frame: only the recap's final fade.
- Stills looked at: `media/frames_it5/sheet_06` (prediction beat, "bed" now clear of the brace) and `sheet_16`
  (scale and recap: no leftover rectangle), the whole video at rest in `media/frames_it5_holds/sheet_01..03`, and the
  last frame. Rubric unchanged: 19/20.

## Final

- File: `/home/quellen/dev/manim-video-skill/out/02-llm-weights.mp4` (copy of
  `/home/quellen/dev/manim-video-skill/examples/02-llm-weights/media/videos/scene/1080p60/Explainer.mp4`), 10.8 MB.
- Duration / resolution / audio: 150.0 s, 1920x1080, 60 fps, H.264, no audio stream (silent).
- Iterations: 5 previews (cap 6) + 2 final renders (final 1 rejected at the Step 7 high-resolution look; final 2
  rendered in 136 s from cached segments).
- `qa_check.py --expect-res 1920x1080 --expect-silent` on the final:
  `PASS stream h264 1920x1080 @ 60 fps, 150.00s, 0 audio stream(s)` / `PASS blank no long empty-screen stretches
  (total 0.0s, incl. start/end)` / `PASS holds 40% still time across 47 hold(s)` / `PASS cuts no abrupt full-frame
  changes` / overall PASS. `LAYOUT` lines in the final log: 0.
- Storyboard in one paragraph: "The cat sat on the" goes into an LLM box and "mat" comes out. The text becomes 5
  token chips; each token looks up its row of an embedding table and becomes a vector (5 of 4,096 numbers drawn) on
  its own lane, the residual stream. A block is a purple attention band across all lanes plus a teal MLP box on each
  lane; 32 such blocks stack up. The vectors rise and recolour as each block adds an update, and the last token's
  top vector scores the next token ("mat" highest). Zoom into attention: arcs from earlier tokens into "the" (5, 20,
  31, 34, 10 %), values flow along them; the shares come from query · key match scores and a softmax, and q, k, v
  come from weight matrices W_Q, W_K, W_V, W_O (32 heads). Zoom into one MLP neuron: weighted edges (numbers),
  sum 1.60, a GELU bend gives 1.51 and the neuron glows; a different input gives a negative sum and the neuron
  stays quiet; its output weights write an update back. Many neurons: their edges fold into the rows of W_up, a
  matrix × vector sweep lights some neurons, W_down holds the output weights, real sizes 14,336 × 4,096. Count the
  weights for Llama 3 8B: one block's 7 matrices to scale (attention 42 M, MLP 176 M), then a bar for the whole
  model (≈ 8.0 B: MLP 5.6 B, attention 1.3 B, embedding tables 1.1 B), all set by training. Recap in four lines.
- Bugs found and fixed: 4 lifecycle bugs found in code review before the first render; 12 found by watching
  (see notes.md): caption/chip collision; low-contrast purple MathTex; small MathTex numbers; "value" leap;
  unexplained area scale; over-length (154.5 s); garbled "block 32" morph; bunched q-k lines; garbled digit
  morph; a sweep lighting one neuron; a coloured semicolon; "bed" touching the block-32 brace at 1080p; and a
  scale-chapter rectangle left on screen through the recap (id-reuse bug in my `clear_stage`, caught by `LAYOUT END`).
- Checked: `qa_check.py` on every preview and both finals; `LayoutGuard` (confirmed active); every `--beats --mid`
  sheet of iteration 2; changed-beat sheets and `--holds` overviews of iterations 3 and 5; 1080p stills
  (`render.sh still`) of the neuron and matrix frames; the final's `--count 8` contact sheet, two full-size frames,
  a 2x crop of the output panel and the last frame; every number on screen recomputed (see iteration 3).
- Rubric: 19/20 (one idea per beat 1/2; everything else 2/2).
- Assumptions: silent video (skill default; the user could not be asked about narration); newcomer audience,
  intuitive depth, 60 to 150 s, 1920x1080 at 60 fps; Llama 3 8B as the reference "modern LLM" for real sizes.
- Left out on purpose: normalisation (RMSNorm), positional encoding (RoPE), sampling and temperature, the KV
  cache, training and backprop, mixture-of-experts, details of multi-head and grouped-query attention (K and V are
  drawn to their real, smaller size without explanation), the tokenizer algorithm, the 1/√d scaling in attention.
  The gated SwiGLU MLP is drawn as a plain GELU neuron, with a footnote and the third (gate) matrix in the count.
- Known limitations: probabilities, attention scores and weights are illustrative toy values, not taken from a real
  model. Titles and captions cross-fade in place (two lines overlap for about 1 s mid-transition), and the edge-to-row
  morph looks ragged mid-morph; neither is visible at rest. Two places hold about 1 s of slightly sparse stage
  (the start of the scale chapter, the restored input before the sum recomputes).
