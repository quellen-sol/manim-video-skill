#!/bin/sh
# Make the manim-video skill discoverable by agents by linking ONE canonical copy
# (skills/manim-video in this repo) into ~/.agents/skills and ~/.claude/skills.
# Thin shim for Linux, macOS, WSL2 and Git Bash: runs install.py (Python 3.9+, standard library
# only) with the same options. Windows PowerShell: install.ps1.
#
# Usage: ./install.sh [--openclaw] [--no-claude] [--no-agents] [--copy] [--force] [--uninstall] [--dry-run]
#        ./install.sh --help
DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd -P) || exit 1
CHECK='import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)'
for py in python3 python; do
  if command -v "$py" >/dev/null 2>&1 && "$py" -c "$CHECK" >/dev/null 2>&1; then
    exec "$py" "$DIR/install.py" "$@"
  fi
done
# Git Bash on Windows: the python.org installer provides the py launcher
if command -v py >/dev/null 2>&1 && py -3 -c "$CHECK" >/dev/null 2>&1; then
  exec py -3 "$DIR/install.py" "$@"
fi
echo "install.sh: needs Python 3.9 or newer as python3 on PATH" >&2
exit 1
