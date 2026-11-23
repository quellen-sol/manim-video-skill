#!/usr/bin/env bash
# Profile where the time goes in one real render: per-frame Cairo drawing, animation Python,
# LaTeX/SVG/Text building, partial-movie encoding, concat, and the job's checks and stills.
#
# Usage: tests/profile_render.sh JOB_DIR [--quality preview|final] [--keep]
#   Copies JOB_DIR (scene, job.json, assets) to out/profile/<name>/, renders it with the normal
#   in-container job runner (manim-job render), with tests/profile/ on PYTHONPATH so the
#   `manim` process loads the stage timers, then prints a Markdown time split.
# Silent jobs only (the run has no network). Environment: MANIM_IMAGE (default manim-video:local).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
IMAGE="${MANIM_IMAGE:-manim-video:local}"
SRC="${1:?usage: tests/profile_render.sh JOB_DIR [--quality preview|final]}"; shift
QUALITY=final
while [ $# -gt 0 ]; do
  case "$1" in
    --quality) QUALITY="$2"; shift 2 ;;
    *) echo "unknown option $1" >&2; exit 2 ;;
  esac
done
SRC="$(cd "$SRC" && pwd -P)"
NAME="$(basename "$SRC")"
WORK="${PROFILE_DIR:-$ROOT/out/profile}/$NAME-$QUALITY"
rm -rf "$WORK"; mkdir -p "$WORK/out"
( cd "$SRC" && find . -maxdepth 1 -type f \( -name '*.py' -o -name '*.json' -o -name 'manim.cfg' \) -exec cp {} "$WORK/" \; )
[ -d "$SRC/assets" ] && cp -r "$SRC/assets" "$WORK/"
docker image inspect "$IMAGE" >/dev/null
echo "profile: $NAME, $QUALITY, image $IMAGE -> $WORK/out" >&2
t0=$(date +%s.%N)
docker run --rm --network none --user "$(id -u):$(id -g)" --read-only --tmpfs /tmp --cap-drop ALL \
  --security-opt no-new-privileges --init \
  -v "$WORK:/job:ro" -v "$WORK/out:/job/out" -v "$ROOT/tests/profile:/prof:ro" \
  -e PYTHONPATH=/prof:/opt/manim-video/scripts -e MANIM_PROFILE_OUT=/job/out/profile.json \
  "$IMAGE" render --quality "$QUALITY" > "$WORK/wrapper.log" 2>&1 || echo "render exit $?" >&2
t1=$(date +%s.%N)
python3 "$ROOT/tests/profile_report.py" "$WORK/out" "$(python3 -c "print($t1-$t0)")"
