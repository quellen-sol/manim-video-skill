# Visual QA checklist (Step 4)

Run this after every preview render. Automated help first, then your own eyes.

## 0. Collect the evidence

1. `render.sh` output: read every `LAYOUT` line (from `LayoutGuard`) and every `NARRATION` line.
2. `qa_check.py VIDEO [--expect-audio | --expect-silent]`: every FAIL is a bug; every WARN needs
   either a fix or a one-line explanation in `review.md`.
3. `frames.py VIDEO --beats --mid`: open **every** `sheet_NN.png`. Then open full-size stills
   (`frame_NNN_t*.png`) wherever text is small, objects are close, or anything looks odd.
   For text that is small in the 480p preview, render the frame at full resolution:
   `render.sh still scene.py Explainer -- -n 0,K` (K = animation number from `index.txt`).
4. If a bug might be transient (a flash, a jump), extract frames around it:
   `frames.py VIDEO --at 12.0,12.07,12.13,12.2`.

## 1. Layout

- [ ] Nothing is clipped by the frame edge; nothing important sits outside the safe area
      (x within ±6.4, y within ±3.4).
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
- [ ] Each sentence plays while its visual is on screen; no visual changes topic mid-sentence.
- [ ] No narration gap longer than about 3 s, except planned pauses.
- [ ] The voice does not read out on-screen text word for word.
- [ ] Pronunciation of symbols and jargon is plausible (write "theta", "sine of theta", "x
      squared" in the narration text, not symbols).

## Logging

Record each finding in `review.md`: beat, time, what is wrong, and the fix. After fixing,
re-render and look at the same beats again; mark each finding fixed only after seeing the new frame.
