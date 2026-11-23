#!/bin/sh
# Render a manim-video job in the render container (the default render path).
# Thin shim for Linux, macOS, WSL2 and Git Bash: runs render_in_container.py (Python 3.9+,
# standard library only) with the same arguments. Usage: render-in-container.sh --help
# Windows PowerShell: render-in-container.ps1 (same arguments).
DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd -P) || exit 3
CHECK='import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)'
for py in python3 python; do
  if command -v "$py" >/dev/null 2>&1 && "$py" -c "$CHECK" >/dev/null 2>&1; then
    exec "$py" "$DIR/render_in_container.py" "$@"
  fi
done
# Git Bash on Windows: the python.org installer provides the py launcher
if command -v py >/dev/null 2>&1 && py -3 -c "$CHECK" >/dev/null 2>&1; then
  exec py -3 "$DIR/render_in_container.py" "$@"
fi
echo "render-in-container: needs Python 3.9 or newer as python3 on PATH" >&2
exit 3
