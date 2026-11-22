# Notes: 01-unit-circle (end-to-end test of the manim-video skill)

Request: "show a unit circle animation, with its relations to sin, cos, tan, sec, csc, and cot."
Narration could not be asked, so the skill's default (silent) was used.

## Result

- Preview iterations: **3** (cap 6), plus one render-error fix before iteration 1 and 3 full-res stills.
- Final: `/home/quellen/dev/manim-video-skill/out/01-unit-circle.mp4`, 138.9 s, 1920x1080, 60 fps, silent, 6.4 MB; `render.sh final` took 1060 s on the loaded machine.
- Rubric: 18/20 (it. 1), 19/20 (it. 2), 20/20 (it. 3).

## Bugs found and how they were fixed

| # | Found in | Bug | Fix |
|---|---|---|---|
| 1 | render attempt 1 | `TypeError: cannot pickle '_thread.lock' object`: label updaters were bound methods (`add_updater(self.place_one)`); `FadeIn` copies the label, deep-copying a bound method deep-copies the Scene | wrap every updater in a lambda |
| 2 | it. 1 (tooling) | `frames.py --beats` mislabelled every tile (tile 1 "beat 12" at 0.6 s) and missed the last ~14 s: Manim kept only 100 of 111 partial movies (`max_files_cached`), and `beat_times()` skips missing files without adding their duration | used `--holds` + `--at` for it. 1; then `config.max_files_cached = 1000` in the scene (there is no CLI flag for it in 0.22.1) |
| 3 | it. 1, recap | `Circumscribe` (buff 0.08) looked like an overline glitch on the formulas in stills | `SurroundingRectangle` drawn, held, faded |
| 4 | it. 1, sweeps | θ arc had a fixed 0.5 radius: crossed the sin leg at 80° and was oversized after the zoom-out | radius 0.16 R |
| 5 | it. 1, 1080p still | the point's dot was hidden under the tan and cot segments | `set_z_index(5)` |
| 6 | it. 1, 1080p still | "sin θ/ cos θ": thin space after the slash (`\cos` is an operator) | braces `{\cos\theta}` |
| 7 | it. 1, rubric | tangent line and the triangle flip arrived without a reason; blow-up near 90° only implied | captions "Four more, on one line", "Same shape, just bigger", explicit θ → 90°: tan θ, sec θ → ∞ (and θ → 0°) |
| 8 | it. 2, recap | `Indicate` scales a segment about its centre: the sec dimension line poked left of O and into its own label, csc below the axis | white `ShowPassingFlash` on a fresh copy of each segment; `Indicate` only on labels |
| 9 | it. 2, all beats | caption crossfade put two captions on top of each other mid-transition | `AnimationGroup(FadeOut(old), FadeIn(new), lag_ratio=0.6)` |
| 10 | it. 2, beat 14 | "θ → 90° : tan θ" (relation spacing on ":") | `\colon` |
| 11 | it. 2, beat 14 | right-angle mark kept its size after the zoom-out | side 0.09 R |
| 12 | it. 2, rubric | "Scale it by 1/cos θ" gave the factor without the reason | "Stretch until cos θ is 1" / "... sin θ is 1" |

Accepted, not fixed: in beats 12-13, `Indicate` on the moving triangle's sides overshoots their
ends by ~0.3 units for about a second; it touches no label.

## What was checked

- Every iteration: `qa_check.py --expect-silent`; render.sh `LAYOUT` lines (none in any iteration);
  my own safe-area check (±6.4 / ±3.4, printed as `LAYOUT ... SAFE-AREA`; never fired).
- Every iteration, looked at as images: it. 1 `--holds` sheets 01-04 and 20 `--at` frames inside
  sweeps, flips, zooms and recap; it. 2 and it. 3 all 15 `--beats --mid` sheets (234 tiles each),
  plus single full-size frames. 1080p stills: recap (it. 1), limit caption at 80° and stretched
  triangle (it. 3). Final: `qa_check.py --expect-res 1920x1080 --expect-silent` (PASS stream/blank/holds/cuts, two WARN holds, both explained), `frames.py --count 8` sheet, one full 1080p frame, and 8 `--at` frames in the new WARN window (92.5-98.6 s).
- qa_check WARN "holds: nothing moves for 6 s" at ~21-27 s and ~42-48 s in every preview: false
  positives. `frames.py --holds` finds 4 separate holds there (sin leg drawn, label, coordinates
  assembled; triangle fill, identity written, Indicate); freezedetect at n=0.0005 does not see a
  thin line growing on a dark 480p frame, and qa_check merges the neighbouring holds.

## Stills (`stills/`)

- `01_before_it2_recap_indicate_pokes_into_sec_label.png` / `02_after_it3_recap_flash_stays_on_segments.png`:
  bug 8 before and after (same recap moment, 480p preview frames).
