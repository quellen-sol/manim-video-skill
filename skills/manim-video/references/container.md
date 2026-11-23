# The render container and the job contract

The default way to render is the `manim-video:local` image, run by
`scripts/render-in-container.sh`. Everything the render needs is inside the image: Manim Community
0.22.1, manim-voiceover 0.4.0 with `KokoroService`, LaTeX, ffmpeg, Cairo/Pango with Noto fonts, and
the skill's helpers. The host needs only Docker with the compose plugin. You hand the container a
job directory, and it writes a video, stills and a check report into that directory's `out/`.

The host route (`scripts/render.sh`) is a fallback for local testing; see
[environment.md](environment.md).

## The job directory

```
jobs/<slug>/                 any path you like; one directory per video
├── scene.py                 the Manim scene file (read-only inside the container)
├── job.json                 what to render (below); start from templates/job.json
├── assets/                  optional images, SVGs, data; refer to them as "assets/x.png"
├── narration.json           optional narration script (or put it inline in job.json)
├── storyboard.md, review.md your planning and review notes (the container ignores them)
└── out/                     written by the container; the only writable path
    ├── <Scene>-<quality>.mp4    the video (with audio if narrated)
    ├── report.md, report.json   automated checks: streams, resolution, audio (narrated: AAC as
    │                            long as the video, padded if needed), blank screen,
    │                            stalls, pop-ins/flicker, measured geometry (GeometryGuard),
    │                            plus LayoutGuard and Timeline warnings
    ├── geometry.json            GeometryGuard's measurements: every tracked object's box and
    │                            centre after every animation, and every rule result
    ├── geometry-check.txt/.json from --geometry (the scene runs, no frames are drawn)
    ├── stills/sheet_NN.png      contact sheets to look at; stills/frame_*.png full size;
    │                            stills/index.txt maps tiles to times and beats
    ├── frames/                  extra stills from `--frames` (below)
    ├── stills-full/             full-resolution PNGs from `--still K`, one per call, UTC-stamped;
    │                            kept across renders for before/after comparison
    ├── render.log               the full Manim/ffmpeg log
    ├── summary.json             machine-readable summary (status, paths, timings, GPU)
    └── media/                   Manim's cache (re-renders only redo changed animations)
```

The container sees the job directory at `/job`, read-only, with `/job/out` mounted read-write. The
scene runs with `/job` as its working directory, so relative paths such as `assets/logo.svg`
work. It runs as your uid and gid, so everything in `out/` belongs to you.

## job.json

```json
{
  "scene": "Explainer",
  "quality": "preview",
  "narration": {"enabled": false}
}
```

| Key | Default | Meaning |
|---|---|---|
| `scene` | required | Scene class name in the scene file |
| `file` | `"scene.py"` | scene file name in the job directory |
| `quality` | `"preview"` | `preview` = 854x480 at 15 fps (fast review); `final` = 1920x1080 at 60 fps |
| `fps` | by quality | override the frame rate |
| `resolution` | by quality | override, e.g. `"1280x720"` (even numbers) |
| `renderer` | `"cairo"` | `cairo` (complete, CPU) or `opengl` (see "GPU" below; less complete) |
| `gpu` | `false` | pass the host's `/dev/dri` into the container (opt-in) |
| `encode` | `"manim"` | keep Manim's own H.264 (libx264, CRF 23), or re-encode with `"libx264"` (CRF 20) or `"h264_vaapi"` (needs `gpu`) |
| `narration.enabled` | `false` | narrated video; gives the container network access to the TTS server only |
| `narration.mode` | `"voiceover"` | `voiceover` (manim-voiceover in the scene) or `mux` (fallback: WAV per beat, muxed after rendering) |
| `narration.script` | none | narration text: a file name in the job directory or an inline `{"beats": [{"id", "text"}]}` object; required for `mux` |
| `narration.voice` | `"af_heart"` | Kokoro voice |
| `narration.speed` | `1.0` | speech speed (`mux` mode) |
| `narration.kokoro.base_url` | `http://host.docker.internal:8880/v1` | OpenAI-compatible TTS endpoint; `127.0.0.1`/`localhost` are rewritten to the host |
| `narration.kokoro.model` | `"kokoro"` | TTS model |
| `requirements` | `[]` | extra pip packages, e.g. `["sympy==1.13.3"]`; installed once into `out/.pydeps/` (needs network, so the job gets it) |
| `animations` | all | render only animations A to B, e.g. `"12,20"` (0-based, as in `index.txt`); same as `--animations 12,20` |
| `stills` | `"auto"` | `auto` (one still per animation plus midpoints for preview, 8 even stills for final), `anims` (alias `beats`), `count:N`, `none` |
| `checks` | `{}` | `light_bg` (true for light themes), `min_duration`, `max_duration` (seconds) |
| `cache` | `true` | `false` re-renders every animation (`--disable_caching`): use it when a fix does not show up, because Manim's cache key misses some changes (e.g. swapping one rate function for another). Narrated jobs never use the cache |
| `workers` | `1` | opt-in: render the scene as N contiguous sections in N processes and join them (`--workers N` on the command line). Output is frame-identical to a serial render: each worker replays earlier animations exactly without drawing them, and every seam is checked; it falls back to serial by itself when it cannot be used (manim-voiceover narration, `animations` set, OpenGL renderer, a failed seam check). Measurements and traps: [gpu-and-speed.md](gpu-and-speed.md) |
| `encoders` | `1` | opt-in: Manim's `max_inflight_encoders`, i.e. keep encoding the last animations' partial movies while the next ones are drawn, instead of waiting at the end of each animation. Same frames; see [gpu-and-speed.md](gpu-and-speed.md) |
| `timeout` | `7200` | render time limit in seconds (whole job; parallel workers each get it too) |

