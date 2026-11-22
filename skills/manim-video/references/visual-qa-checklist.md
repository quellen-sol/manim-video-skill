# Visual QA checklist (Step 4)

Run this after every preview render. Automated help first, then your own eyes.

## 0. Collect the evidence

Commands are for the container route (`R` = `scripts/render-in-container.sh`); host-route
equivalents are in brackets.

1. `out/report.md` [`render.sh` output]: confirm `LayoutGuard: active` [`layout guard active`],
   then read every `LAYOUT` line (`CLIPPED`, `UNSAFE`, `OFFSCREEN`, `OVERLAP`, `CROSSED`, `END`)
   and every `NARRATION` line.
2. The checks in `out/report.md` [`qa_check.py VIDEO [--expect-audio | --expect-silent]`]: every
   FAIL is a bug; every WARN needs either a fix or a one-line explanation in `review.md`.
3. The stills in `out/stills/` [`frames.py VIDEO --anims --mid`]: open every `sheet_NN.png` on
   the first preview; on later previews, the sheets for the changed time window
   (`R JOB_DIR --frames --anims --from S --to S`) plus `R JOB_DIR --frames --count 16` for the
   whole video. Then open full-size stills (`frame_NNN_t*.png`) wherever text is small, objects
   are close, or anything looks odd, and **every label placed near a line** (contact sheets hide
   collisions of a few pixels).
4. Render the 2 or 3 busiest frames at full resolution every iteration: `R JOB_DIR --still K`
   [`render.sh still scene.py Explainer -- -n 0,K`] (K = the `anim K` number in `index.txt`).
5. If a bug might be transient (a flash, a jump), extract frames around it:
   `R JOB_DIR --frames --at 12.0,12.07,12.13,12.2` [`frames.py VIDEO --at ...`].

## 0b. Geometry (mandatory, measured)

Eyeballing a still is not enough for this class of bug: a circle 0.3 units off its axes'
crossing, or axes that reach 1.1 radii on one side and 2 on the other, look "about right" in a
contact sheet. Declare the relations with `GeometryGuard` (`scripts/geometry_qa.py`) and let it
measure them after every animation; `out/report.md` reports them as the `geometry` check.

- [ ] **Concentric** things share a centre: a circle and the crossing of its axes, a ring of
      nodes and its hub, an epicycle and the tip it rides on: `concentric("circle", "x_axis", "y_axis")`.
- [ ] **Axes and number lines are symmetric about their origin** (equal reach both ways), or end
      in an arrowhead or ticks that show why one side is longer: `symmetric("x_axis", about="circle", axis="x")`.
- [ ] The **main figure is centred in its layout region** (the frame, or its half or panel):
      `centered_in("figure", region=(x0, y0, x1, y1))`.
- [ ] **Margins:** the main figure keeps at least 6 to 8% of the frame width/height on every side:
      `within_margin("figure", pct=7)`. Nothing touches the frame edge (a default 2% rule
      checks every object on screen).
- [ ] **Symmetric things look symmetric**: layer stacks, mirrored panels, balanced trees.
- [ ] Every declared rule was checked (no `UNCHECKED` lines) in every layout state the scene
      moves through (re-centre, zoom, panel opens).

A geometry FAIL caps the rubric total at 15 of 20 ([intuition-rubric.md](intuition-rubric.md)).
The per-animation measurements are in `out/geometry.json` (host route:
`media/geometry-<Scene>.json`; `python3 scripts/geometry_qa.py FILE` summarises it).

## 1. Layout

- [ ] Nothing is clipped by the frame edge; nothing important sits outside the safe area
      (x within ±6.5, y within ±3.5).
- [ ] No text overlaps other text; no label sits on top of a line, arrow or shape it does not
      name (check rotated and curved elements, which bounding-box checks miss).
- [ ] No object covers another unintentionally (z-order): labels and highlights are on top
      (`set_z_index`), edges go behind nodes.
- [ ] Moving parts never collide with fixed labels at any point of their path (check `--mid`
      frames and the extremes of a `ValueTracker` sweep).
- [ ] Groups are balanced on screen; no large empty half of the frame while the other is crowded.
- [ ] Zones are respected: titles in the title band, formulas in their panel.

## 2. Text and maths

- [ ] Every text is readable at 1080p (font size 24 or more; check at full size, not in the sheet).
- [ ] LaTeX rendered correctly: no missing symbols, no literal backslashes, no `\frac` shown as
      text, correct sub- and superscripts, matching brackets.
- [ ] Spelling and maths are correct (values in readouts match the picture: sin 30° = 0.50).
- [ ] No sentence-length text where a label would do; at most two lines per text object.
- [ ] `Text` and `MathTex` are not mixed for the same symbol.

## 3. Lifecycle

- [ ] Every object leaves when its beat is over, or is deliberately kept (see the `LAYOUT END`
      line for what remains at the end).
- [ ] No ghost copies after `Transform`/`ReplacementTransform`/`TransformFromCopy`.
- [ ] `always_redraw` and updater-driven objects stop and leave; they do not reappear after a
      `FadeOut`.
- [ ] Nothing pops in or out without an animation, unless it is a deliberate cut (`cuts` lines
      from `qa_check.py`).
- [ ] Text swaps are clean in the `--mid` frames: no two captions or titles overlapping
      mid-fade, no scrambled glyphs from a `Transform` between different strings.

## 4. Motion and timing

- [ ] No flicker: nothing flashes for a frame or two (`cuts` lines close together).
- [ ] No jumps: objects move smoothly from where they were; no snapping to a new position.
- [ ] One focus at a time: the eye is never asked to follow two unrelated motions at once.
- [ ] Each key reveal is followed by a hold of 1 to 2 s; no stall longer than about 6 s with
      nothing moving (silent) unless the viewer is meant to read something.
- [ ] Speed: a sweep the viewer should follow takes 3 s or more; nothing important happens in
      under 0.5 s.
- [ ] Total length matches the storyboard (within about 20 %).

## 5. Colour

- [ ] Colours match the legend everywhere: shape, label and symbol in equations.
- [ ] Enough contrast against the background (no dark blue text on the dark background).
- [ ] Emphasis colour (yellow) is used only for what to look at now.
- [ ] No difference shown by red versus green alone.

## 6. 3D scenes (if any)

- [ ] Labels that must stay readable are fixed in frame (`add_fixed_in_frame_mobjects`).
- [ ] The camera angle shows the shape clearly; nothing important is hidden behind a surface.

## 7. Narration (if any)

- [ ] `qa_check.py --expect-audio` passes; audio level is reasonable and not clipping.
- [ ] `frames.py VIDEO --cues`: each sentence's still (labelled with its text) shows that
      sentence's visual; no visual changes topic mid-sentence.
- [ ] No narration gap longer than about 3 s, except planned pauses.
- [ ] The voice does not read out on-screen text word for word.
- [ ] Pronunciation of symbols and jargon is plausible (write "theta", "sine of theta", "x
      squared" in the narration text, not symbols).

## Logging

Record each finding in `review.md`: beat, time, what is wrong, and the fix. After fixing,
re-render and look at the same beats again; mark each finding fixed only after seeing the new frame.