- `03_similar_triangles_stretch_1080p.png`: the key "stretch until cos θ is 1" moment (1080p still).
- `04_limit_toward_90deg_1080p.png`: zoomed-out picture at 80° with all six live readouts (1080p still).
- `05_final_contact_sheet.png`: `frames.py --count 8` on the final MP4.

## Skill feedback

Most important first.

1. **`frames.py --beats` silently gives wrong times for scenes with more than 100 animations.**
   Manim CE's `max_files_cached` defaults to 100 and evicts partial movie files; `beat_times()` does
   `if not f.exists(): continue`, so every later timestamp shifts earlier, beat labels are wrong
   and the end of the video is never sampled. A 2-minute explainer easily has 100+ play/wait calls
   (this one has 118). Fix in frames.py: if any listed partial file is missing, print a warning and
   fall back to `--holds` or `--count`. Fix in the templates / render.sh: set
   `config.max_files_cached = 1000` (or document it). Note `--max_files_cached` is **not** a CLI
   flag in 0.22.1 (`Error: No such option`), so `render.sh ... -- --max_files_cached` does not work.
2. **Bound methods as updaters crash the render** (`cannot pickle '_thread.lock' object` from
   `Scene.__deepcopy__` when an animation copies the mobject). Natural code style for a
   one-method-per-beat scene class (`label.add_updater(self.place_label)`) hits it. Add to
   `api-cheatsheet.md` (Updaters) and the troubleshooting table: use `lambda m: self.place(m)`.
3. **qa_check `holds` false positives.** In every preview it reported 6 s "stalls" over beats in
   which a thin segment is drawn, a label fades in and an equation is written. Its freezedetect
   (n=0.0005) misses small motion at 480p, and it merges adjacent holds. `frames.py --holds` on the
   same video lists the separate holds correctly. Suggest a lower noise threshold, or checking
   that each merged hold really has no motion, before warning.
   The result also depends on resolution and frame rate: the final 1080p60 render reported a
   different window (92.5-98.6 s, formulas being written) and dropped the preview's 42 s one.
4. **Highlighting segments: `Indicate` and `Circumscribe` misbehave on diagrams.** `Indicate`
   scales a line about its centre, so it overshoots its endpoints and can run into labels;
   `Circumscribe` with a small buff reads as an overline glitch in stills. A short note in the
   style guide or cheatsheet ("to highlight a segment, `ShowPassingFlash` a copy of it; to
   highlight a formula, draw and fade a `SurroundingRectangle`") would have saved an iteration.
5. **SKILL.md's own example is "the unit circle and its trig functions", but scene-patterns only
   covers sin/cos.** Pattern 1 has a fixed arc radius and no label-placement rule. The six-function
   picture has two recurring layout traps that a pattern could solve once: cos and sec are
   collinear on the x-axis (I drew sec as a dimension line below the axis), and labels on slanted
   segments need an offset along the normal sized by the label's bounding box. Labels that follow
   a `ValueTracker` sweep collide at the extremes, so the pattern should fade them during big
   sweeps and show live readouts instead.
6. **LayoutGuard does not check what the style guide demands.** It checks the frame edge, not the
   ±6.4 / ±3.4 safe area, and only text-vs-text overlap, not text over lines (the main risk in a
   labelled diagram). I added a safe-area check in my scene's `play()`; it could live in
   `manim_qa.py`.
7. **Contact-sheet volume.** "Open every contact sheet" with `--beats --mid` meant 15 sheets
   (234 tiles) per iteration for a 140 s video. That's thorough but expensive. Suggest `--beats`
   (ends only) for the full pass and `--mid` or `--at` only around changed beats, or a larger
   `--per-sheet`.
8. **`render.sh still` always writes the same file name** (`media/images/scene/Explainer_ManimCE_v0.22.1.png`),
   so each still overwrites the previous one; I had to copy each one away. It could add the `-n`
   range to the name, or the docs could say so.
9. **Caption swaps.** Nothing in the style guide covers replacing one caption with another; the
   obvious `play(FadeOut(old), FadeIn(new))` overlaps both texts mid-transition. A one-line
   recommendation (lagged `AnimationGroup`, or `ReplacementTransform`) would help.
10. **Style guide vs request.** "At most 4 or 5 concept colours on screen" cannot hold for a
    request about six functions in one picture; a "unless the request needs more; then pair
    every colour with a label" clause would make the rule usable.
11. Process note (my error, not the skill's): I ran one read-only `docker ps` at the start to see
    whether other renders were running, before re-reading the test rule "Docker only through the
    skill's scripts". All rendering went through `render.sh`.

What worked well: `check_env.sh` (5 s, clear); the storyboard and review templates; the rubric
caught two real leaps (unmotivated tangent line, unexplained scale factor); `render.sh still --
-n 0,K` for 1080p spot checks (~30 s each); `frames.py --at` for frames inside sweeps; the
ManimGL pre-flight; the ValueTracker/always_redraw guidance (the whole diagram, including the
zoom-out, is driven by five trackers with no ghost objects).
