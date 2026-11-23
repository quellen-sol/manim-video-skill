#!/usr/bin/env bash
# Measure render-speed options on one real job, through the normal container route:
# serial (the default), Manim's max_inflight_encoders ("encoders"), and parallel sections
# ("workers"). Every run starts from an empty out/ (no Manim cache). For each run it checks that
# the delivered video decodes to exactly the same frames as the first (serial) run.
#
# Usage: tests/bench_parallel.sh JOB_DIR [QUALITY] [CONFIG ...]
#   CONFIG is comma-separated job.json overrides, e.g. "workers=4,encoders=4" or "fps=30" (default
#   set: serial, encoders 4, workers 2 and 4, each with encoders 1 and 4); the first config is the
#   baseline. Run on a quiet host; prints a Markdown table.
# Environment: MANIM_IMAGE (default manim-video:local), BENCH_DIR (default out/bench-parallel).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
RENDER="${RENDER:-$ROOT/skills/manim-video/scripts/render-in-container.sh}"
IMAGE="${MANIM_IMAGE:-manim-video:local}"
SRC="$(cd "${1:?usage: tests/bench_parallel.sh JOB_DIR [QUALITY] [CONFIG ...]}" && pwd -P)"; shift
QUALITY="${1:-final}"; [ $# -gt 0 ] && shift
CONFIGS=("$@")
[ ${#CONFIGS[@]} -gt 0 ] || CONFIGS=("workers=1,encoders=1" "workers=1,encoders=4" "workers=2,encoders=1"
                                     "workers=4,encoders=1" "workers=2,encoders=4" "workers=4,encoders=4")
NAME="$(basename "$SRC")"
WORK="${BENCH_DIR:-$ROOT/out/bench-parallel}/$NAME-$QUALITY"
mkdir -p "$WORK"

frames() {  # decoded-frame md5 list of a video
  docker run --rm --network none --user "$(id -u):$(id -g)" -v "$(dirname "$1"):/v:ro" "$IMAGE" exec \
    ffmpeg -v error -i "/v/$(basename "$1")" -map 0:v:0 -f framemd5 - | grep -v '^#' | awk -F, '{print $6}'
}

echo "## Render speed options: $NAME, $QUALITY ($(date -u +%Y-%m-%dT%H:%MZ), $(grep -m1 'model name' /proc/cpuinfo | cut -d: -f2- | xargs), $(nproc) cores)"
echo
echo "| Config | Render s | Checks s | Job total s | Render speedup | Same frames as baseline | Notes |"
echo "|---|---|---|---|---|---|---|"
BASE_RENDER=""; BASE_FRAMES=""
for cfg in "${CONFIGS[@]}"; do
  dir="$WORK/$(tr -c 'a-zA-Z0-9\n' '_' <<< "$cfg")"
  rm -rf "$dir"; mkdir -p "$dir"
  ( cd "$SRC" && find . -maxdepth 1 -type f \( -name '*.py' -o -name '*.json' -o -name 'manim.cfg' \) -exec cp {} "$dir/" \; )
  [ -d "$SRC/assets" ] && cp -r "$SRC/assets" "$dir/"
  python3 - "$dir/job.json" "$QUALITY" "$cfg" <<'PY'
import json, sys
p, q, cfg = sys.argv[1], sys.argv[2], sys.argv[3]
d = json.load(open(p)); d["quality"] = q
for kv in filter(None, cfg.split(",")):
    k, v = kv.split("=", 1)
    d[k] = int(v) if v.isdigit() else v
json.dump(d, open(p, "w"), indent=1)
PY
  rc=0; MANIM_IMAGE="$IMAGE" "$RENDER" "$dir" --no-build > "$dir.log" 2>&1 || rc=$?
  read -r render checks total note < <(python3 - "$dir/out/summary.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1])); t = d.get("timings", {}); p = d.get("parallel") or {}
note = []
if p: note.append(f"{p.get('workers')} workers, ranges {p.get('ranges')}, seams {'ok' if all(s['match'] for s in p.get('seams', [])) else p.get('reason')}; plan {p.get('timings', {}).get('plan')} s, workers {p.get('worker_secs')}")
if d.get("warnings"): note.append("; ".join(d["warnings"]))
note.append(f"checks {d.get('checks')}, geometry {d.get('geometry', {}).get('status')}")
print(t.get("render", 0), t.get("checks", 0), t.get("total", 0), " / ".join(note).replace(" ", " "))
PY
)
  video="$(ls "$dir"/out/*.mp4 | head -1)"
  frames "$video" > "$dir.frames"
  if [ -z "$BASE_RENDER" ]; then BASE_RENDER="$render"; BASE_FRAMES="$dir.frames"; same="baseline ($(wc -l < "$dir.frames") frames)"
  else
    nd="$(paste -d' ' "$BASE_FRAMES" "$dir.frames" | awk '$1!=$2' | wc -l)"
    [ "$(wc -l < "$BASE_FRAMES")" = "$(wc -l < "$dir.frames")" ] && [ "$nd" = 0 ] && same="yes" || same="NO ($nd differ)"
  fi
  speed="$(python3 -c "print(f'{$BASE_RENDER/$render:.2f}x')")"
  echo "| $cfg (exit $rc) | $render | $checks | $total | $speed | $same | ${note//$' '/ } |"
done
