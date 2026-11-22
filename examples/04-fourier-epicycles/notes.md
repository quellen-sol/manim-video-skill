# Notes: 04-fourier-epicycles

Request: "Show the Fourier series as rotating circles (epicycles) drawing a shape." Silent.

## Result

- Final: `/home/quellen/dev/manim-video-skill/out/04-fourier-epicycles.mp4`, 129.5 s, 1920x1080 @ 60 fps, silent, 6.3 MB
- Iterations: 2 full previews (480p15), plus 2 full-resolution stills of the one frame changed
  after preview 2, then the final (`render.sh final`).
- Rubric: 18/20 after preview 1, 20/20 after preview 2.

## Planning choices

- Shape: a lightning bolt (7-vertex polygon), chosen after a quick spectrum check
  (`/tmp` script, pure Python): a regular star has only every 5th coefficient non-zero, so after
  3 arrows all the rest are under 1/50 of its size and "50 arrows" would look like 3; the bolt
  is irregular and has sharp corners, so about 13 arrows are visibly sized (a real chain of
  circles) and the 1 -> 3 -> 10 -> 50 progression goes circle, blob, rough bolt, sharp bolt.
- Build-up: one arrow (circle) -> length and speed (1 turn vs 2 turns backwards) -> tip to tail
  (circle on circle: a rounded triangle) -> 5 arrows (a fancier closed curve) -> "Which arrows
  draw this?" -> Fourier's arrows for the bolt, 1, 3, 10, 50, each result kept as a thumbnail ->
  recap row -> `pen = arrow1 + arrow2 + ...  = sum c_k e^{ikt}`.
- The pen path is computed exactly (sum of the terms over 1600 samples per loop), not with
  `TracedPath`, so the curve is the same at 15 and 60 fps and can be frozen, copied into a
  thumbnail and rewound. With whole-number speeds the rig is identical at t = 0 and t = 1, so
  each pass rewinds invisibly and new arrows grow out of the current tip.
- Rigs are `always_redraw` objects that read opacity trackers (rig, circles, pen, pivot), so they
  fade in and out without animating an updater-driven mobject (no `zip()` crash, no pop-ins).

## Bugs found and fixed

1. Formula labels ("an arrow", "spins k turns per loop") under braces sat on the sum's subscript
   `k` (LayoutGuard OVERLAP x2, confirmed in the frame), and the inline `k` was tiny. Fixed with a
   two-line formula and a separate legend row; checked at 1080p (`stills/01` -> `stills/02`).
2. `TransformMatchingTex` from `pen = arrow1 + ...` to `pen(t) = sum c_k e^{ikt}` matched almost
   nothing, so mid-way it crossfaded two whole equations on the same spot. Fixed: line 2 is
   written under line 1, aligned on `=`.
3. Recap thumbnails crossed each other on the way from the 2x2 panel to the row (the 10-arrow
   thumbnail ran through "3 arrows"). Fixed with a staggered `LaggedStart` (`stills/03` ->
   `stills/04`).
4. Caption changes overlapped two captions at half opacity. Fixed: old caption fades out first
   (`AnimationGroup(..., lag_ratio=0.6)`).
5. Beat 5's three new arrows (0.35/0.2/0.12 long) were nearly invisible at 480p. Made them
   0.4/0.25/0.15 after an extent check (rig stays in y -3.14..2.34).
6. Leap (rubric 3 = 1): the bolt's arrows appeared with no hint where they come from. Added
   "Fourier's recipe gives the arrows" and pass captions ordered "biggest first", "small fast ones
   add detail". (The first draft of that caption was 51 characters, about 13.8 units at font 40,
   wider than the safe area; caught by estimating, since LayoutGuard would not have flagged it.)
7. `LAYOUT END 5 object(s) still on screen: Group x5`: not a real leftover; see skill feedback 1.
   Worked around by growing arrows with per-tracker lagged rate functions instead of `LaggedStart`.
8. Legend items on two different baselines (about 8 px at 1080p). Fixed by aligning the words'
   flat-bottomed letters and the `k` to the bottom of `c`; checked with a 1080p still.

## What was checked

- Every preview: `qa_check.py --expect-silent` (all PASS both times), `frames.py --beats --mid`
  and all 10 contact sheets opened and looked at each time, plus full-size frames of the formula,
  the 50-arrow pass, the recap move and beat 5; two 1080p stills of the formula frame.
- Final: `qa_check.py --expect-res 1920x1080 --expect-silent`, `frames.py --count 8` contact sheet
  opened and looked at, plus two full 1080p frames (24.3 s, 105.2 s). qa_check on the
  final: PASS stream (h264 1920x1080 @ 60 fps, 129.50 s, 0 audio), PASS blank (0.8 s), PASS holds
  (35 % across 33 holds), PASS cuts; overall PASS. No LAYOUT lines in the final log.

## Skill feedback

Most important first.

1. **LayoutGuard reports invisible ValueTracker groups as leftovers.** `LaggedStart` (or
   `AnimationGroup`) over `tracker.animate...` adds a `Group` of ValueTrackers to the scene, and
   `LAYOUT END` then lists `Group, Group, ...` as "still on screen". `tear_down` only skips
   top-level `ValueTracker`s; inside a group, `_visible()` falls into the `except` branch
   (ValueTracker has points but no `get_fill_opacity`) and returns True. Suggest: treat
   `ValueTracker` (and point-only non-VMobjects) as invisible in `_family_visible`/`_collect`.
   Growing several arrows with `LaggedStart` is exactly what the epicycle pattern invites.
