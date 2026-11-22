# manim-video skill

One cross-agent [Agent Skill](https://agentskills.io) that makes short, intuitive explainer
videos with [Manim Community](https://www.manim.community/) v0.22.1, optionally narrated with a
local [Kokoro](https://github.com/remsky/Kokoro-FastAPI) TTS server.

The skill makes the agent work in a loop rather than in one shot: **plan** a storyboard,
**write** the scene, **render** a fast preview, **watch** it (extract stills and actually look at
them, plus headless checks), **judge** intuitiveness against a rubric, **fix** and repeat, and
only then render the **final** 1080p60 file.

## Layout

```
manim-video-skill/
├── README.md, LICENSE (MIT), AGENTS.md
├── install.sh                      symlinks the one canonical skill into agent skill dirs
├── skills/manim-video/             the skill (the only copy)
│   ├── SKILL.md                    workflow and rules (spec-only frontmatter)
│   ├── references/                 API cheatsheet, scene patterns, style guide, QA checklist,
│   │                               intuition rubric, narration, troubleshooting, environment
│   ├── scripts/                    check_env.sh, setup_env.sh, render.sh, frames.py, qa_check.py,
│   │                               manim_qa.py (LayoutGuard), kokoro_service.py, narrate_mux.py,
│   │                               narration_timeline.py, _env.sh, _ffbin.py, docker/Dockerfile
│   └── templates/                  storyboard, review log, silent and narrated scenes, narration.json
├── examples/                       the five test prompts run through the full loop
└── tests/                          validate_skill.py, check_patterns.py, api_smoke.py
```

## Install

```bash
git clone git@github.com:quellen-sol/manim-video-skill.git ~/dev/manim-video-skill
cd ~/dev/manim-video-skill
./install.sh                                   # symlinks; --dry-run to preview, --uninstall to undo
skills/manim-video/scripts/setup_env.sh        # user space: static ffmpeg + Docker image
skills/manim-video/scripts/check_env.sh --tts  # read-only check, including a Kokoro test clip
```

`install.sh` creates two symlinks to `skills/manim-video` and changes nothing else:

| Agent | How it finds the skill | Status on the nucbox |
|---|---|---|
| OpenClaw | reads `~/.agents/skills` natively | verified: `openclaw skills list` shows `manim-video` as ready |
| Claude Code | `~/.claude/skills/manim-video` symlink | verified: a running Claude Code session listed `manim-video` right after `install.sh` |
| Codex CLI | reads `~/.agents/skills` natively | untested (Codex is not installed here) |
| Hermes Agent | add `~/.agents/skills` to `skills.external_dirs` in `~/.hermes/config.yaml` | untested (Hermes is not installed here); `install.sh` prints the step |

`--openclaw` also links `~/.openclaw/skills/manim-video`, which is only needed for an OpenClaw
that does not read `~/.agents/skills`.

## Render recipe (what works without root)

Manim Community cannot be pip-installed on this host without root: `manimpango` and `pycairo`
publish no Linux wheels and need `libcairo2-dev`/`libpango1.0-dev` headers. The working,
user-space recipe is:

1. **Renderer:** the official image `manimcommunity/manim:v0.22.1` (Manim, Python 3.14, TeX Live),
   extended by `scripts/docker/Dockerfile` into `manim-video:0.22.1` with manim-voiceover 0.4.0,
   ffmpeg and sox. `render.sh` runs one `--rm` container per render as your uid, with
   `--network none` for silent scenes.
2. **Host helpers:** a static ffmpeg/ffprobe build in `~/.local/share/manim-video/bin` (the
   system ffmpeg on this host is installed but broken: `liblapack.so.3` is missing), and the
   system `python3` (stdlib only) for `frames.py`, `qa_check.py` and `narrate_mux.py`.
3. **Narration:** `KokoroService` (manim-voiceover) POSTs to `$KOKORO_BASE_URL/audio/speech`
   (default `http://127.0.0.1:8880/v1`, model `kokoro`, voice `af_heart`). For narrated scenes
   `render.sh` maps the host's loopback to `host.docker.internal` inside the container and passes
   `KOKORO_API_KEY` by name only. The fallback `narrate_mux.py` makes one WAV per beat, measures
   it and muxes after rendering.

```bash
SKILL_DIR=~/.agents/skills/manim-video
"$SKILL_DIR/scripts/render.sh" preview scene.py Explainer      # 854x480 @ 15 fps
python3 "$SKILL_DIR/scripts/qa_check.py" <video>                 # headless checks
python3 "$SKILL_DIR/scripts/frames.py" <video> --beats --mid     # stills + contact sheets
"$SKILL_DIR/scripts/render.sh" final scene.py Explainer        # 1920x1080 @ 60 fps
```

Details: `skills/manim-video/references/environment.md`.

## Narration settings

| Variable | Default |
|---|---|
| `KOKORO_BASE_URL` | `http://127.0.0.1:8880/v1` |
| `KOKORO_MODEL` | `kokoro` |
| `KOKORO_VOICE` | `af_heart` |
| `KOKORO_API_KEY` | unset; read from the environment only, never written or printed |

To load only the key from an env file without exposing other variables:
`export KOKORO_API_KEY="$(sed -n 's/^KOKORO_API_KEY=//p' /path/to/secrets.env)"`.

## Examples (the test prompts)

`examples/` holds the five test prompts, each run through the full loop by a fresh agent that
had only the skill: prompt, storyboard, final scene code, review log, inspection stills, and
notes on the bugs found and fixed. Videos are not committed (on the nucbox they are in `out/`);
rebuild them with `render.sh final examples/<name>/scene.py Explainer`.

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
python3 tests/check_patterns.py   # renders every scene in references/scene-patterns.md
mkdir -p out && cp tests/api_smoke.py out/ && skills/manim-video/scripts/render.sh preview out/api_smoke.py
```

Render output goes under `out/` (git-ignored). `AGENTS.md` has the rules for editing the skill.

## License

MIT, see `LICENSE`.