Unknown keys are an error (typos fail fast). Keys that start with `_` are comments.

## Running it

```bash
R="$SKILL_DIR/scripts/render-in-container.sh"
"$R" jobs/unit-circle                       # render as job.json says (preview by default)
"$R" jobs/unit-circle --quality final       # the deliverable, without editing job.json
"$R" jobs/unit-circle --frames --at 12.5,31 # extra full-size stills from the last render
"$R" jobs/unit-circle --geometry            # re-measure GeometryGuard rules in seconds (no frames)
"$R" --doctor [--gpu]                       # versions, fonts, LaTeX, EGL and VA-API in the image
"$R" --build                                # build or rebuild the image (about 6 min the first time)
```

On Windows (PowerShell) run `scripts\render-in-container.ps1` with the same arguments; on any OS
`python3 scripts/render_in_container.py` is the same program (the `.sh` and `.ps1` files are thin
shims; Python 3.9+, standard library only). `--check [--tts]` is a quick read-only readiness check
on any OS.

It prints `VIDEO:`, `SHEET:`, `INDEX:`, `REPORT:` and `LOG:` lines with host paths. Exit status:
0 rendered and checks passed (WARNs allowed), 1 rendered but a check FAILed, 2 bad job or usage,
3 Docker or image problem, 4 render failed (the log tail is printed; LaTeX errors are flagged).

The loop: edit `scene.py` (or `job.json`) on the host, run the wrapper again, open `out/report.md`
and the contact sheets, fix, repeat. For a layout fix, `--geometry` checks the rules in seconds
before you spend minutes on a preview.

Long renders: a 1080p60 final of a 2 to 3 minute video takes 4 to 8 minutes of rendering plus
about a minute of checks on an idle 4-core host (the five examples: 4.7 to 8.9 minutes per job);
renders running at the same time slow each other down, so render one at a time. Speed options
(`"workers"`, `"encoders"`, lower frame rates) and their measurements: [gpu-and-speed.md](gpu-and-speed.md).
If your tool calls time out sooner, run the wrapper in the background
(`"$R" JOB_DIR --quality final > JOB_DIR/out-wrapper.log 2>&1 &`) and poll `out/summary.json`:
its `status` is `running` until the job ends, then `ok`, `checks_failed` or `failed`. Ctrl-C or
SIGTERM to the wrapper stops the render and removes its container.

Each run replaces the previous video, report and stills (copy a video elsewhere to keep it).
Manim's cache in `out/media/` makes re-renders redo only the animations it sees as changed; if a
fix does not show up, set `"cache": false` for one render. `--still K` renders the current
`scene.py`, so after editing the scene, take K from a fresh render's `index.txt`.

If the image is missing, the wrapper builds it. If the skill's scripts or Docker files changed
since the image was built (it compares a hash stored in an image label), it rebuilds; with the
build cache that takes seconds. `--no-build` skips both and warns instead.

## Narration in the container

Set `"narration": {"enabled": true, ...}` in job.json. Then:

- The container gets network access (silent jobs get none) and the host's Kokoro server at
  `host.docker.internal:8880`, mapped to the Docker host gateway.
- The wrapper passes `KOKORO_API_KEY` by name from your environment. If it is unset, it reads
  only that line from `KOKORO_ENV_FILE` (default `~/.config/agent-stack/gateway.env`, if
  readable). The key is never in the image, the repo, the job directory, the command line or
  the logs. Silent jobs never receive it.
- `voiceover` mode: the scene uses `VoiceoverScene` and `KokoroService` (see
  `templates/scene_narrated.py`). Keep the words in job.json and read them with
  `from narration_script import line`, then `with self.voiceover(text=line("intro")) as tracker:`.
