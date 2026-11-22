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
├── README.md, LICENSE (MIT), AGENTS.md
├── install.sh                      symlinks the one canonical skill into agent skill dirs
├── skills/manim-video/             the skill (the only copy)
│   ├── SKILL.md                    workflow and rules (spec-only frontmatter)
│   ├── docker/                     Dockerfile, requirements.in/.lock (hash-pinned), manim_job.py
│   │                               (the in-container job runner), compose.yml, compose.gpu.yml
│   ├── .dockerignore               the build context is the skill directory
│   ├── references/                 container.md (job contract, GPU, benchmarks), API cheatsheet,
│   │                               scene patterns, style guide, QA checklist, intuition rubric,
│   │                               narration, troubleshooting, environment (host route)
│   ├── scripts/                    render-in-container.sh (the renderer), check_env.sh,
│   │                               setup_env.sh, render.sh (host route), frames.py, qa_check.py,
│   │                               manim_qa.py (LayoutGuard), geometry_qa.py (GeometryGuard),
│   │                               kokoro_service.py, narration_script.py,
│   │                               narrate_mux.py, narration_timeline.py, _env.sh, _ffbin.py
│   └── templates/                  job.json, storyboard, review log, silent and narrated scenes,
│                                   narration.json
├── examples/                       the five test prompts run through the full loop
└── tests/                          validate_skill.py, test_container.sh, test_geometry.py,
                                    check_patterns.py, bench_gpu.sh, api_smoke.py, jobs/ (smoke,
                                    narrated, mux, bench, geometry-old/fixed-unit-circle)
```

## Install

```bash
git clone git@github.com:quellen-sol/manim-video-skill.git ~/dev/manim-video-skill
cd ~/dev/manim-video-skill
./install.sh                                   # symlinks; --dry-run to preview, --uninstall to undo
skills/manim-video/scripts/setup_env.sh        # builds the render image manim-video:local (~6 min)
skills/manim-video/scripts/check_env.sh --tts  # read-only check (add --gpu, --host)
```

The container route needs only Docker with the compose plugin and membership of the `docker`
group. For the host route (fallback), `setup_env.sh --host` builds a venv from the same lock
file; it needs system packages it cannot install and lists any that are missing.

`install.sh` creates two symlinks to `skills/manim-video` and changes nothing else:

| Agent | How it finds the skill | Status on the nucbox |
|---|---|---|
| OpenClaw | reads `~/.agents/skills` natively | verified: `openclaw skills list` shows `manim-video` as ready |
| Claude Code | `~/.claude/skills/manim-video` symlink | verified: a running Claude Code session listed `manim-video` right after `install.sh` |
| Codex CLI | reads `~/.agents/skills` natively | untested (Codex is not installed here) |
| Hermes Agent | add `~/.agents/skills` to `skills.external_dirs` in `~/.hermes/config.yaml` | untested (Hermes is not installed here); `install.sh` prints the step |

`--openclaw` also links `~/.openclaw/skills/manim-video`, which is only needed for an OpenClaw
that does not read `~/.agents/skills`.

## Rendering: the container route (default)

```bash
R=~/.agents/skills/manim-video/scripts/render-in-container.sh
mkdir -p jobs/demo && cp ~/.agents/skills/manim-video/templates/job.json jobs/demo/
# write jobs/demo/scene.py; set "scene" in jobs/demo/job.json
"$R" jobs/demo                        # preview: 854x480 @ 15 fps
"$R" jobs/demo --quality final        # 1920x1080 @ 60 fps
"$R" jobs/demo --still 12             # full-resolution frame after animation 12
"$R" jobs/demo --frames --count 16    # more stills, no re-render
```

Each run writes `jobs/demo/out/`: `<Scene>-<quality>.mp4`, `report.md`/`report.json` (ffprobe
streams, resolution, duration, audio, blank-screen and stall detection, pop-ins, LayoutGuard
warnings, and the measured geometry check: declared `concentric`/`symmetric`/`within_margin`/
`centered_in` rules from `scripts/geometry_qa.py`, plus `geometry.json`), `stills/` (contact sheets, one still per animation, `index.txt`), `render.log` and
`summary.json`. The contract and every `job.json` key: `skills/manim-video/references/container.md`.

- **Image** `manim-video:local` (never pushed): Ubuntu 24.04 by digest, apt from a dated
  `snapshot.ubuntu.com` snapshot, Python packages hash-pinned in `docker/requirements.lock`.
  Manim Community 0.22.1, manim-voiceover 0.4.0, Python 3.12, TeX Live 2023 (latex-base,
  latex-extra, fonts-recommended, science, tipa) + dvisvgm 3.2.1, ffmpeg 6.1.1, Cairo/Pango,
  Noto fonts, Mesa EGL/GL, Intel VA-API. 1.72 GB; first build 6 min 8 s on the nucbox.
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
  defaults are Cairo, GPU off, no re-encode. Numbers: `references/container.md`.

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

| Prompt | Narration | Previews | Final (1080p60) | Rubric |
|---|---|---|---|---|
| unit circle and the six trig functions | silent | 3 | 138.9 s | 20/20 |
| modern LLM weights and neurons | silent | 5 | 150.0 s | 19/20 |
| git: commit, branch, merge, rebase, conflicts, teams | silent | 6 | 139.0 s | 20/20 |
| Fourier series as epicycles | silent | 2 | 129.5 s | 20/20 |
| gradient descent and backprop | Kokoro via manim-voiceover | 6 | 158.2 s | 20/20 |

All five pass `qa_check.py`. Known small flaws and the lessons folded back into the skill are
listed in `examples/README.md`.

## Development

```bash
python3 tests/validate_skill.py   # agentskills.io validator (skills-ref) + portability lint
tests/test_container.sh           # end to end: build, render, LaTeX, narration, GPU, no strays (~1 min)
python3 tests/test_geometry.py    # geometry checker: unit tests + the old unit-circle layout must FAIL
python3 tests/check_patterns.py   # renders every scene in references/scene-patterns.md (container;
                                  #   --route host for the host route)
tests/bench_gpu.sh                # CPU vs GPU render and encode benchmark (quiet host, ~6 min)
mkdir -p out && cp tests/api_smoke.py out/ && skills/manim-video/scripts/render.sh preview out/api_smoke.py
```

After changing anything in `skills/manim-video/scripts/*.py` or `docker/`, the next container
render rebuilds the image automatically (it compares a source hash stored in an image label).

Render output goes under `out/` (git-ignored). `AGENTS.md` has the rules for editing the skill.

## License

MIT, see `LICENSE`.
