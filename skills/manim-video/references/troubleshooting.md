# Troubleshooting

Read the end of the render log first: `render.sh` prints its last 60 lines on failure, and the
full log is under `<project>/media/logs/`.

## LaTeX

| Symptom | Fix |
|---|---|
| `latex: command not found`, `dvisvgm` missing, `LaTeX compilation error` with no TeX installed | Use the Docker backend (it ships TeX Live), or replace `MathTex`/`Tex` with `Text`/`MarkupText` and Unicode (θ, π, ², √, ≤). |
| `! Undefined control sequence` | A typo or a command from a package that is not loaded. Check backslashes; use raw strings `r"\theta"`. For extra packages: `tex_template = TexTemplate(); tex_template.add_to_preamble(r"\usepackage{mathtools}")`, then `MathTex(..., tex_template=tex_template)`. |
| `! Missing $ inserted` | Maths inside `Tex` (text mode): use `MathTex`, or wrap the maths in `$...$` inside `Tex`. |
| `! Missing { inserted` or a broken split | A `MathTex` part (or a `{{ }}` group) does not form valid LaTeX on its own, e.g. splitting inside `\frac{...}{...}`. Keep each part self-contained. |
| `set_color_by_tex` colours too much or nothing | Isolate the substring first: `{{ }}` or `substrings_to_isolate=[...]`. |
| Odd symbol shapes or missing glyphs | The renderer lacks a LaTeX package; keep to `amsmath`/`amssymb` symbols, or use `Text`. |

## Text, fonts and Pango

- Words render in a serif font: set `Text.set_default(font="Noto Sans")` (Docker image) or a font
  that `fc-list : family` shows in your renderer.
- `Text` shows boxes instead of characters: the font lacks those glyphs; pick a font that has
  them (Noto families cover most scripts).
- Text looks blurry in the preview: the preview is 480p. Judge text at full resolution with
  `render.sh still scene.py Scene -- -n 0,K`.
- `MarkupText` errors: escape `&`, `<`, `>` as `&amp;`, `&lt;`, `&gt;`.

## Installing Manim without Docker (Cairo and Pango)

- `pip install manim` fails building `manimpango` or `pycairo` ("pangocairo >= 1.30.0 is required",
  "cairo not found"): PyPI has no Linux wheels for them, so they compile against system headers.
  They need `libcairo2-dev`, `libpango1.0-dev` and `pkg-config` (Debian/Ubuntu), which need root.
  Do not use sudo: use the Docker backend, or ask an administrator to install those packages.
- conda-forge ships prebuilt `manim` (with Cairo and Pango) and works in user space with
  micromamba; this route is documented but untested here (see `environment.md`).

## Docker

| Symptom | Fix |
|---|---|
| `permission denied ... docker.sock` | The user is not in the `docker` group (needs root to change). Use a local install instead, or ask an administrator. |
| Output files owned by root | Always render through `render.sh`; it runs the container as your uid. |
| `No such file` for an asset or a module | Only the scene's directory is mounted: keep assets (SVG, PNG, JSON) inside the project directory and refer to them by relative path. |
| Narration: connection refused to the TTS server | The server must listen on an address the container can reach. `render.sh` maps `127.0.0.1`/`localhost` to `host.docker.internal`, which only works if the server listens on all interfaces (Docker port published on `0.0.0.0`). Otherwise set `KOKORO_BASE_URL` to an address reachable from the container. |
| Image not found | `scripts/setup_env.sh` pulls `manimcommunity/manim:v0.22.1` and builds `manim-video:0.22.1`. |

## ffmpeg and ffprobe

- `frames.py`/`qa_check.py` say no working ffmpeg: a system ffmpeg can be installed but broken
  (for example `error while loading shared libraries`). `scripts/setup_env.sh` installs a static
  build into `~/.local/share/manim-video/bin`, which the scripts prefer.
- Manim itself does not need the ffmpeg command (it encodes with PyAV).

## Manim runtime errors

| Symptom | Fix |
|---|---|
| `NameError: ShowCreation` (or `TexText`, `CONFIG`...) | ManimGL idiom; see the table in `api-cheatsheet.md`. |
| `ValueError: zip() argument 2 is shorter than argument 1` | An `always_redraw`/updater object was animated (FadeOut, Transform). Call `m.clear_updaters()` first. |
| An object comes back after `FadeOut` | It has an updater or is redrawn; clear updaters and `self.remove` it. |
| Two copies after a transform | `Transform(a, b)` keeps `a` on screen (looking like `b`); do not also add `b`. Or use `ReplacementTransform`. |
| `TypeError: ... got multiple values` in `self.play` | Passing a method and arguments (old style). Use `m.animate.method(args)`. |
| A scene renders but nothing moves | Animations were built but not played, or `self.add` was used instead of an animation. |
| `Mobject.__getattr__` / `AttributeError` on `.animate` chains | Only methods returning `self` can chain; split into two animations. |
| Very slow renders | 3D surfaces, thousands of submobjects, or `always_redraw` around `MathTex` that changes text every frame. Lower `Surface` resolution, use `DecimalNumber` with an updater instead of rebuilding `MathTex`, preview only part with `-- -n A,B`. |
| Multiple scenes in one file render in an interactive prompt | Always name the scene class: `render.sh preview scene.py Explainer`. |

## Narration

- `ModuleNotFoundError: manim_voiceover`: the renderer lacks it. Use the derived Docker image
  (`setup_env.sh`), or the fallback `narrate_mux.py`.
- `Kokoro TTS request ... failed`: run `check_env.sh --tts`; check `KOKORO_BASE_URL` and the key.
- Audio cut off at the end: add `self.wait(0.5)` after the last `voiceover` block.
- Narration drifts out of step in the fallback path: look for `NARRATION` warnings from
  `Timeline.sync` and shorten the animations of the beat before.
