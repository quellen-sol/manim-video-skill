# manim-video skill

One cross-agent [Agent Skill](https://agentskills.io) that makes short, intuitive explainer
videos with [Manim Community](https://www.manim.community/) v0.22.1, optionally narrated with a
local [Kokoro](https://github.com/remsky/Kokoro-FastAPI) TTS server.

The skill makes the agent work in a loop rather than in one shot: **plan** a storyboard,
**write** the scene, **render** a fast preview, **watch** it (extract stills and actually look at
them, plus headless checks), **judge** intuitiveness against a rubric, **fix** and repeat, and
only then render the **final** 1080p60 file.

Rendering runs in a **Docker image that holds the whole toolchain** (Manim, LaTeX, ffmpeg,
manim-voiceover, the helpers). The agent writes a job directory (`scene.py`, `job.json`,
assets), runs one wrapper, and gets back a video, stills to look at and a check report. A
host-native install is kept only as a fallback for local testing.

## Layout

```
manim-video-skill/
├── README.md, LICENSE (MIT), AGENTS.md, .gitattributes (LF for everything that runs in Linux)
├── install.py                      links the one canonical skill into agent skill dirs (Linux,
│                                   macOS, Windows; Python 3.9+, stdlib only)
├── install.sh, install.ps1         thin shims that run install.py (bash/zsh; PowerShell)
├── skills/manim-video/             the skill (the only copy)
│   ├── SKILL.md                    workflow and rules (spec-only frontmatter)
│   ├── docker/                     Dockerfile (linux/amd64 and linux/arm64), requirements.in/.lock
│   │                               (hash-pinned), manim_job.py (the in-container job runner),
│   │                               compose.yml, compose.gpu.yml, compose.nvidia.yml (untested)
│   ├── .dockerignore               the build context is the skill directory
│   ├── references/                 container.md (job contract, GPU, benchmarks), gpu-and-speed.md
│   │                               (where render time goes, parallel sections, GPU and hardware
│   │                               encoding per platform), API cheatsheet, scene patterns, style
│   │                               guide, QA checklist, intuition rubric, narration,
│   │                               troubleshooting, environment (host route)
│   ├── scripts/                    render_in_container.py (the renderer, cross-platform) with
│   │                               render-in-container.sh / .ps1 shims, parallel_render.py,
│   │                               check_env.sh, setup_env.sh, render.sh (host route), frames.py,
│   │                               qa_check.py, manim_qa.py (LayoutGuard), geometry_qa.py
│   │                               (GeometryGuard), kokoro_service.py, narration_script.py,
│   │                               narrate_mux.py, narration_timeline.py, _env.sh, _ffbin.py
│   └── templates/                  job.json, storyboard, review log, silent and narrated scenes,
│                                   narration.json
├── examples/                       the five test prompts run through the full loop
└── tests/                          validate_skill.py, test_wrapper.py, test_container.sh,
                                    test_geometry.py, check_patterns.py, bench_gpu.sh,
                                    bench_parallel.sh, profile_render.sh (+ profile/), api_smoke.py,
                                    jobs/ (smoke, narrated, mux, bench, geometry-old/fixed-unit-circle)
```

## Install

The skill is one folder (`skills/manim-video`). Agents find it through a link (or a copy) in their
skills directory; all rendering happens in a Docker image that the wrapper builds on first use.
Status per platform: **Linux is verified** (Ubuntu 24.04, amd64, on the nucbox). **macOS and
Windows are UNTESTED**: the steps below follow the tools' documentation, and everything that
could be checked from Linux was (the Windows path conversion and the installer's junction and
copy logic are unit-tested, the PowerShell shims are syntax-checked, the arm64 image is checked
statically). See "What to test on a real Mac or Windows PC" at the end of this section.

### What you need

| | Linux | macOS (Apple Silicon or Intel) | Windows 10/11 |
|---|---|---|---|
| Containers | Docker Engine with the compose plugin (v2); your user in the `docker` group | Docker Desktop | Docker Desktop with the WSL 2 backend |
| Git | `git` | `git` (Xcode Command Line Tools or Homebrew) | Git for Windows |
| Python 3.9+ (runs the wrapper and the installer; standard library only) | `python3`, usually preinstalled | `python3` from `xcode-select --install`, or Homebrew | python.org installer or `winget install Python.Python.3.12` (gives the `py` launcher) |
| Disk | about 1.8 GB for the image plus build cache | same (inside Docker Desktop's disk) | same (inside Docker Desktop's WSL disk) |
| Status | verified | UNTESTED | UNTESTED |

No root is needed beyond installing Docker itself. The image runs as your user, never as root.

### Linux (verified)

```bash
git clone git@github.com:quellen-sol/manim-video-skill.git ~/dev/manim-video-skill
cd ~/dev/manim-video-skill
./install.sh --dry-run                                     # what it would link
./install.sh                                               # link; --uninstall to undo
skills/manim-video/scripts/render-in-container.sh --check  # Docker, compose, image status
skills/manim-video/scripts/setup_env.sh                    # build manim-video:local (~6 min first time)
skills/manim-video/scripts/check_env.sh --tts              # fuller read-only check (add --gpu, --host)
skills/manim-video/scripts/render-in-container.sh tests/jobs/smoke   # first smoke render (~15 s)
```

The smoke render prints `VIDEO:`, `SHEET:` and `REPORT:` paths under `tests/jobs/smoke/out/` and
exits 0. `install.sh` creates two symlinks to `skills/manim-video` and changes nothing else.

### macOS, Apple Silicon or Intel (UNTESTED)

1. Install [Docker Desktop for Mac](https://docs.docker.com/desktop/setup/install/mac-install/)
   (the Apple Silicon or the Intel build) and start it. In Settings, Resources, give it at least
   4 CPUs and 4 GB of memory. Keep the clone and your job directories under `/Users` (shared with
   containers by default).
2. Install Git and Python: `xcode-select --install`, or `brew install git python`.
3. In Terminal (zsh), run the Linux commands above, but build with
   `skills/manim-video/scripts/render-in-container.sh --build` instead of `setup_env.sh`
   (`check_env.sh` and `setup_env.sh` were written for Linux; the wrapper's `--check` and
   `--build` are the cross-platform equivalents). On Apple Silicon the image builds natively for
   `linux/arm64`.

### Windows 10/11, native PowerShell (UNTESTED)

1. Install [Docker Desktop for Windows](https://docs.docker.com/desktop/setup/install/windows-install/)
   with the WSL 2 backend (the default), start it and wait until it says it is running.
2. Install Git and Python: `winget install Git.Git Python.Python.3.12` (or the python.org and
   git-scm.com installers). Open a new PowerShell window so they are on `PATH`.
3. Clone, link and build (`.gitattributes` keeps every script and Docker file with LF endings):

   ```powershell
   git clone git@github.com:quellen-sol/manim-video-skill.git $env:USERPROFILE\dev\manim-video-skill
   cd $env:USERPROFILE\dev\manim-video-skill
   .\install.ps1 --dry-run
   .\install.ps1
   .\skills\manim-video\scripts\render-in-container.ps1 --check
   .\skills\manim-video\scripts\render-in-container.ps1 --build
   .\skills\manim-video\scripts\render-in-container.ps1 tests\jobs\smoke
   ```

   If PowerShell refuses to run scripts, allow local scripts for your account once:
   `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, or run one script with
   `powershell -ExecutionPolicy Bypass -File .\install.ps1`.
4. `install.ps1` links with a symlink if Windows allows it (Developer Mode on, or an elevated
   shell), otherwise with a directory junction (no special rights), otherwise it copies the
   skill and marks the copy (run `.\install.ps1` again after `git pull` to refresh a copy).
5. Agents that run shell commands through Git Bash (Claude Code on Windows does) can use the
   `.sh` shim; agents that use PowerShell (Codex, OpenClaw's native Windows exec) use the `.ps1`
   shim. Both run the same `render_in_container.py`.

### Windows with WSL2 (UNTESTED here)

Inside the WSL distribution (for example Ubuntu), follow the Linux steps. Docker can be Docker
Desktop with WSL integration turned on for that distribution (Settings, Resources, WSL
integration) or Docker Engine installed inside WSL. Keep the clone and job directories in the
WSL file system (`~/...`), not under `/mnt/c` (slow, and file modes do not survive). Agents
running inside WSL see the Linux paths; agents on the Windows side do not see skills installed
in WSL, and the reverse: install in each place an agent runs. The wrapper refuses
`\\wsl$\...` paths when called from Windows, because Docker Desktop cannot bind-mount them
reliably: run it from inside WSL for files that live there.

### Where each agent looks for skills

`install.py` (through `install.sh` or `install.ps1`) links the skill into the first two rows'
directories; `--openclaw` adds the third.

| Agent | Linux, macOS, WSL2 | Windows (native) | Status |
|---|---|---|---|
| Codex CLI | `~/.agents/skills` | `%USERPROFILE%\.agents\skills` (assumed: `~` is the user profile) | untested (Codex is not installed on the nucbox) |
| OpenClaw | `~/.agents/skills` (and `~/.openclaw/skills`) | `%USERPROFILE%\.agents\skills`, `%USERPROFILE%\.openclaw\skills` for a native gateway; Windows Hub's default local gateway runs in its own WSL distro, so install there with the Linux steps | verified on Linux (`openclaw skills list` shows it ready) |
| Claude Code | `~/.claude/skills` (or `$CLAUDE_CONFIG_DIR/skills`) | `%USERPROFILE%\.claude\skills` | verified on Linux |
| Hermes Agent | add `~/.agents/skills` to `skills.external_dirs` in `~/.hermes/config.yaml` | the native install keeps its data in `%LOCALAPPDATA%\hermes` (or `HERMES_HOME`): add the full `.agents\skills` path there | untested (Hermes is not installed here); the installer prints the step |

Hermes example (`~` and `${VAR}` are expanded):

```yaml
skills:
  external_dirs:
    - ~/.agents/skills
```

### Narration with Kokoro (optional, any OS)

Narrated jobs call an OpenAI-compatible TTS server, normally
[Kokoro-FastAPI](https://github.com/remsky/Kokoro-FastAPI), listening on the host at port 8880.
The render container reaches it as `host.docker.internal:8880`: Docker Desktop (macOS, Windows)
provides that name, and on Linux the compose file maps it to the host gateway. `localhost` and
`127.0.0.1` in job.json are rewritten to it automatically.

- Run Kokoro on the host so that port 8880 answers on the host. Its CPU image
  (`ghcr.io/remsky/kokoro-fastapi-cpu`) is published for `linux/amd64` and `linux/arm64`, so it
  runs under Docker Desktop on Apple Silicon too; publish the port (`-p 8880:8880`). (Not run
  from this README: the nucbox already runs it.)
- If your server needs a key, put it in the environment as `KOKORO_API_KEY` before rendering
  (bash: `export`, PowerShell: `$env:KOKORO_API_KEY = ...`). The wrapper passes it to narrated
  jobs by name and never prints or stores it. On the nucbox it is read from
  `~/.config/agent-stack/gateway.env` if unset.
- Check from the host, then render the narrated test job:

  ```bash
  curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8880/v1/models     # 200 (or 401 without a key)
  skills/manim-video/scripts/render-in-container.sh --check --tts
  skills/manim-video/scripts/render-in-container.sh tests/jobs/narrated
  ```

  On Windows: `.\skills\manim-video\scripts\render-in-container.ps1 --check --tts` and
  `... tests\jobs\narrated`.
- If the container cannot reach the host (a host firewall on Linux), set
  `MANIM_TTS_NETWORK=host` for narrated renders.

### Troubleshooting

| Symptom | Fix |
|---|---|
| `cannot talk to the Docker daemon` | macOS/Windows: start Docker Desktop and wait until it is running. Linux: is the service up, and is your user in the `docker` group (`id -nG`; adding it needs an administrator and a new login)? |
| `needs Python 3.9 or newer` | install Python (table above); on Windows the `python` that opens the Microsoft Store is only an alias, so install Python or use `py -3` |
| bind mount errors, or `out/` stays empty | macOS: the job directory must be under a path shared with Docker Desktop (Settings, Resources, File sharing; `/Users` is shared by default). Windows: use a local drive path such as `C:\Users\me\jobs\demo` (the wrapper passes it to compose as `C:/Users/me/jobs/demo`); network shares and `\\wsl$\...` paths are refused, run from inside WSL for those |
| `/usr/bin/env: 'bash\r'`, `$'\r': command not found`, or the image build fails on a `RUN` line | the checkout has CRLF line endings (a copy made without git, or a clone made before `.gitattributes` existed). Clone again with Git; `.gitattributes` forces LF |
| `install.ps1` made a junction or a copy, not a symlink | expected without Developer Mode (Settings, For developers) or an elevated shell. Junctions behave like links; a copy needs `.\install.ps1` again after each `git pull` |
| PowerShell: `running scripts is disabled on this system` | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, or `powershell -ExecutionPolicy Bypass -File ...` |
| Apple Silicon: the image build fails | the image builds natively for `linux/arm64` (checked only statically). As a slower fallback, build and run the amd64 image under emulation: set `DOCKER_DEFAULT_PLATFORM=linux/amd64` before `--build` and every render (UNTESTED) |
| `--gpu` prints "rendering on the CPU" on macOS or Windows | expected: Docker Desktop gives Linux containers no GPU for this use (references/gpu-and-speed.md); the default Cairo renderer is CPU-only anyway |
| narration: `cannot reach the TTS server` | is Kokoro answering on the host's port 8880 (`--check --tts`)? Linux: try `MANIM_TTS_NETWORK=host` |

### What to test on a real Mac or Windows PC

1. `install.sh` (macOS) or `install.ps1` (Windows): links created; the agent lists the skill.
2. `render-in-container --check`, then `--build`: the image builds (on Apple Silicon: natively for arm64).
3. The smoke render: `tests/jobs/smoke` exits 0 and `out/report.md` says PASS.
4. A silent example at preview quality (`examples/01-unit-circle`), and one final.
5. Narration: Kokoro on the host, `--check --tts`, then `tests/jobs/narrated`.
6. Windows: a job directory path with spaces; Ctrl-C during a render leaves no container
   behind (`docker ps -a`); the `.sh` shim from Git Bash.

## Rendering: the container route (default)

```bash
S=~/.agents/skills/manim-video
R=$S/scripts/render-in-container.sh
mkdir -p jobs/demo
cp $S/templates/job.json jobs/demo/job.json          # "scene": "Explainer"
cp $S/templates/scene_silent.py jobs/demo/scene.py    # the skeleton; your scene goes here
"$R" jobs/demo                        # preview: 854x480 @ 15 fps
"$R" jobs/demo --quality final        # 1920x1080 @ 60 fps
"$R" jobs/demo --still 3              # full-resolution frame after animation 3
"$R" jobs/demo --frames --count 16    # more stills, no re-render
"$R" jobs/demo --geometry             # re-measure the GeometryGuard rules (dry run, seconds)
"$R" jobs/demo --quality final --workers 2   # opt-in: render sections in parallel
```

On Windows (PowerShell) the same commands work with
`$R = "$env:USERPROFILE\.agents\skills\manim-video\scripts\render-in-container.ps1"` and `& $R jobs\demo ...`.

Each run writes `jobs/demo/out/`: `<Scene>-<quality>.mp4`, `report.md`/`report.json` (ffprobe
streams, resolution, duration, audio, blank-screen and stall detection, pop-ins, LayoutGuard
warnings, and the measured geometry check: declared `concentric`/`symmetric`/`within_margin`/
`centered_in` rules from `scripts/geometry_qa.py`, plus `geometry.json`), `stills/` (contact sheets, one still per animation, `index.txt`), `render.log` and
`summary.json`. The contract and every `job.json` key: `skills/manim-video/references/container.md`.

- **Image** `manim-video:local` (never pushed): Ubuntu 24.04 by digest, apt from a dated
  `snapshot.ubuntu.com` snapshot, Python packages hash-pinned in `docker/requirements.lock`.
  Manim Community 0.22.1, manim-voiceover 0.4.0, Python 3.12, TeX Live 2023 (latex-base,
  latex-extra, fonts-recommended, science, tipa) + dvisvgm 3.2.1, ffmpeg 6.1.1, Cairo/Pango,
  Noto fonts, Mesa EGL/GL, Intel VA-API (amd64 only). Builds for `linux/amd64` (verified) and
  `linux/arm64` (Apple Silicon, arm64 Linux; checked statically, see `docker/Dockerfile`).
  1.72 GB (amd64); first build 6 min 8 s on the nucbox, about 4 min after a Dockerfile change, seconds after a helper change.
- **Compose** is the definition (`docker/compose.yml`, styled after the host's Jellyfin
  stack); the wrapper runs `docker compose run --rm` with a unique project per job and removes
  the container on exit, error, Ctrl-C or SIGTERM. No restart policy, ports or container names;
  `network_mode` instead of a project network.
- **Least privilege:** runs as your uid:gid (the image refuses root), job sources read-only and
  only `out/` writable, read-only root filesystem, `cap_drop: ALL`, `no-new-privileges`, no
  network for silent jobs.
- **Narration:** narrated jobs get the host's Kokoro as `host.docker.internal:8880` (Docker host
  gateway) and `KOKORO_API_KEY` by name, read at run time from the environment or from
  `~/.config/agent-stack/gateway.env`; never in the image, repo or logs.
- **GPU (opt-in, `"gpu": true` or `--gpu`):** `docker/compose.gpu.yml` passes `/dev/dri` only and
  joins the `video` and `render` groups (ids resolved with `getent` at run time). Measured on
  the nucbox's Intel N150 iGPU: it does not speed up rendering (Cairo is CPU-only; Manim's
  OpenGL renderer runs on the iGPU but is slower than Cairo here), and VA-API H.264 encoding
  works from the container but only as an extra post-render step with larger files. So the
  defaults are Cairo, GPU off, no re-encode. `--nvidia` adds `docker/compose.nvidia.yml` for an
  NVIDIA GPU on Linux (UNTESTED). Docker Desktop on macOS and Windows gives Linux containers no
  GPU for this use, so GPU options are Linux-only. Numbers and recipes:
  `references/gpu-and-speed.md`.
- **Speed (opt-in):** `"workers": N` renders sections of one scene in parallel processes
  and joins them (frame-identical to a serial render; seams checked, falls back to serial by
  itself), and `"encoders": N` overlaps Manim's partial-movie encoding with drawing. Measured on
  the nucbox's 4-core N150 for a 2:19 final: serial 305 s, `"workers": 2` 255 s (1.19x),
  `"encoders": 4` 1.08x; more workers do not help there because one render already uses about 1.5
  cores. Defaults stay serial. Where render time goes, and the GPU findings:
  `references/gpu-and-speed.md`.

## Rendering: the host route (fallback)

`scripts/render.sh preview|final|still scene.py Scene` with a host-native Manim (the venv from
`setup_env.sh --host`, or `manim` on `PATH`), then `qa_check.py` and `frames.py` by hand. On the
nucbox it works since the owner installed ffmpeg, TeX Live, dvisvgm and the Cairo/Pango headers;
it renders the same scene near-identically to the container (SSIM 0.999). Details:
`skills/manim-video/references/environment.md`.

## Narration settings

| Variable | Default |
|---|---|
| `KOKORO_BASE_URL` | `http://127.0.0.1:8880/v1` |
| `KOKORO_MODEL` | `kokoro` |
| `KOKORO_VOICE` | `af_heart` |
| `KOKORO_API_KEY` | unset; read from the environment only, never written or printed |
| `KOKORO_ENV_FILE` | `~/.config/agent-stack/gateway.env`; the container wrapper reads only the `KOKORO_API_KEY=` line from it when the variable is unset |

In a job, `job.json` `narration.voice` and `narration.kokoro.base_url`/`model` override these.

## Examples (the test prompts)

`examples/` holds the five test prompts, each run through the full loop by a fresh agent that
had only the skill: prompt, storyboard, final scene code, review log, inspection stills, and
notes on the bugs found and fixed. Videos are not committed (on the nucbox they are in `out/`).
Each example folder is also a job directory: `render-in-container.sh examples/<name> --quality final`.

| Prompt | Narration | Final (1080p60) | Rubric | Geometry |
|---|---|---|---|---|
| unit circle and the six trig functions | silent | 138.9 s | 20/20 | PASS (9 rules) |
| modern LLM weights and neurons | silent | 150.0 s | 19/20 | PASS (23 rules) |
| git: commit, branch, merge, rebase, conflicts, teams | silent | 138.5 s | 19/20 | PASS (25 rules) |
| Fourier series as epicycles | silent | 129.5 s | 20/20 | PASS (13 rules) |
| gradient descent and backprop | Kokoro via manim-voiceover | 161.2 s | 20/20 | PASS (18 rules) |

These are the container re-run (2026-11-22): every final rendered inside the container and
passes the automated checks, including the measured geometry check. Iterations, bugs fixed and
the first run's numbers are in `examples/README.md`.

## Development

```bash
python3 tests/validate_skill.py   # agentskills.io validator (skills-ref) + portability lint
python3 tests/test_wrapper.py     # wrapper + installer, no Docker: Windows path forms, junction/copy logic
tests/test_container.sh           # end to end: build, render, LaTeX, narration, parallel sections,
                                  #   GPU, interrupt, no strays (~3 min)
python3 tests/test_geometry.py    # geometry checker: unit tests + the old unit-circle layout must FAIL
python3 tests/check_patterns.py   # renders every scene in references/scene-patterns.md (container;
                                  #   --route host for the host route)
tests/bench_gpu.sh                # CPU vs GPU render and encode benchmark (quiet host, ~6 min)
tests/profile_render.sh examples/01-unit-circle            # where the time goes in one final (~6 min)
tests/bench_parallel.sh examples/01-unit-circle final      # serial vs "encoders" vs "workers" (~30 min)
mkdir -p out && cp tests/api_smoke.py out/ && skills/manim-video/scripts/render.sh preview out/api_smoke.py
```

After changing anything in `skills/manim-video/scripts/*.py` (except the host-side
`render_in_container.py`) or `docker/`, the next container render rebuilds the image
automatically (it compares a source hash stored in an image label). Shell scripts pass
`shellcheck --severity=warning`; the PowerShell shims are checked with pwsh's parser.

Render output goes under `out/` (git-ignored). `AGENTS.md` has the rules for editing the skill.

## License

MIT, see `LICENSE`.
