# Notes: 02-llm-weights (end-to-end test of the manim-video skill)

Request: "show a diagram animation of a modern llm weight and neuron setup". Silent (skill default; the user could not
be asked). Reference numbers: Llama 3 8B. Result: a 150 s silent explainer in 4 chapters (stack, attention, MLP neuron
and matrices, weight count) plus a hook and a recap.

## Iterations

5 preview iterations (cap 6) and 2 final renders. Iterations 1-3 converged and final render 1 was made; the Step 7
high-resolution look found a near-collision, so I went back for iterations 4 and 5. Preview renders took 229, 196,
180, 163 and 119 s (the last ones reuse cached segments); 1080p stills with `render.sh still -- -n 0,K` took 45 to
60 s each; final render 1 took 1059 s and final render 2 took 136 s (cached segments).

## Bugs found and how they were fixed

Found before the first render (self-review of the code):

- Double `FadeOut` of the old title when `swap_title` and `clear_stage` ran in one `play`: `clear_stage` now skips
  every title ever created.
- Caption lines faded in one by one were not the caption group on stage, so a later `FadeOut(group)` would have
  restored and re-faded them: the group is added after the lines appear.
- The vector kept from the attention chapter lived inside a (chip, vector) group and would have faded with it:
  `self.add(vec)` first to split it out.
- `FadeIn` of an `always_redraw` marker fights the redraw: a static copy fades in, then the live one replaces it.

Found by watching the frames:

1. (it 1) Two-line footer captions touched the token chips in the attention chapter: diagram moved up 0.35.
2. (it 1) Purple MathTex (%, scores, `W_Q`..`W_O`) unreadable: thin Computer Modern glyphs in `PURPLE` on near-black.
   Text-weight tint `PURPLE_A`, sizes 34 to 38.
3. (it 1) MathTex numbers looked smaller than the Text beside them: +2 to +4 font size.
4. (it 1, rubric) "value" used before it was named; to-scale rectangles never said area means count: both now said.
5. (it 1) 154.5 s, over the 150 s default: waits trimmed (final 150.0 s).
6. (it 2) "block 1" morphed through garbled glyphs into "block 32": shapes copied, label faded in.
7. (it 2) Five dashed q-k lines bunched into a band skimming the key chips: replaced by copies of q that slide above each key.
8. (it 2) Input digits garbled while `Transform`ing "0.8" into "−0.7" (different glyph counts): cross-fade instead.
9. (it 2) The `matrix × vector` sweep lit only neuron 1 (random rows gave the other neurons sums ≤ 0), contradicting
   "every neuron at once": explicit rows (two fire, one partly, one faintly, two quiet) and a matching caption.
10. (it 2) The semicolon after "query" was coloured: `t2c` key fixed.
11. (final 1, 1080p) "bed" in the prediction panel touched the tip of the "block 32" brace (invisible at 480p; the
    guard does not check text against shapes): rows 0.4 apart instead of 0.45, group 0.2 to the right.
12. (it 4, caught by `LAYOUT END`) A `W_K`/`W_V` rectangle stayed on screen from the scale chapter to the end. My
    `clear_stage` stored title `id()`s; a garbage-collected title's id was reused by a new Rectangle, which was then
    "kept as a title". It was nondeterministic and appeared only after an unrelated edit. Fixed by keeping the
    title objects themselves.

Before/after stills: `stills/01` vs `02` (bugs 1 and 2), `stills/03` vs `04` (bug 9); `stills/05` is a 1080p frame of the final, `stills/06` the final contact sheet (`frames.py --count 8`).

## What was checked

- `qa_check.py` on every preview and both finals: all PASS every time. It never flagged any of the bugs above;
  they were all found by looking.
- `LayoutGuard`: one warning in all renders, the `LAYOUT END` that caught bug 12 in iteration 4; none in the
  final. Because the template's import fallback is silent, I added a `LAYOUT WARNING` print to it; that never
  appeared, so the guard really was active.
- Stills: iteration 1 via `--holds` and `--count 48` (see the `--beats` bug below); iteration 2 all 16 `--beats --mid`
  sheets; iterations 3 and 5 the changed-beat sheets plus a `--holds` overview of the whole video; two 1080p stills
  from `render.sh still`; both finals via `--count 8`, full-size frames, a 2x crop of the output panel and the last frame.
- Every number on screen recomputed: softmax of the shown scores = 5/20/31/34/10 %; neuron sum 1.60, GELU 1.51, update
  vector; Llama 3 8B counts (Q, O 4096², K, V 1024×4096, gate/up/down 14336×4096; 42 M + 176 M = 218 M per block;
  5.64 + 1.34 + 1.05 = 8.03 B; vocabulary 128,256; 32 blocks; 32 query heads).

## Skill feedback

Most important first.

