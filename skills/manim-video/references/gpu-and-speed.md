# GPU acceleration and render speed

Read this when a final render is too slow, or before turning on any GPU option. The defaults do
not change: **1080p60, Cairo renderer, GPU off, serial render** (`"workers": 1`, `"encoders": 1`).
Every speed option below is opt-in in `job.json`.

"Measured" means measured on the nucbox: Intel N150 (4 cores, no hyper-threading), 16 GB RAM,
Intel Alder Lake-N iGPU, no discrete GPU, Docker 29.4 on Ubuntu 24.04, 2026-11-22, with
`tests/profile_render.sh`, `tests/bench_parallel.sh` and `tests/bench_gpu.sh` (each run starts
from an empty `out/`, so Manim's cache never helps). **UNTESTED** means nobody measured it; it is
written from the tools' documentation and general knowledge and may be wrong.

## Summary

Times are render times of a 1080p60 final unless noted; "frame-identical" means the delivered
video decodes to exactly the serial render's frames.

| Technique | Measured on this host | Risk | How to enable | Recommendation |
|---|---|---|---|---|
| Parallel sections | 2 workers **1.19x**, 3 workers 1.14x, 4 workers 1.13x; frame-identical | low: seam check and GeometryGuard cross-check, serial fallback; manim-voiceover narration always serial | `"workers": 2` or `--workers 2` | opt-in; 2 workers on a 4-core host when nothing else renders |
| Manim's encoder overlap | 1.08x and 1.09x (paired runs); frame-identical | low; about 66 MB per extra encoder | `"encoders": 4` | opt-in; no extra gain with workers |
| Workers and encoders together | 1.10x to 1.11x | as above | both keys | no |
| 1080p at 30 fps | 1.79x (bench scene) | less smooth motion | `"fps": 30` | offer when the user wants the final sooner |
| 720p at 60 fps / 1440p at 60 fps | 1.14x / 0.75x (bench scene) | detail | `"resolution": "1280x720"` / `"2560x1440"` | rarely worth it / only on request |
| Preview quality while iterating | 3.6x faster than final (unit circle: 85 s against 305 s) | none | `"quality": "preview"` (the default) | the loop already does this |
| `--geometry` without drawing | 23.7 s instead of about 220 s (unit circle) | none for stateless updaters; frame-dependent animations are stepped | `--geometry` | now how `--geometry` works |
| Manim's partial-movie cache | unit-circle preview re-render 85 s to 60 s (21 of 138 animations reused) | a stale picture when the key misses a change (`"cache": false`) | on by default (silent jobs) | unchanged |
| Running the QA passes concurrently | 0.9x (slower) | none | - | tried, not kept |
| Skipping the automated checks | would save about 16% of a final job | loses the safety net | not offered | no |
| Several videos at once | slower: three finals at once needed 27 minutes of wall time, one after another 19 minutes | none | - | render one at a time |
| Cairo with the iGPU passed in | 1.00x | none | `--gpu` | no (Cairo is CPU-only) |
| OpenGL renderer on the Intel iGPU | 0.69x (slower than Cairo; llvmpipe on the CPU 0.71x) | renderer gaps, slightly different strokes | `"renderer": "opengl"` + `--gpu` | no |
| OpenGL renderer on an NVIDIA or AMD GPU | **UNTESTED** (no such GPU here) | renderer gaps; toolkit setup | `--nvidia` (NVIDIA), `--gpu` (AMD) | only for heavy 3D or fill-bound scenes, after a Cairo comparison |
| VA-API re-encode (Intel/AMD, Linux) | 2.6x faster than an x264 re-encode, but always an extra step; 1.5 to 4x larger files | none | `"encode": "h264_vaapi"` + GPU | no |
| NVENC, AMF, VideoToolbox, Quick Sync | **UNTESTED** (Quick Sync fails in this container) | - | native ffmpeg, after the render | delivery copies only |
| ManimGL (GPU-first 3b1b library) | not measured | different API; out of scope | - | no |

## Where the time goes (measured)

`tests/profile_render.sh examples/01-unit-circle --quality final`: the unit-circle example,
138.9 s of video, 1920x1080 at 60 fps (8334 frames), silent, on an otherwise idle host. The
profiler wraps Manim's own functions with wall-clock timers inside the render process and counts
*exclusive* time (time inside nested timed calls is subtracted), on the main thread that draws
the frames and on Manim's partial-movie encoder threads separately. Overhead: render 308 s with
the profiler, 306 s without.

| Stage (wall time on the critical path) | Seconds | Share |
|---|---|---|
| Python animation: interpolation and updaters (`always_redraw` rebuilds) | 128.3 | 34.9% |
| Cairo: drawing each frame | 65.3 | 17.7% |
| Cairo: clearing or copying the background, copying the pixel array | 22.0 | 6.0% |
| Waiting for the encoder at the end of each animation (partial movie flush) | 54.0 | 14.7% |
| Waiting for the encoder mid-animation (frame queue full) | 4.7 | 1.3% |
| Manim's cache key: hashing each play call | 10.0 | 2.7% |
| Other per-play Python (compiling animations, static frame) | 5.9 | 1.6% |
| LaTeX: `latex` and `dvisvgm` (34 formulas) | 8.7 | 2.4% |
| SVG parsing and Pango text | 1.2 | 0.3% |
| The skill's LayoutGuard and GeometryGuard (per animation) | 4.0 | 1.1% |
| `construct()` outside play calls, startup, imports | 2.8 | 0.8% |
| Joining partial movies (concat, stream copy) | 0.8 | 0.2% |
| Opening partial movie encoders | 0.1 | 0.0% |
| Job: automated checks (`qa_check.py`, three full decodes) | 57.5 | 15.6% |
| Job: stills and contact sheets | 2.1 | 0.6% |
| Job: container start, job.json, report (rest) | 0.7 | 0.2% |
| **Total job** | **368.0** | 100% |

Alongside, on Manim's encoder threads (overlapping the drawing): RGBA to YUV conversion and x264
147 s, flushing and closing partial movies 30 s. The render process used 476 s of CPU in 308 s
(1.55 cores on average), peak memory 826 MB; LaTeX and dvisvgm subprocesses 8.6 s of CPU.

What this means:

- **A render is a single-threaded Python program plus a few encoder threads.** The main thread
  (which every frame waits for) spends 35% of the job in Python animation code
  (`interpolate`, updaters, `always_redraw` rebuilding mobjects every frame) and 22% drawing with
  Cairo. The process used 1.55 cores on average; the rest of a 4-core host is not idle enough to
  run three more renders at full speed (see "Parallel sections").
- **Drawing is the only part a GPU could take over**, and it is about a fifth of the job: even
  infinitely fast drawing would save at most about 22%, and Manim's OpenGL renderer adds work
  elsewhere (see "GPU" below).
- **LaTeX, SVG and text are small** for a typical explainer: 34 formulas compiled once (latex
  1.8%, dvisvgm 0.6%), SVG parsing 0.3%, Pango text under 0.1%.
- **Encoding mostly overlaps** with drawing (x264 runs on the encoder threads, 177 s of thread
  time), but by default Manim waits for each animation's partial movie to finish encoding before
  it starts the next animation: 54 s (15%) of waiting. `"encoders"` overlaps part of that wait
  (8% faster, below).
- **The automated checks are 16%** of the job (three full decodes of the 1080p60 video for blank
  frames, holds and cuts); see "The automated checks" below.
- **Joining the partial movies is negligible** (0.8 s, stream copy). Manim's cache hashing of each
  play call is 2.7% (10 s); `"cache": false` skips it, but then re-renders redo everything.

The earlier figure of "16 to 27 minutes for a 2 to 3 minute final" came from rendering four
finals **at the same time** on this 4-core host (2026-11-21: 02, 03, 04 and a re-run of 01
overlapped; each took 16 to 27 minutes). One final alone takes 4.7 to 8.9 minutes here (the
five examples, rendered one at a time on 2026-11-22: 374, 341, 282, 506 and 533 s per job,
checks included). Rendering several at once did not even help total throughput: 02, 03 and 04,
started within 90 s of each other on 2026-11-21, needed 27 minutes of wall time; one after
another they need 19 minutes (341 + 282 + 506 s).

## Parallel sections (`"workers": N`, measured)

Manim writes every `play()`/`wait()` as its own partial movie file and joins them at the end, so
a video can be cut between any two animations. With `"workers": N` (or `--workers N`), the job
runner inside the container (`scripts/parallel_render.py`):

1. **plans** with one quick pass over the scene (every animation jumps to its end): the duration
   of every animation and an estimated cost (its frame count times the timed cost of one update
   step and one drawn frame of its end state; about 23 s for the unit circle); it also fills the
   LaTeX and text caches;
2. **splits** the animations into N contiguous ranges of about equal estimated cost, putting each
   boundary just after a cheap animation;
3. **renders** the ranges in N processes (`manim render -n A,B`), each with its own media
   directory (the LaTeX/text caches hard-linked in, so no two processes ever write the same file).
   Each worker runs the whole `construct()` and **fast-forwards** the animations before its range
   without drawing or encoding them: in one step (Manim's own skipping) when nothing on screen can
   depend on the individual frames, or frame by frame (interpolation and updaters, still without
   drawing) when the scene has a time-based updater (one that takes `dt`, such as `TracedPath`), a
   scene-level updater, a `wait_until` or an `UpdateFromFunc`;
4. **checks** two safety nets: (a) every seam: worker k also renders the last animation of worker
   k-1, and both renderings must decode to identical frames; (b) the GeometryGuard cross-check:
   every tracked object's measured box after every fast-forwarded animation must match the worker
   that drew it. If either fails, the job renders serially instead (with a job warning);
5. **joins** the partial movies in order with ffmpeg (stream copy: the encoded frames are exactly
   the ones a serial render produces), merges the GeometryGuard measurements (each animation from
   the worker that drew it) and runs the usual checks and stills.

Correctness traps, and how each is handled:

| Trap | What would go wrong | Handling |
|---|---|---|
| State carried between animations (ValueTracker, `always_redraw`, updaters that position things from trackers) | a later section starts from the wrong state | each worker runs the whole `construct()`; these are pure functions of the trackers, so jumping an animation to its end gives the same state |
| Time-based updaters (`dt`), `TracedPath`, `wait_until`, `UpdateFromFunc`, scene updaters | jumping to the end in one step integrates `dt` once, traces one segment, misses the stop condition | detected per animation; those animations are stepped frame by frame (verified: the `Traced` trap in `tests/jobs/parallel-traps` gives identical frames) |
| An updater **without** `dt` that changes state on every call (`lambda m: m.shift(RIGHT * 0.01)`: frame-rate dependent, which Manim advises against) | applied once per skipped animation instead of once per frame | caught by the seam check or the GeometryGuard cross-check when the object is on screen at a seam or tracked, and the job renders serially (verified: the `Stateful` trap). Not caught if the object is neither; use `dt` in such updaters, or render serially |
| Shared caches (`media/Tex`, `media/texts`, partial movies) | two processes writing the same file | one media directory per worker; the shared LaTeX/text caches are filled by the plan pass and hard-linked, never written concurrently; Manim's partial-movie cache is not used in parallel mode |
| manim-voiceover (`add_sound` offsets, the voiceover cache) | audio placed relative to each section, a cache written by every process | not supported: narrated `voiceover` jobs render serially (with a job warning). `"mode": "mux"` narration works, because the audio is added after the join |
| `next_section(skip_animations=True)`, `--save_sections` | sections are numbered per process | scenes that skip sections render serially; the job runner never uses `--save_sections` |
| Random numbers (`random`, `np.random`) | Manim seeds them from `config.seed`, which is unset by default, so every process draws different numbers (a serial render is not reproducible either) | the plan pass and all workers get the same `--seed` (recorded as `parallel.seed` in `summary.json`), unless the job's `manim.cfg` sets one; the output equals a serial render with that seed |

Measured on `examples/01-unit-circle`, final 1920x1080 at 60 fps (138.9 s, 8334 frames), one
run per row on an otherwise idle host (`tests/bench_parallel.sh`). Serial runs of the same job
took 304.6, 306.4, 311.6 and 329.2 s across the day, so differences under about 5% are noise.

| Configuration | Render s | Speedup | Job total s | Frames identical to serial | Time per worker s |
|---|---|---|---|---|---|
| serial (default) | 304.6 | 1.00x | 368.1 | (baseline) | - |
| `"workers": 2` | 255.1 | **1.19x** | 317.3 | yes | 209, 231 |
| `"workers": 3` | 267.7 | 1.14x | 330.1 | yes | 242, 208, 225 |
| `"workers": 4` | 268.5 | 1.13x | 330.9 | yes | 181, 236, 194, 243 |
| `"workers": 2, "encoders": 4` | 275.9 | 1.10x | 339.2 | yes | 217, 251 |
| `"workers": 4, "encoders": 4` | 274.3 | 1.11x | 337.4 | yes | 175, 234, 199, 249 |

Every parallel output decoded to exactly the serial render's 8334 frames, the seam checks and the
GeometryGuard cross-check passed, and the job's checks and geometry gate passed. Each job includes
a 23 s plan pass.

Why the gain is small on this host: the cores are already busy. One render uses 1.55 cores on
average (drawing thread plus x264 threads) and a lot of memory bandwidth (each 1080p frame is an
8 MB array copied several times). With four workers, the four ranges that take 72, 104, 60 and
94 s when rendered alone took 181 to 243 s each. A host with more cores and memory channels should
scale better; that is **UNTESTED**.

Two earlier designs, measured and dropped on the way: stepping every earlier frame exactly
(frame by frame, no drawing) and planning with Manim's `--dry_run` (which, it turned out, still
draws every frame) made 2 workers slower than serial (507 s, 0.60x); splitting by frame count
instead of estimated cost left the last quarter with 42% of the work (2 workers 1.09x, 4 workers
1.11x).

**Recommendation:** keep the serial default. On a 4-core host like this one, `"workers": 2` saves
about 15% of a final's render time (about 50 s on a 5-minute render) when nothing else is running;
more workers do not help. Do not combine it with other renders running at the same time.

## Manim's encoder pipeline (`"encoders": N`, measured)

Manim 0.22 encodes each animation's partial movie on a background thread, but with its default
`max_inflight_encoders = 1` the drawing thread waits at the end of every animation until that
file is finished. `"encoders": 4` lets up to four partial movies finish encoding while the next
animations are drawn. The frames written are the same (checked: decoded frames identical).

| Configuration | Render s | Speedup | Frames identical |
|---|---|---|---|
| serial (default), paired runs | 306.4 / 311.6 | 1.00x | (baseline) |
| `"encoders": 4`, paired runs | 284.2 / 286.1 | 1.08x / 1.09x | yes |

It costs memory (each extra partial movie in flight holds up to eight 1080p frames, about 66 MB).
**Recommendation:** a small, safe gain on its own (8%, consistent in two paired runs but close to
the run-to-run spread), so it stays opt-in; it does not add to `"workers"` (see the table above).

## The automated checks (measured)

`qa_check.py` decodes the final video once per analysis (blank frames, holds, cuts; plus two
audio passes when narrated): 56 to 62 s of a 368 s final job here. Running the three video passes
at the same time was tried and is slower on this host (62.1 and 63.7 s against 56.3 and 58.3 s
serially, identical reports), because each ffmpeg decode already uses several cores; the change
was not kept. Skipping the checks is not offered: they are the skill's safety net.

## Cheaper outputs and faster iteration

None of these change a default; use them when the user agrees or while iterating.

Measured on `tests/jobs/bench` (24 rotating vectors with circles, a traced path, a redrawn
sine wave and a formula; 10 s; one run each; render time only):

| Output | job.json | Render s | Speedup |
|---|---|---|---|
| 1920x1080 at 60 fps (the default final) | - | 24.8 | 1.00x |
| 1920x1080 at 30 fps | `"fps": 30` | 13.8 | 1.79x |
| 1280x720 at 60 fps | `"resolution": "1280x720"` | 21.8 | 1.14x |
| 2560x1440 at 60 fps | `"resolution": "2560x1440"` | 32.9 | 0.75x |
| 854x480 at 15 fps (preview) | `"quality": "preview"` | 6.7 | 3.68x |

Halving the frame rate roughly halves the work, because the per-frame Python and drawing
dominate; lowering the resolution saves much less, for the same reason. Offer 1080p30 when the user
wants a final sooner (motion is slightly less smooth); keep 1080p60 as the default.

- **Preview quality** (854x480 at 15 fps, the default `quality` while iterating) is the fast
  path: the unit-circle preview renders in 85 s against 305 s for its final (plus 31 s for its
  per-animation stills). Iterate on previews, `--still K` and `--geometry`; render the final once.
- **`--geometry`** re-measures the GeometryGuard rules without drawing any frame: 23.7 s for the
  unit circle (it used Manim's `--dry_run`, which turned out to step and draw every frame: about
  220 s). Same result (9 rules, 0 violations); `tests/test_geometry.py` still sees the old layout's
  4 violations through it.
- **Render a range** with `--animations A,B` to iterate on one section.
- **Manim's partial-movie cache** (`out/media/`, on by default for silent jobs): a re-render
  redoes only the animations whose hash changed. Measured on the unit-circle preview: an unchanged
  second render reused only 21 of 138 animations and took 60 s instead of 85 s (why the other keys
  changed was not investigated). Narrated jobs never use it.
- **Skipping the checks** is not offered (see above): about 16% of a final job here.

## GPU

### This host's Intel iGPU (measured, `tests/bench_gpu.sh`)

| Configuration | Render s (600 frames, 1080p60) | Frames/s |
|---|---|---|
| Cairo, CPU (the default) | 24.4 | 24.5 |
| Cairo, GPU passed in | 24.4 | 24.6 |
| OpenGL renderer, EGL on the CPU (llvmpipe) | 34.3 | 17.5 |
| OpenGL renderer, EGL on the iGPU (Mesa iris) | 35.3 | 17.0 |

The Cairo renderer cannot use a GPU at all. Manim's OpenGL renderer runs on the iGPU but is
slower than Cairo here, and no faster than software rendering on the CPU: its time goes to
CPU-side work (Python, triangulating fills, reading every frame back from the GPU, encoding),
not to rasterising. Details and the encode numbers: [container.md](container.md#gpu-opt-in).

### Manim's OpenGL renderer: what it is

`"renderer": "opengl"` (Manim Community's OpenGL renderer, through moderngl and a headless EGL
context in the container):

- **Draws on the GPU:** fills and strokes are triangulated on the CPU (earcut) and rasterised by
  shaders; each frame is read back to the CPU for encoding with the same PyAV/libx264 path.
- **Gaps seen here** (Manim Community 0.22.1): a bare `VMobject()` crashes it (use concrete
  classes, `TracedPath` or `always_redraw` shapes), and strokes and LaTeX look slightly different
  from Cairo (SSIM 0.991, heavier formula strokes). Manim's documentation calls the OpenGL
  renderer less complete than Cairo, so other scenes may hit other differences: test any OpenGL
  scene against a Cairo render first. The skill's parallel sections are Cairo-only.
- **Where it could pay off (UNTESTED):** a discrete GPU with heavy, fill-dominated or 3D scenes
  (surfaces with many faces, thousands of filled shapes), where rasterising, not Python, is the
  bottleneck. For typical 2D explainers the profile above says Python and per-frame readback
  dominate, so expect little gain even on a fast GPU.

### Recipes (opt-in; GPU stays off by default)

| Hardware | How | Status |
|---|---|---|
| Intel iGPU, Linux | `"gpu": true` or `--gpu`: `docker/compose.gpu.yml` passes `/dev/dri` and joins the `video` and `render` groups | measured (above): works, no speedup |
| AMD GPU, Linux | the same `--gpu` (Mesa radeonsi does OpenGL through `/dev/dri`; ROCm and `/dev/kfd` are for compute and not needed). VA-API encoding on AMD would also need `mesa-va-drivers` in the image (not included) | UNTESTED |
| NVIDIA GPU, Linux | install the NVIDIA driver and the NVIDIA Container Toolkit (`nvidia-ctk runtime configure --runtime=docker`, restart Docker), then `--nvidia` (adds `docker/compose.nvidia.yml`: device reservation with `gpu, graphics, video, utility` capabilities and the NVIDIA EGL vendor file), with `"renderer": "opengl"` in job.json. Check with `--doctor --nvidia`: the `opengl` line should name the NVIDIA GPU | UNTESTED |
| Docker Desktop on Windows (WSL 2) | passes NVIDIA GPUs to Linux containers for **CUDA compute** (`--gpus`); OpenGL/EGL and NVENC, which this skill would use, are not expected to work there | UNTESTED (general knowledge, not verified) |
| Docker Desktop on macOS | no GPU passthrough into Linux containers (the containers run in a Linux VM without Metal access) | general knowledge, not verified |

So: **GPU acceleration for the container is Linux-only, and hardware encoding on macOS and
Windows is native-only (outside Docker).**

### ManimGL (out of scope)

ManimGL (3b1b/manim) is the GPU-first original that 3Blue1Brown uses: OpenGL throughout, an
interactive window, fast previews. It is a different library with a different API (`ShowCreation`,
`CONFIG` dicts, `InteractiveScene`, ...); this skill targets Manim Community and its renderer
refuses ManimGL code. Mentioned only for completeness.

## Hardware video encoding (post-render)

Manim always encodes once itself while rendering (libx264 through PyAV, CRF 23). A hardware
encoder can only **re-encode** the finished file afterwards, so it adds time to a job rather than
saving it; it is worth it only for a separate delivery encode (for example a smaller HEVC file).
`"encode": "h264_vaapi"` (Intel VA-API, Linux) exists for experiments; the default is `"manim"`
(no re-encode).

| Encoder | Platform | Inside this Linux container | Status |
|---|---|---|---|
| VA-API (`h264_vaapi`, `hevc_vaapi`) | Intel and AMD on Linux | yes, with `--gpu` (Intel driver in the amd64 image; AMD needs `mesa-va-drivers`) | measured on Intel (below) |
| NVENC (`h264_nvenc`, `hevc_nvenc`, `av1_nvenc`) | NVIDIA on Linux and Windows | yes on Linux with `--nvidia` (the image's ffmpeg has NVENC; the toolkit's `video` capability supplies the driver library) | UNTESTED |
| Quick Sync (`h264_qsv`) | Intel on Linux and Windows | the image's ffmpeg has `h264_qsv` and the oneVPL dispatcher (`libvpl2`), but not Intel's GPU runtime (`libmfx-gen1.2`), so it fails | measured: fails in the container; natively on Windows with Intel drivers UNTESTED |
| AMF (`h264_amf`) | AMD, normally on Windows | no (the image's ffmpeg is built without AMF) | UNTESTED |
| VideoToolbox (`h264_videotoolbox`, `hevc_videotoolbox`) | macOS | no (native macOS ffmpeg only, e.g. Homebrew) | UNTESTED |

Measured on this host, re-encoding the unit-circle final (138.9 s, 8334 frames, 1080p60):

| Encoder | Settings | Encode s | Size MB | SSIM vs Manim's file |
|---|---|---|---|---|
| (Manim's own file, written during the render) | libx264 CRF 23, one encoder per animation | - | 6.1 | 1 |
| libx264, CPU | CRF 23, preset medium, whole file at once | 98.5 | 3.6 | 0.9996 |
| h264_vaapi, iGPU | QP 20 (what `"encode": "h264_vaapi"` uses) | 38.0 | 13.7 | 0.9997 |
| h264_vaapi, iGPU | QP 26 | 38.2 | 7.0 | 0.9993 |
| h264_vaapi, iGPU | QP 30 | 38.3 | 5.3 | 0.9986 |
| hevc_vaapi, iGPU | QP 26 | 39.8 | 5.3 | 0.9995 |
| h264_qsv, iGPU | global_quality 23 | failed: "Error creating a MFX session" (no Intel oneVPL GPU runtime in the image) | - | - |

(`tests/bench_encode.sh`.) VA-API encodes 2.6 times faster than x264 here, but at similar SSIM its
files are 1.5 to 4 times larger. A one-pass x264 re-encode of the whole file is 41% smaller than
Manim's own output (which encodes every animation separately) at SSIM 0.9996: worth it for a
delivery copy (`"encode": "libx264"`, CRF 20, or by hand), not for speed. No encoder option was
added: none of these makes a render faster.

Hardware encoders need a higher bitrate than x264 for the same quality; at equal visual quality
the VA-API files here are several times larger. Typical native commands for a delivery
re-encode (UNTESTED; adjust the quality value until the file size and look are right):

```text
NVIDIA (Linux/Windows): ffmpeg -i in.mp4 -c:v h264_nvenc -preset p5 -cq 23 -c:a copy out.mp4
macOS:                  ffmpeg -i in.mp4 -c:v h264_videotoolbox -q:v 60 -c:a copy out.mp4
Windows, AMD:           ffmpeg -i in.mp4 -c:v h264_amf -quality quality -qp_i 22 -qp_p 22 -c:a copy out.mp4
Windows, Intel:         ffmpeg -i in.mp4 -c:v h264_qsv -global_quality 23 -c:a copy out.mp4
```