- `mux` mode: the container synthesizes one WAV per beat first (`narrate_mux.py tts`) and sets
  `NARRATION_TIMELINE` for the scene, renders, then muxes the clips onto the video. In the scene:
  `TL = Timeline(os.environ.get("NARRATION_TIMELINE", "audio/timeline.json"))`.
- If the host-gateway route is blocked (for example by a host firewall), run with
  `MANIM_TTS_NETWORK=host` to give narrated jobs the host's network instead.

## GPU (opt-in)

This host (the nucbox) has no NVIDIA GPU. It has an Intel Alder Lake-N iGPU (`/dev/dri/card0`,
group `video`; `/dev/dri/renderD128`, group `render`) and 4 CPU cores. With `"gpu": true` (or
`--gpu`), the wrapper adds `docker/compose.gpu.yml`, which passes `/dev/dri` and joins the `video`
and `render` groups. It resolves their ids at run time with `getent group video render`, falling
back to the device files' groups. There is no `--privileged`, no other device and no extra
capability. Without a render node on the host, the job runs on the CPU with a warning.

What the GPU can and cannot do here (measured on the nucbox; full numbers below):

- **Cairo renderer (the default): CPU only; the GPU changes nothing.** Same render time with
  and without `/dev/dri`.
- **OpenGL renderer (`"renderer": "opengl"`): works headless via EGL, on the iGPU (Mesa iris) or
  on the CPU (llvmpipe), but on this hardware it is slower than Cairo either way, and the iGPU
  is no faster than llvmpipe.** The bottleneck is CPU-side work (Python, updaters, tessellation,
  frame readback and encoding), not rasterising. It is also less complete: a bare `VMobject()`
  crashes it (use `TracedPath`, `always_redraw` shapes or concrete classes), and strokes and
  LaTeX render slightly differently (SSIM 0.991 against Cairo, with heavier formula strokes).
- **VA-API H.264 encode works from the container** (Intel iHD driver 24.1, low-power VDEnc
  entrypoint `EncSliceLP`): 2.4x faster than libx264, but only as a post-render re-encode,
  because the PyAV build inside Manim has no VA-API encoder (`[video_encoder] codec =
  h264_vaapi` fails with "Unknown video encoder"). Manim always encodes once itself, so a
  re-encode is extra time, and at equal quality (SSIM 0.9996) the VA-API file is 4 to 5 times
  larger. So `"encode": "manim"` (no re-encode) stays the default.
- Other GPUs: AMD on Linux uses the same `--gpu` (Mesa radeonsi through `/dev/dri`); NVIDIA on
  Linux uses `--nvidia` (`docker/compose.nvidia.yml`, NVIDIA Container Toolkit). Both UNTESTED;
  Docker Desktop on macOS and Windows gives Linux containers no GPU for this use. Recipes, the
  OpenGL renderer's limits and hardware encoders per platform: [gpu-and-speed.md](gpu-and-speed.md).
- Defaults chosen from these numbers: `renderer: cairo`, `gpu: false`, `encode: manim`. The GPU
  stays opt-in for experiments and for heavier OpenGL/3D work on other hardware, where it might
  pay off; it was not measured to help here.

Benchmark (`tests/bench_gpu.sh`, run on the quiet nucbox, Intel N150 4 cores, 2026-11-22;
scene `tests/jobs/bench/scene.py`: 24 rotating vectors with circles, a traced path, a redrawn
sine wave and a `MathTex` formula, 10 s; every render starts from an empty cache; 2 runs each,
median and both runs):

| Configuration | OpenGL device | Frames | Render s | Frames/s |
|---|---|---|---|---|
| Cairo, preview 854x480 @ 15, CPU | - | 150 | 6.7 (6.9 / 6.6) | 22.3 |
| Cairo, final 1080p60, CPU | - | 600 | 24.4 (24.3 / 24.6) | 24.5 |
| Cairo, final 1080p60, GPU passed in | - | 600 | 24.4 (24.5 / 24.2) | 24.6 |
| OpenGL, final 1080p60, EGL on the CPU | llvmpipe (LLVM 20.1.2) | 600 | 34.3 (34.5 / 34.1) | 17.5 |
| OpenGL, final 1080p60, EGL on the iGPU | Mesa Intel Graphics (ADL-N) | 600 | 35.3 (35.1 / 35.5) | 17.0 |

Post-render H.264 encode of the 1080p60 Cairo render (600 frames):