1. **Step 7 has no "what if the final is wrong" path.** The 1080p look at the final found a real collision that
   480p hid. SKILL.md does not say whether to go back to Step 6, or whether that counts against the 6-preview cap.
   I went back and counted it (5 previews in total). Two cheaper ways to catch it before the final: render the
   `render.sh still` checks of the busiest frames at 1080p as part of every iteration (not only "where text is
   small"), or offer a `PREVIEW_QUALITY=m` (720p) pass before the final.

2. **`frames.py --beats` gives wrong times and labels for any video with more than 100 segments, and says
   nothing.** Manim's default `max_files_cached` is 100. This 150 s scene has 131 `play`/`wait` calls, so Manim
   evicted the first 31 partial movies after combining them (the log says "removed 31 least recently used
   segment(s)"). `beat_times()` does `if not f.exists(): continue` without adding the missing duration. Tile 1 was
   labelled "beat 32", every time was shifted, and the last 30 s were never sampled. Any 2-minute explainer hits
   this. Fix: `render.sh` should pass `--max_files_cached` (or the templates should set `config.max_files_cached`),
   and `frames.py` should fail or fall back to `--holds` with a warning when list entries are missing. My workaround
   was `config.max_files_cached = 1000` in the scene.
3. **A disabled LayoutGuard cannot be told apart from a clean pass.** The template's `except ImportError: class
   LayoutGuard: pass` is silent, and a clean run prints no `LAYOUT` lines either. Suggest printing a warning in the
   fallback (as I did), or having `render.sh` print "LayoutGuard active, N checks" from the log.
4. **LayoutGuard missed the main iteration-1 bug.** It only checks text against text and against the frame edge.
   A caption touching the chip boxes (shapes), and anything between the safe area (±6.4, ±3.4) and the frame edge,
   pass silently. An optional text-against-shape check and a safe-area check would have caught it.
5. **Colour guidance does not survive MathTex.** `PURPLE` is a listed concept colour, but MathTex in `PURPLE` at size
   30 was unreadable on `#0F1117`. The style guide should say: use the `_A`/`_B` tints for coloured text and maths,
   and size MathTex and DecimalNumber about 4 points larger than Text, because Computer Modern looks smaller and
   thinner at the same `font_size`.
6. **Style-guide contradiction.** "`to_edge(..., buff=0.5)` or more" puts a title's top at y = 3.5, outside the
   stated safe area (y ≤ 3.4); `templates/scene_silent.py` does exactly this. Use `buff=0.6` for top and bottom.
7. **The full-contact-sheet rule is expensive at this length.** `--beats --mid` on 150 s gave 256 tiles on 16 sheets.
   Viewing all of them every iteration is costly. Suggest `--holds` (about 40 tiles) for the full pass and
   `--beats --mid` only for changed beats, and a `--from/--to` time range in `frames.py`. Mapping sheets to time
   ranges needed a small script; `index.txt` could print a per-sheet time range.
8. **Undocumented numbering mismatch.** `frames.py` beat numbers are 1-based segments, while `render.sh still -- -n
   0,K` takes 0-based animation numbers (K = beat − 1), and waits count as animations. One line in SKILL.md Step 4
   would save the guesswork.
9. **`frames.py` overwrites its default output folder** (`frames_<stem>`) on every run, so before/after comparisons
   are lost unless you pass `--out` per iteration. Worth a note in Step 4, or a per-run default folder.
10. **Missing gotchas in the cheatsheet.** `Transform` between Text or DecimalNumbers with different glyph counts shows
   garbled mid-frames; prefer a cross-fade or `FadeTransform` for changing labels, and do not `TransformFromCopy` a
   group that contains a label whose text changes. `always_redraw` objects also fight `FadeIn`, not only
   `FadeOut`/`Transform`.
11. **LayoutGuard's `LAYOUT END` line was valuable, but its keys share the same id-reuse hazard.** It caught my
    id-reuse lifecycle bug. `manim_qa.py` itself keys `_qa_seen` and `_qa_ignored` by `id(mob)`; after garbage
    collection a new object can inherit an id, so a real problem can be suppressed as "already reported" or
    "ignored". Keeping references (or using a `WeakSet`) would avoid that. Scene authors need the same warning
    (never keep stage bookkeeping by `id()` alone); a line in the cheatsheet's gotchas would help.
12. **`LAYOUT END` in still renders.** `render.sh still` prints "LAYOUT END 22 objects still on screen" under "scene
    warnings", which is expected for a mid-scene still but reads as a warning. Suppress it when `-n` stops the scene early.
13. **What worked well.** `check_env.sh` was fast and clear. The storyboard template and the intuition rubric gave a
    useful structure; the rubric's "is a term used before it is shown" question found the "value" leap. The
    `TinyNetwork` and `Pipeline` patterns were good starting points. `render.sh` output (VIDEO line with
    w/h/fps/duration) and `qa_check.py` were easy to use. No ManimGL issues, no LaTeX or font problems (Noto Sans had
    "−", "≈", "×" and curly quotes).