2. **Off-by-one between `index.txt` and `-n`.** `frames.py` numbers beats from 1
   (`enumerate(files, 1)`), Manim's `-n` counts animations from 0, but SKILL.md and the checklist
   say `-n 0,K` with "K = animation number from index.txt". Following that literally renders one
   animation later (harmless when the next one is a wait, wrong otherwise). Also "beat" in
   `frames.py` means one `play()`/`wait()` call, while "beat" in the storyboard and `review.md`
   means a section of 5 to 10 animations; I had to translate in every review table. Suggest
   "anim N" in `index.txt` plus "use K = N - 1".
3. **Scene pattern 7 (epicycles) is a weak base for "show how more terms sharpen it".**
   (a) `TracedPath` samples once per frame, so the 15 fps preview shows a coarser curve than the
   60 fps final (the preview is not representative), and a traced path cannot be frozen, copied
   into a thumbnail or rewound cleanly for a second pass. Computing the pen path from the terms
   (sum over s in [0, t], about 1000+ samples per loop) avoids all three. (b) The note "show
   5, 11, 21 terms" gives no way to redo the loop; with whole-number speeds the rig is identical
   at t = 0 and t = 1, so rewinding is invisible and new arrows can grow out of the current tip:
   worth one line in the pattern. (c) Shape choice matters and is not mentioned: the heart is
   smooth (terms die out fast, 5/11/21 look alike), and a symmetric star has only every 5th
   coefficient non-zero, so most of its "50 arrows" are invisible. An irregular shape with
   corners (I used a lightning bolt) gives a visible chain of about 13 circles and a clear
   circle -> blob -> rough -> sharp progression.
4. **No check or rule of thumb for text width against the safe area.** LayoutGuard's CLIPPED
   only fires beyond the frame edge (+0.05), not outside the ±6.4 safe area, and nothing in the
   style guide says how wide a caption will be. My first "Fourier's recipe: measure the shape,
   get the arrows" (51 characters at font 40, about 13.8 units) would have sat outside the safe
   area unflagged. Suggest a SAFE warning in LayoutGuard and a rule of thumb (Noto Sans at font
   40 is about 0.27 units per character, so keep captions under about 45 characters).
5. **Caption crossfades and `TransformMatchingTex` produce overlapping text mid-transition.**
   Every captioned video changes captions; `FadeOut(old)` plus `FadeIn(new)` in one `play`
   overlaps both captions at half opacity (visible in every `--mid` frame). A `caption()` helper
   in `templates/scene_silent.py` (old out first, `lag_ratio` about 0.6) would save an iteration.
   Likewise warn that `TransformMatchingTex` only reads well when most parts match; when they do
   not, it crossfades two whole equations on the same spot. Writing the new line under the old
   one is cleaner.
6. **Mixed `Text` + `MathTex` labels and braces under narrow parts.** The cheatsheet says not to
   mix them for the same symbol, but a label like "k turns per loop" has to mix them, and
   `arrange` aligns centres, so baselines differ. A one-line recipe (shift the words so a
   flat-bottomed letter's bottom matches the math glyph's bottom) would help. Braces under
   narrow, adjacent parts (`c_k`, `e^{ikt}`) put their labels on the sum's subscript; a legend
   row under the formula worked better.
7. **Style-guide inconsistency:** the safe area is y within ±3.4, but the guide says
   `to_edge(..., buff=0.5)` is fine, which puts a title's top at 3.5. Use `buff=0.6` (as I did)
   or say the safe margin is 0.5.
8. **Step 6 is unclear about one-frame polish.** After preview 2 the only change was a legend
   baseline nudge in the last frame. I verified it with a 1080p `render.sh still` and went to
   the final rather than spend a third 5-minute preview; the skill does not say whether that
   counts as an iteration or is allowed.
9. **Timing guidance is optimistic for updater-heavy scenes on a shared machine.**
   `environment.md` says a 60 s 2D preview takes 20 to 60 s; this 130 s video with
   `always_redraw` rebuilding up to 50 arrows and circles per frame took 151 s, then 285 s with
   other renders running; the 1080p60 final took 1320 s (22 min), about 4.6 times the second
   preview. Worth saying that scenes rebuilding many mobjects per frame scale with the frame count.
10. Smaller: `check_env.sh` resolves the symlinked skill to the dev repo path, which is fine but
    surprising when `SKILL_DIR` is `~/.agents/skills/...`. Ten contact sheets per preview (160
    tiles with `--mid`) is a lot to look at for a 2-minute video; a `--mid` threshold option or
    one sheet per storyboard section would make the watch step faster.

What helped: `check_env.sh` and `render.sh` worked first time. The OVERLAP warning caught the
formula collision. `--mid` frames caught the thumbnail crossing and the caption overlap, which
qa_check's `cuts` check cannot see. The rubric's "where would a newcomer ask why?" found the one
real leap (where the bolt's arrows come from). The visual-QA checklist's "moving parts never
collide" line prompted the extent simulation that fixed the layout before the first render.
