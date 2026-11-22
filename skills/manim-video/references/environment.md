# Environment: the two render routes

| | Container route (default) | Host route (fallback) |
|---|---|---|
| Entry point | `scripts/render-in-container.sh JOB_DIR` | `scripts/render.sh preview\|final\|still scene.py Scene` |
| Host needs | Docker + compose plugin, docker group | Manim Community 0.22.1, LaTeX, dvisvgm, ffmpeg, Python 3.11+ |
| Toolchain | pinned in the `manim-video:local` image | whatever the host has |
| Checks and stills | run for you, in `out/` | run `qa_check.py` and `frames.py` yourself |
| Use it for | every render | local testing, comparing against the container, no-Docker machines |
| Details | [container.md](container.md) | below |

Set up: `scripts/setup_env.sh` (container route), `scripts/setup_env.sh --host` (host route).
Check: `scripts/check_env.sh` (add `--host`, `--gpu`, `--tts`, `--fonts`).

## Verified on the nucbox (Ubuntu 24.04, Intel N150, 4 cores, Intel iGPU, no root)

| Piece | Container route | Host route |
|---|---|---|
| Manim Community 0.22.1 + manim-voiceover 0.4.0 | in the image, from `docker/requirements.lock` | venv `~/.local/share/manim-video/venv`, same lock file |
| Python | 3.12.3 | system 3.12.3 |
| TeX Live 2023, dvisvgm 3.2.1 | in the image | system packages (installed by the owner) |
| ffmpeg 6.1.1 | in the image | system package (works; see container.md); a static build in `~/.local/share/manim-video/bin` is only a fallback |
| Cairo 1.18, Pango 1.52 | in the image | system `libcairo2-dev`, `libpango1.0-dev` |
| Kokoro TTS | `host.docker.internal:8880` | `127.0.0.1:8880` |

The same scene rendered by both routes gives near-identical video (SSIM 0.99, see
[container.md](container.md)); both use the same Python packages and the same Ubuntu library
versions.

## The host route

`render.sh MODE scene.py Scene` runs, in effect,
`cd <scene dir> && PYTHONPATH=<skill>/scripts manim -ql --config_file media/manim-video.cfg scene.py Scene`
with the venv's `manim` (or `manim` on `PATH`):

- Output lands in `<scene dir>/media/videos/<file stem>/<quality>/<Scene>.mp4`; the log in
  `media/logs/`. It prints `VIDEO:`/`IMAGE:` lines, whether the layout guard ran and its warnings.
- Quality: `preview` = `-ql` (854x480, 15 fps), `final` = `-qh` (1920x1080, 60 fps), `still` =
  `-qh -s` (PNG of the last frame; add `-- -n 0,K` for the frame after animation K). Override
  with `PREVIEW_QUALITY=m` or `FINAL_QUALITY=k`.
- `media/manim-video.cfg` is the project's `manim.cfg` (if any) plus `max_files_cached = 100000`,
  so per-animation stills stay correct; narrated scenes also get `--disable_caching`.
- It refuses ManimGL idioms, like the container.
- Then check and look: `python3 scripts/qa_check.py <video> [--expect-audio | --expect-silent]`
  and `python3 scripts/frames.py <video> --anims --mid` (or `--count`, `--at`, `--cues`).
- Narration: the scene calls Kokoro at `KOKORO_BASE_URL` (default `http://127.0.0.1:8880/v1`)
  directly. `KOKORO_API_KEY` comes from your environment only.

### Installing the host route

`setup_env.sh --host` checks for the system packages it needs and stops with a list if any are
missing (it never uses sudo): `python3-venv`, `python3-dev`, `libcairo2-dev`, `libpango1.0-dev`,
`pkg-config`, a C compiler, `texlive-latex-extra`, `texlive-fonts-recommended`,
`texlive-science`, `tipa`, `dvisvgm` (and `fonts-noto-core` for the style guide's font). Then it
creates the venv from `docker/requirements.lock` (hash-checked; `manimpango` and `pycairo` are
compiled against the Cairo/Pango headers), and fetches a static ffmpeg only if the system one
is missing or broken. Without LaTeX, write maths with `Text` and Unicode.

## Typical render times (container, 4 cores)

A 10 s benchmark scene: preview 7 s, 1080p60 final 24 s (24 frames/s). Explainers of 2 to 2.5
minutes: previews in 1 to 3 minutes, finals 9 to 22 minutes when other renders shared the
machine. Scenes that rebuild many objects every frame (`always_redraw` around groups,
epicycles), 3D, and thousands of objects are much slower. A narrated scene's first preview also
waits for TTS of every sentence (minutes on a CPU Kokoro); later renders reuse the clips.

## Environment variables

| Variable | Default | Used by |
|---|---|---|
| `MANIM_IMAGE` | `manim-video:local` | container route: image tag |
| `MANIM_TTS_NETWORK` | `bridge` | container route: `host` if the host-gateway route to the TTS server is blocked |
| `KOKORO_ENV_FILE` | `~/.config/agent-stack/gateway.env` | container route: where to read `KOKORO_API_KEY` if it is not set |
| `MANIM_VIDEO_HOME` | `~/.local/share/manim-video` | host route: static ffmpeg (`bin/`) and the venv |
| `MANIM_HOST_VENV` | `$MANIM_VIDEO_HOME/venv` | host route: Manim venv |
| `PREVIEW_QUALITY`, `FINAL_QUALITY` | `l`, `h` | host route: render qualities |
| `FFMPEG`, `FFPROBE` | unset | host route: explicit binary paths for the helpers |
| `KOKORO_BASE_URL`, `KOKORO_MODEL`, `KOKORO_VOICE`, `KOKORO_API_KEY` | see [narration.md](narration.md) | narration (job.json wins in the container) |
