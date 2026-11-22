# Troubleshooting

Read the end of the render log first: `render-in-container.sh` prints its last lines on failure,
and the full log is `out/render.log` in the job directory (`out/still.log` for `--still`). On the
host route, `render.sh` prints the last 60 lines and keeps logs under `<project>/media/logs/`.

## LaTeX

| Symptom | Fix |
|---|---|
| `latex: command not found`, `dvisvgm` missing, `LaTeX compilation error` with no TeX installed | Use the container route (the image ships TeX Live), or replace `MathTex`/`Tex` with `Text`/`MarkupText` and Unicode (θ, π, ², √, ≤). |
| `! Undefined control sequence` | A typo or a command from a package that is not loaded. Check backslashes; use raw strings `r"\theta"`. For extra packages: `tex_template = TexTemplate(); tex_template.add_to_preamble(r"\usepackage{mathtools}")`, then `MathTex(..., tex_template=tex_template)`. |
| `! Missing $ inserted` | Maths inside `Tex` (text mode): use `MathTex`, or wrap the maths in `$...$` inside `Tex`. |
| `! Missing { inserted` or a broken split | A `MathTex` part (or a `{{ }}` group) does not form valid LaTeX on its own, e.g. splitting inside `\frac{...}{...}`. Keep each part self-contained. |
| `set_color_by_tex` colours too much or nothing | Isolate the substring first: `{{ }}` or `substrings_to_isolate=[...]`. |
| Odd symbol shapes or missing glyphs | The renderer lacks a LaTeX package; keep to `amsmath`/`amssymb` symbols, or use `Text`. |

## Text, fonts and Pango

- Words render in a serif font: set `Text.set_default(font="Noto Sans")` (in the image) or a font
  that `check_env.sh --fonts` lists for your renderer.
- `Text` shows boxes instead of characters: the font lacks those glyphs; pick a font that has
  them (Noto families cover most scripts).
- Text looks blurry in the preview: the preview is 480p. Judge text at full resolution with
  `render-in-container.sh JOB_DIR --still K` (host route: `render.sh still scene.py Scene -- -n 0,K`).
- `MarkupText` errors: escape `&`, `<`, `>` as `&amp;`, `&lt;`, `&gt;`.

## The host route: installing Manim without Docker (Cairo and Pango)

- `pip install manim` fails building `manimpango` or `pycairo` ("pangocairo >= 1.30.0 is required",
  "cairo not found"): PyPI has no Linux wheels for them, so they compile against system headers.
  They need `libcairo2-dev`, `libpango1.0-dev` and `pkg-config` (Debian/Ubuntu), which need root.
  Do not use sudo: use the container route, or ask an administrator to install those packages;
  then `setup_env.sh --host` builds the venv.
- conda-forge ships prebuilt `manim` (with Cairo and Pango) and works in user space with
  micromamba; this route is documented but untested here (see `environment.md`).

## The render container

| Symptom | Fix |
|---|---|
| `cannot talk to the Docker daemon` / `permission denied ... docker.sock` | The user is not in the `docker` group (needs root to change). Use the host route, or ask an administrator. |
| `bad job.json: ...` (exit 2) | Fix the key it names; the table of keys is in [container.md](container.md). |
| `manim-job: refusing to run as root` | Something ran the image as uid 0. Use `render-in-container.sh`, which runs it as you. |
| `No such file` for an asset or a module | Only the job directory is mounted: keep assets (SVG, PNG, JSON) inside it and refer to them by relative path (`assets/logo.svg`). |
| `out is not writable` | The job directory belongs to another user; render as its owner. |
| `narration: cannot reach the TTS server` | The server must listen where the container can reach it: `127.0.0.1`/`localhost` in job.json become `host.docker.internal` (the Docker host gateway), which only works if the server listens on all interfaces (a Docker port published on `0.0.0.0`). If a host firewall blocks the gateway, run with `MANIM_TTS_NETWORK=host`. |
| `image ... is older than the skill's sources; rebuilding` | Normal after the skill's scripts or Docker files change; the cached rebuild takes seconds. |
| Image build fails | Read the build log it names. The apt step needs `snapshot.ubuntu.com` and the pip step `pypi.org`. |
| `AttributeError: VMobject object has no attribute 'should_render'` | The OpenGL renderer cannot draw a bare `VMobject()`; use `"renderer": "cairo"` (the default). |

## frames.py and qa_check.py

- `frames.py: WARNING ... partial movie files are missing`: Manim deletes partial movies beyond
  `max_files_cached` (default 100). Both routes raise the limit; renders made without it fall
  back to evenly spaced frames. Re-render for per-animation stills.
- `--still K` keeps every still in `out/stills-full/` with a timestamp (host route: `render.sh
  still` under `media/stills/`).
- `qa_check.py` `holds` warnings for stretches where something small is moving: thin strokes and
  small text barely change pixels at 480p. Check the frames at that time; if motion is visible,
  note it as a false positive.
- Stopping a render: Ctrl-C or SIGTERM to `render-in-container.sh` removes its container. Each
  run is its own compose project named `manim-<job>-<time>-<pid>`; if one is still listed by
  `docker ps -a --filter label=com.docker.compose.service=manim` after a crash, report it.

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
| `TypeError: cannot pickle '_thread.lock' object` | An updater is a bound method (`add_updater(self.follow)`); use a lambda or a plain function. |
| Letters scramble during a text change | `Transform` between different strings; fade old out, then new in (scene pattern 11). |
| An object reused after `Uncreate` is invisible | `Uncreate` collapses it to zero size; create a new object. |
| An object comes back after `FadeOut` | It has an updater or is redrawn; clear updaters and `self.remove` it. |
| Two copies after a transform | `Transform(a, b)` keeps `a` on screen (looking like `b`); do not also add `b`. Or use `ReplacementTransform`. |
| `TypeError: ... got multiple values` in `self.play` | Passing a method and arguments (old style). Use `m.animate.method(args)`. |
| A scene renders but nothing moves | Animations were built but not played, or `self.add` was used instead of an animation. |
| `Mobject.__getattr__` / `AttributeError` on `.animate` chains | Only methods returning `self` can chain; split into two animations. |
| Very slow renders | 3D surfaces, thousands of submobjects, or `always_redraw` around `MathTex` that changes text every frame. Lower `Surface` resolution, use `DecimalNumber` with an updater instead of rebuilding `MathTex`, preview only part with `--animations A,B` (host route: `-- -n A,B`). |
| Multiple scenes in one file render in an interactive prompt | Host route: always name the scene class (`render.sh preview scene.py Explainer`); the container always renders job.json's `scene`. |

## Narration

- `ModuleNotFoundError: manim_voiceover`: the renderer lacks it. The image has it; on the host
  route use `setup_env.sh --host`, or the fallback (`"mode": "mux"`, or `narrate_mux.py`).
- `Kokoro TTS request ... failed`: run `check_env.sh --tts`; check `KOKORO_BASE_URL` and the key.
- Audio cut off at the end: add `self.wait(0.5)` after the last `voiceover` block.
- Narration drifts out of step in the fallback path: look for `NARRATION` warnings from
  `Timeline.sync` and shorten the animations of the beat before.
