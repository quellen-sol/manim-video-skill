# Style guide

A calm, dark, 3Blue1Brown-like look. Consistency matters more than any single choice: decide
once in the storyboard, then use the same colours, sizes and positions everywhere.

## Canvas and safe area

- 16:9, 1920x1080 final (`-qh`, 60 fps). The scene frame is 14.22 x 8 units, centred at the
  origin: x runs from -7.11 to 7.11, y from -4 to 4.
- **Safe area:** keep every object inside x within ±6.5 and y within ±3.5 (margins of about
  0.6 and 0.5 units, 70 to 80 px at 1080p). `to_edge(..., buff=0.5)` or more lands exactly on it;
  never `buff=0` at the frame edge. `LayoutGuard` reports text outside it as `UNSAFE`.
- **Zones** (adapt per video, but keep them fixed within one video):

  | Zone | y range | Holds |
  |---|---|---|
  | Title band | 2.8 to 3.5 | the beat's short title, if any |
  | Main stage | -2.6 to 2.5 | the diagram |
  | Footer band | -3.5 to -2.8 | a caption or a formula that summarises the beat |

  A side panel (x from 2.5 to 6.5) works well for formulas and readouts next to a diagram on the
  left. Do not let the diagram's moving parts cross into the panel.

## Colour

Background `#0F1117` (near-black, slightly blue; set `config.background_color`).

| Role | Colour | Hex |
|---|---|---|
| Primary concept | `BLUE` | `#58C4DD` |
| Second concept / contrast | `ORANGE` or `RED` | `#FF862F` / `#FC6255` |
| Emphasis, the thing to watch now | `YELLOW` | `#F7D96F` |
| Result, success, "correct" | `GREEN` | `#83C167` |
| Error, conflict, "wrong" | `RED` | `#FC6255` |
| Extra concepts | `TEAL`, `PURPLE`, `GOLD`, `PINK` | `#5CD0B3`, `#9A72AC`, `#F0AC5F`, `#D147BD` |
| Body text | `WHITE` | |
| Secondary text, axes, scaffolding | `GREY_B` | `#BBBBBB` |
| De-emphasised, ghosted | `DARK_GREY` or any colour at opacity 0.25 | `#444444` |

Rules:

- **One colour per concept** for the whole video, applied to the shape, its label and its symbol
  inside equations (`set_color_by_tex`). Write the legend in the storyboard first.
- At most 4 or 5 concept colours on screen at once; everything else is white or grey. When the
  subject truly has more (six trig functions), pair related concepts in related shades.
- **Coloured text and thin strokes need light tints.** `PURPLE`, `MAROON`, `BLUE_E`, `TEAL_E`,
  `DARK_GREY` and any `_D`/`_E` shade are unreadable as text on the dark background; for text use
  the main colour if it is light (`BLUE`, `YELLOW`, `GREEN`, `ORANGE`) or the `_A`/`_B` tint
  (`PURPLE_A`, `MAROON_A`, `TEAL_A`), and check at full resolution.
- Do not encode a difference with red versus green alone (colour-blind viewers); pair colour with
  position, shape or a label. Blue versus orange is the safest binary pair.
- Yellow is reserved for "look here now"; do not give it a permanent meaning as well, unless
  the legend says so.
- Fills: use `fill_opacity` 0.15 to 0.3 for boxes and regions so strokes and text stay readable.

## Fonts and text

- `Text.set_default(font="Noto Sans")` at the top of the file (the Docker image's default font
  is a serif). Monospace for code: `Noto Mono`. Check the fonts available to your renderer
  with `fc-list : family` if you change them; a missing font silently falls back.
- Maths in `MathTex` (LaTeX Computer Modern). Do not mix `Text` and `MathTex` for the same
  symbol; write θ either always in `MathTex` or always as a `Text` character.
- Sizes (`font_size`, at 1080p): title 44 to 48, main labels 32 to 36, secondary labels 26 to
  30, never below 24. Equations 44 to 56. `MathTex` renders smaller than `Text` at the same
  `font_size`: give maths about 4 points more than the words beside it. A label must stay readable when the video is watched
  on a phone: if in doubt, larger.
- At most two lines in one text object, about 6 words per label, and at most about 12 words on
  screen at once (narrated videos: fewer). A caption at size 30 fits about 45 characters in the
  12-unit safe width; check `width` and `scale_to_fit_width(12)` if longer.
- **Captions change by swapping, not crossfading:** fade the old one out (0.3 s), then the new one
  in (0.3 s). Two captions fading at once overlap visibly mid-transition (pattern 11).
- Labels sit next to what they name (`next_to(..., buff=0.2 to 0.3)`), on the side facing away
  from other content. Leader lines only when the label cannot fit beside its object.

## Lines, shapes, motion

- Stroke widths: scaffolding (axes, grids) 1 to 2; ordinary shapes 3 to 4 (default 4); the key
  object of a beat 6.
- Arrows: `Arrow(start, end, buff=0.1)` so arrowheads do not hide inside boxes; keep
  `max_tip_length_to_length_ratio` default.
- **Highlighting:** a segment gets a flash along it (`ShowPassingFlash` of a thick yellow copy);
  a formula or region gets a `SurroundingRectangle` that is created, held for a second, then
  faded. Avoid `Indicate` on lines (it stretches them) and `Circumscribe` on formulas (it reads
  as a stray overline in stills).
- Moving labels (branch tags, pointers) travel along arcs (`.animate(path_arc=...)`) or move
  before new edges are drawn, so they never slide across other labels.
- Animation `run_time`: 0.5 to 1 s for small changes, 1 to 2 s for main reveals, 3 to 6 s for
  a slow sweep the viewer should watch. Default rate function `smooth`; `linear` for constant
  motion such as rotation or tracing.
- Hold 1 to 2 s after each key reveal (`self.wait`), 2 to 3 s on the final recap.
- Transitions between chapters: fade everything out (`FadeOut(*self.mobjects)`), then a short
  chapter card or the next diagram. No hard cuts.
- Introduce at most 2 or 3 new elements per animation; group the rest with `LaggedStart`.

## Length

- One idea in 20 to 40 s; a typical explainer is 60 to 150 s; longer only when asked.
- Narrated videos: the narration sets the pace (about 2.5 words per second); leave 0.5 to 1 s
  of silence between beats.
