# Environment and render recipe

## What works (verified)

Tested on Ubuntu 24.04 (x86_64, 4 cores, no GPU), as an ordinary user with no root, in the
`docker` group:

| Piece | Where | Notes |
|---|---|---|
| Manim Community 0.22.1, TeX Live, Python 3.14 | Docker image `manimcommunity/manim:v0.22.1` | official image, about 1.4 GB on disk |
| manim-voiceover 0.4.0, ffmpeg, sox | derived image `manim-video:0.22.1` | built from `scripts/docker/Dockerfile` by `setup_env.sh` |
| ffmpeg, ffprobe (host) | `~/.local/share/manim-video/bin` | static build, used by `frames.py`, `qa_check.py`, `narrate_mux.py` |
| Python 3.11+ (host) | system `python3` | helper scripts use the standard library only |
| Kokoro TTS | any OpenAI-compatible `/v1/audio/speech` server | default `http://127.0.0.1:8880/v1` |

Setup, once per machine: `scripts/setup_env.sh`, then `scripts/check_env.sh --tts`.

## How rendering runs

`render.sh MODE scene.py Scene` runs, in effect:

```bash
docker run --rm --user "$(id -u):$(id -g)" -e HOME=/tmp \
  -v "<project dir>:/manim" -v "<skill>/scripts:/skill/scripts:ro" -e PYTHONPATH=/skill/scripts \
  --network none \
  manim-video:0.22.1 manim -ql --progress_bar none scene.py Scene
```

- `--network none` for silent scenes. For narrated scenes (the file uses `VoiceoverScene` or
  `KokoroService`) it instead adds `--add-host=host.docker.internal:host-gateway`, rewrites a
  `127.0.0.1`/`localhost` `KOKORO_BASE_URL` to `host.docker.internal`, and forwards
  `KOKORO_*` variables by name (the key's value never appears on a command line).
- Each render is a fresh `--rm` container; nothing keeps running afterwards.
- Output lands in `<project>/media/videos/<file stem>/<quality>/<Scene>.mp4`, owned by you.
- Quality: `preview` = `-ql` (854x480, 15 fps), `final` = `-qh` (1920x1080, 60 fps), `still` =
  `-qh -s` (PNG of the last frame). Override with `PREVIEW_QUALITY=m` or `FINAL_QUALITY=k`.
- Typical times on 4 CPU cores: a 60 s 2D preview in 20 to 60 s; the 1080p60 final 5 to 15
  times longer (2 to 2.5 minute explainers took 9 to 22 minutes while other renders shared the
  machine). Scenes that rebuild many objects every frame (`always_redraw` around groups,
  epicycles), 3D, and thousands of objects are much slower. A narrated scene's first preview also
  waits for TTS of every sentence (minutes on a CPU Kokoro); later renders reuse the clips.
- `render.sh` also writes `media/manim-video.cfg` (the project's `manim.cfg`, if any, plus
  `max_files_cached = 100000`, so per-animation stills stay correct) and passes it with
  `--config_file`, and adds `--disable_caching` for narrated scenes.

## Choosing a backend

`MANIM_BACKEND=auto` (default) uses a local `manim` if one is installed and reports
"Manim Community", else Docker. Force with `MANIM_BACKEND=docker` or `MANIM_BACKEND=local`.

### Local install (optional)

A local install renders without containers but needs system libraries:

- **pip/uv:** `uv venv && uv pip install "manim==0.22.1" "manim-voiceover==0.4.0"` needs
  `libcairo2-dev`, `libpango1.0-dev` and `pkg-config` (root to install), because `manimpango`
  and `pycairo` have no Linux wheels. LaTeX (for `MathTex`) is separate: TeX Live or TinyTeX
  plus `dvisvgm` and the packages `standalone preview doublestroke relsize fundus-calligra
  wasysym physics dvisvgm rsfs wasy cm-super jknapltx mathastext microtype ms setspace`.
- **conda-forge (user space, untested here):** `micromamba create -p ~/.local/share/manim-video/env
  -c conda-forge python=3.12 manim=0.22.1`, then `pip install manim-voiceover==0.4.0` inside it,
  and put its `bin` on `PATH`. Add LaTeX as above if needed.

Without LaTeX, write maths with `Text` and Unicode; `check_env.sh` warns when LaTeX is missing.

## Environment variables

| Variable | Default | Used by |
|---|---|---|
| `MANIM_BACKEND` | `auto` | `render.sh`, `check_env.sh` |
| `MANIM_IMAGE` | `manim-video:0.22.1` | Docker image to run |
| `MANIM_BASE_IMAGE` | `manimcommunity/manim:v0.22.1` | base image (silent renders only) |
| `MANIM_VIDEO_HOME` | `~/.local/share/manim-video` | static ffmpeg location |
| `PREVIEW_QUALITY`, `FINAL_QUALITY` | `l`, `h` | render qualities |
| `MANIM_NETWORK` | `auto` | `none` or `tts` to override detection |
| `FFMPEG`, `FFPROBE` | unset | explicit binary paths for the helpers |
| `KOKORO_BASE_URL`, `KOKORO_MODEL`, `KOKORO_VOICE`, `KOKORO_API_KEY` | see `narration.md` | narration |