| Encoder | Settings | Encode s | Size MB | SSIM vs Manim's file |
|---|---|---|---|---|
| (Manim's own output, made during the render) | libx264 CRF 23 | - | 0.48 | 1 |
| libx264, CPU | CRF 20, preset medium | 6.8 (6.6 / 6.9) | 0.55 | 0.9996 |
| h264_vaapi, iGPU | QP 20, low-power VDEnc | 2.8 (2.8 / 2.8) | 2.40 | 0.9996 |
| libx264, CPU, standalone | CRF 23, preset medium (Manim's settings) | 7.8 | 0.43 | - |

Parity: the host route (same lock file, host libraries) against the container, Cairo final:
SSIM 0.999, 25.1 s against 24.4 s.

Re-run on another machine with `tests/bench_gpu.sh` (needs a quiet host; about 6 minutes).

## Compose files and the security settings

`docker/compose.yml` defines the `manim` service; `docker/compose.gpu.yml` is the GPU override
(`/dev/dri`), `docker/compose.nvidia.yml` the untested NVIDIA one.
The style follows the host's media-stack compose file (TZ/UMASK environment, bind mounts, GPU via
`devices` + `group_add`), but this is a run-to-completion job rather than a daemon:

- `docker compose run --rm`, one compose project per job (`manim-<job>-<time>-<pid>`), and a
  cleanup trap that removes the container on exit, error, Ctrl-C or SIGTERM;
- no restart policy, no published ports, no `container_name`;
- `network_mode` (`none` for silent jobs, `bridge` for narration or extra requirements), so
  compose creates no project network to leave behind;
- runs as the caller's uid:gid; the image's entrypoint refuses uid 0 or gid 0;
- read-only root filesystem with a tmpfs `/tmp`, `cap_drop: ALL`, `no-new-privileges`, and an
  init process that forwards signals.

Manual equivalent of a CPU render:

```bash
cd "$SKILL_DIR"
JOB_DIR=/abs/path/to/job HOST_UID=$(id -u) HOST_GID=$(id -g) \
  docker compose -p manim-myjob -f docker/compose.yml run --rm -T manim
# GPU: add  -f docker/compose.gpu.yml  with VIDEO_GID and RENDER_GID exported
```

## The image

`docker/Dockerfile`, build context = the skill directory (`.dockerignore` sends only the Docker
files and `scripts/*.py`). Ubuntu 24.04 pinned by digest; apt pinned to one dated snapshot of the
Ubuntu archive; Python packages pinned with hashes in `docker/requirements.lock` (regenerate with
`uv pip compile docker/requirements.in --python-version 3.12 --python-platform x86_64-manylinux_2_39 --generate-hashes`).
The software is identical across builds; layer bytes are not (file timestamps differ). The
installed versions are listed inside the image at `/opt/manim-video/apt-packages.txt` and
`/opt/manim-video/python-packages.txt`.

Size and build time on the nucbox: **1.72 GB**: Ubuntu base 78 MB; one apt layer of 1.15 GB
(TeX Live about 470 MB, ffmpeg and its codecs, Mesa, Noto fonts 63 MB, Python); the Python venv
488 MB (Manim, SciPy, NumPy, PyAV with its own ffmpeg, skia-pathops, moderngl); the skill's
helpers under 0.1 MB. First build from a cold cache: 6 min 8 s (mostly downloads). Later
builds that change only the helpers take seconds.

## Host ffmpeg on the nucbox (resolved discrepancy)

The first version of this skill said the system ffmpeg was broken (`liblapack.so.3` missing).
That was true only for about two minutes: the owner's `apt` install was in progress. `dpkg.log`
shows `liblapack3` unpacked at 19:55:32 and configured at 19:57:58 on 2026-11-21 (configuring
creates the `liblapack.so.3` alternatives link), and the failing check ran at about 19:57.
Re-tested 2026-11-22 with a real encode: `/usr/bin/ffmpeg` 6.1.1 encodes libx264 + AAC, `ffprobe`
reads it back, and the `blackdetect`, `freezedetect` and `volumedetect` filters the checks use
all run. The host route now uses the system ffmpeg when it works, keeping the static build in
`~/.local/share/manim-video/bin` only as a fallback, and `check_env.sh --host` runs that encode
test. The container route never used the host ffmpeg: the image has its own ffmpeg 6.1.1.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `cannot talk to the Docker daemon` | the user must be in the `docker` group (needs an administrator); otherwise use the host route |
| `bad job.json: unknown key(s)` | a typo; see the table above |
| `narration: cannot reach the TTS server` | is Kokoro running (`curl 127.0.0.1:8880/v1/models` on the host)? Try `MANIM_TTS_NETWORK=host` |
| `AttributeError: VMobject object has no attribute 'should_render'` | the OpenGL renderer cannot draw a bare `VMobject()`; use `renderer: cairo`, or `TracedPath`/`always_redraw` shapes |
| `out is not writable` | the job directory belongs to another user; render as its owner |
| render fails with a LaTeX error | see [troubleshooting.md](troubleshooting.md); the full log is `out/render.log` |
