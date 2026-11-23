# Agent notes for this repo

This repo holds one cross-agent skill: `skills/manim-video/` (entry point `skills/manim-video/SKILL.md`).
It is linked into agent skill directories by `install.py` (shims: `install.sh`, `install.ps1`); there are
no per-agent copies (only Windows without symlink or junction rights falls back to a marked copy).

When you change the skill:

- Keep `SKILL.md` frontmatter to `name`, `description`, `license`, `compatibility` (agentskills.io spec),
  the body under 500 lines, and the body free of agent-specific syntax (no `{baseDir}`,
  no `${CLAUDE_SKILL_DIR}`, no backtick-bang commands, no agent tool names).
- Target Manim Community v0.22.1; never ManimGL idioms.
- The container is the default render route (`scripts/render_in_container.py`, run through the
  `render-in-container.sh` and `.ps1` shims; defined by `docker/compose.yml` and
  `docker/Dockerfile`); `scripts/render.sh` is the host-native fallback. Keep both working. The
  wrapper is cross-platform (Linux, macOS, Windows): Python 3.9+, standard library only, no
  bash-isms in the shims. Anything else in `scripts/*.py` is baked into the image; the wrapper
  notices a changed source hash and rebuilds (`render_in_container.py` itself is host-only and
  excluded from the image and the hash). To change Python dependencies, edit
  `docker/requirements.in` and regenerate the hashed lock with
  `uv pip compile docker/requirements.in --python-version 3.12 --python-platform x86_64-manylinux_2_39 --generate-hashes -o docker/requirements.lock`;
  uv records the hashes of every wheel and sdist of each pinned version, so the same lock serves
  linux/arm64 (check that the resolved set has no x86-only markers). The Dockerfile builds for
  linux/amd64 and linux/arm64; keep amd64-only packages behind its `TARGETARCH` case.
  Never push the image anywhere; it is built locally.
- Defaults stay as they are unless measured better: 1080p60, Cairo, GPU off, serial
  (`workers` 1, `encoders` 1). Speed options and their measurements: `references/gpu-and-speed.md`.
- `.gitattributes` keeps LF for everything except `.ps1`/`.cmd`/`.bat`; do not add CRLF files.
- Re-run the checks: `python3 tests/validate_skill.py`, `python3 tests/test_wrapper.py` (wrapper and
  installer, no Docker; Windows path forms), `tests/test_container.sh` (end to end),
  `python3 tests/test_geometry.py` (the geometry checker must still catch the old unit-circle layout),
  `python3 tests/check_patterns.py` (renders every pattern in `references/scene-patterns.md` in
  the container; `--route host` for the host route), and render `tests/api_smoke.py` with
  `skills/manim-video/scripts/render.sh preview tests/api_smoke.py` (copy it under `out/` first).
- Render output goes under `out/` (git-ignored). Never commit MP4 files.
