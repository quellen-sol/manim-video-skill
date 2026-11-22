#!/usr/bin/env bash
# Make the manim-video skill discoverable by agents, by symlinking ONE canonical copy
# (skills/manim-video in this repo). No copies, no edits to any agent's config.
#
# Usage: ./install.sh [--openclaw] [--no-claude] [--no-agents] [--force] [--uninstall] [--dry-run]
#
# Default links:
#   ~/.agents/skills/manim-video  -> Codex CLI and OpenClaw read this directory natively;
#                                    Hermes reads it once you add it to skills.external_dirs.
#   ~/.claude/skills/manim-video  -> Claude Code.
# Options:
#   --openclaw   also link ~/.openclaw/skills/manim-video (only if your OpenClaw does not read
#                ~/.agents/skills; with both, OpenClaw sees the same skill twice)
#   --no-claude  skip ~/.claude/skills       --no-agents  skip ~/.agents/skills
#   --force      replace an existing symlink that points somewhere else (never a real directory)
#   --uninstall  remove only links that point to this repo's skill
#   --dry-run    print what would happen
set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)/skills/manim-video"
NAME="manim-video"
[ -f "$SRC/SKILL.md" ] || { echo "install.sh: $SRC/SKILL.md not found" >&2; exit 1; }

AGENTS=1; CLAUDE=1; OPENCLAW=0; FORCE=0; UNINSTALL=0; DRY=0
for a in "$@"; do
  case "$a" in
    --openclaw) OPENCLAW=1 ;;
    --no-claude) CLAUDE=0 ;;
    --no-agents) AGENTS=0 ;;
    --force) FORCE=1 ;;
    --uninstall) UNINSTALL=1 ;;
    --dry-run) DRY=1 ;;
    -h|--help) sed -n '2,21p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "install.sh: unknown option $a" >&2; exit 2 ;;
  esac
done

run() { if [ $DRY -eq 1 ]; then echo "  (dry run) $*"; else "$@"; fi; }

TARGETS=()
[ $AGENTS -eq 1 ] && TARGETS+=("$HOME/.agents/skills")
[ $CLAUDE -eq 1 ] && TARGETS+=("$HOME/.claude/skills")
[ $OPENCLAW -eq 1 ] && TARGETS+=("$HOME/.openclaw/skills")

RC=0
for dir in "${TARGETS[@]}"; do
  link="$dir/$NAME"
  if [ $UNINSTALL -eq 1 ]; then
    if [ -L "$link" ] && [ "$(readlink -f "$link")" = "$SRC" ]; then
      echo "remove  $link"; run rm "$link"
    elif [ -e "$link" ] || [ -L "$link" ]; then
      echo "keep    $link (not a link to this repo; left alone)"
    else
      echo "absent  $link"
    fi
    continue
  fi
  if [ -L "$link" ]; then
    if [ "$(readlink -f "$link")" = "$SRC" ]; then echo "ok      $link -> $SRC (already linked)"; continue; fi
    if [ $FORCE -eq 1 ]; then echo "relink  $link (was -> $(readlink "$link"))"; run ln -sfn "$SRC" "$link"; continue; fi
    echo "SKIP    $link points to $(readlink "$link"); use --force to replace it" >&2; RC=1; continue
  fi
  if [ -e "$link" ]; then
    echo "SKIP    $link exists and is not a symlink; not touching it" >&2; RC=1; continue
  fi
  [ -d "$dir" ] || { echo "mkdir   $dir"; run mkdir -p "$dir"; }
  echo "link    $link -> $SRC"; run ln -s "$SRC" "$link"
done

if [ $UNINSTALL -eq 0 ]; then
  cat <<EOF

Hermes Agent (not changed by this script): add the shared directory to ~/.hermes/config.yaml
  skills:
    external_dirs:
      - ~/.agents/skills
Hermes may edit skills in external dirs in place; consider skills.write_approval: true.

Next: run the toolchain check (installs nothing):
  $SRC/scripts/check_env.sh
and, if it reports NOT READY, the user-space setup (no sudo):
  $SRC/scripts/setup_env.sh
EOF
fi
exit $RC
