# Agent notes for this repo

This repo holds one cross-agent skill: `skills/manim-video/` (entry point `skills/manim-video/SKILL.md`).
It is symlinked into agent skill directories by `install.sh`; there are no per-agent copies.

When you change the skill:

- Keep `SKILL.md` frontmatter to `name`, `description`, `license`, `compatibility` (agentskills.io spec),
  the body under 500 lines, and the body free of agent-specific syntax (no `{baseDir}`,
  no `${CLAUDE_SKILL_DIR}`, no backtick-bang commands, no agent tool names).
- Target Manim Community v0.22.1; never ManimGL idioms.
- Re-run the checks: `python3 tests/validate_skill.py`, `python3 tests/check_patterns.py`
  (renders every pattern in `references/scene-patterns.md`), and render `tests/api_smoke.py`
  with `skills/manim-video/scripts/render.sh preview tests/api_smoke.py` (copy it under `out/` first).
- Render output goes under `out/` (git-ignored). Never commit MP4 files.
