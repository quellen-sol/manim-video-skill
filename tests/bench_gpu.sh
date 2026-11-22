#!/usr/bin/env bash
# Benchmark the render container on this host, through the real job path (render-in-container.sh):
#   a) Cairo renderer, CPU only and with the GPU passed in
#   b) OpenGL renderer headless via EGL: llvmpipe (CPU) and the iGPU (Mesa iris)
#   c) post-render H.264 encode: libx264 vs h264_vaapi, plus libx264 at Manim's own settings
#   d) parity: the same scene rendered by a host-native Manim (if MANIM_HOST_BIN is set)
# Every render starts from an empty out/ (no Manim cache). Prints a Markdown report.
#
# Usage: tests/bench_gpu.sh [REPS]          (default 2; run on a quiet host)
# Environment: RENDER (wrapper path), BENCH_SCENE (scene file), BENCH_DIR (work dir),
#              MANIM_HOST_BIN (host manim for the parity run, e.g. ~/.local/share/manim-video/venv/bin/manim)
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
RENDER="${RENDER:-$ROOT/skills/manim-video/scripts/render-in-container.sh}"
SCENE="${BENCH_SCENE:-$ROOT/tests/jobs/bench/scene.py}"
WORK="${BENCH_DIR:-$ROOT/out/bench}"
IMAGE="${MANIM_IMAGE:-manim-video:local}"
REPS="${1:-2}"
mkdir -p "$WORK"

mb() { stat -c %s "$1" | awk '{printf "%.2f", $1/1e6}'; }
field() { python3 -c "import json,sys; d=json.load(open(sys.argv[1])); print(eval(sys.argv[2], {}, {'d': d}))" "$@"; }

# run NAME JSON  -> prints render seconds; keeps the job dir for later steps
run_job() {
  local name="$1" json="$2" dir="$WORK/$1"
  mkdir -p "$dir"; cp "$SCENE" "$dir/scene.py"; printf '%s\n' "$json" > "$dir/job.json"
  rm -rf "$dir/out"
  "$RENDER" "$dir" --no-build >"$dir.log" 2>&1 || { echo "FAILED: $name (see $dir.log)" >&2; return 1; }
}

declare -A RES
row() {  # NAME JSON LABEL
  local name="$1" json="$2" label="$3" times=() t frames gl
  for i in $(seq 1 "$REPS"); do
    run_job "$name" "$json"
    t="$(field "$WORK/$name/out/summary.json" "d['timings']['render']")"
    times+=("$t")
  done
  frames="$(field "$WORK/$name/out/report.json" "round(d['duration'] * $(field "$WORK/$name/out/summary.json" "d['fps']"))")"
  gl="$(field "$WORK/$name/out/summary.json" "d['gpu'].get('gl_renderer', '-')")"
  RES[$name]="$(python3 -c "
import sys, statistics as s
ts = [float(x) for x in sys.argv[1:-1]]; fr = int(sys.argv[-1])
print(f'{s.median(ts):.1f}|{\" / \".join(f\"{t:.1f}\" for t in ts)}|{fr / s.median(ts):.1f}')" "${times[@]}" "$frames")"
  IFS='|' read -r med all fps <<< "${RES[$name]}"
  echo "| $label | $gl | $frames | $med ($all) | $fps |"
}

echo "## Render benchmark ($(date -u +%Y-%m-%dT%H:%MZ), $(grep -m1 'model name' /proc/cpuinfo | cut -d: -f2- | xargs), $(nproc) cores, $REPS runs each, median (all))"
echo
echo "| Configuration | OpenGL device | Frames | Render s | Frames/s |"
echo "|---|---|---|---|---|"
row cairo-preview '{"scene":"Bench","quality":"preview","stills":"none"}' "Cairo, preview 854x480@15, CPU"
row cairo-cpu     '{"scene":"Bench","quality":"final","stills":"none"}' "Cairo, final 1080p60, CPU"
row cairo-gpu     '{"scene":"Bench","quality":"final","gpu":true,"stills":"none"}' "Cairo, final 1080p60, GPU passed in"
row gl-cpu        '{"scene":"Bench","quality":"final","renderer":"opengl","stills":"none"}' "OpenGL, final 1080p60, EGL on CPU"
row gl-gpu        '{"scene":"Bench","quality":"final","renderer":"opengl","gpu":true,"stills":"none"}' "OpenGL, final 1080p60, EGL on iGPU"

# c) encoders, on the cached Cairo final render (the render step is a cache hit here).
SRC_DIR="$WORK/cairo-cpu"
SRC_REL="$(field "$SRC_DIR/out/summary.json" "d['media_video']")"   # out/media/... (Manim's own file)
echo
echo "## Post-render H.264 encode of the 1080p60 Cairo render ($REPS runs each)"
echo
echo "| Encoder | Settings | Encode s | Size MB | SSIM vs Manim's file |"
echo "|---|---|---|---|---|"
enc_row() {  # ENCODER GPU LABEL SETTINGS
  local enc="$1" gpu="$2" times=() t
  for i in $(seq 1 "$REPS"); do
    printf '{"scene":"Bench","quality":"final","gpu":%s,"encode":"%s","stills":"none"}\n' "$gpu" "$enc" > "$SRC_DIR/job.json"
    "$RENDER" "$SRC_DIR" --no-build >"$SRC_DIR-$enc.log" 2>&1 || { echo "FAILED: encode $enc" >&2; return 1; }
    times+=("$(field "$SRC_DIR/out/summary.json" "d['timings']['encode']")")
  done
  cp "$SRC_DIR/out/Bench-final.mp4" "$WORK/enc-$enc.mp4"
  local size ssim
  size="$(mb "$WORK/enc-$enc.mp4")"
  ssim="$(docker run --rm --network none --user "$(id -u):$(id -g)" -v "$WORK:/w:ro" "$IMAGE" exec \
          ffmpeg -hide_banner -nostats -i "/w/enc-$enc.mp4" -i "/w/cairo-cpu/$SRC_REL" -lavfi ssim -f null - 2>&1 \
          | sed -n 's/.*All:\([0-9.]*\).*/\1/p' | tail -1)"
  echo "| $3 | $4 | $(python3 -c "import sys,statistics as s; ts=[float(x) for x in sys.argv[1:]]; print(f'{s.median(ts):.1f} (' + ' / '.join(f'{t:.1f}' for t in ts) + ')')" "${times[@]}") | $size | $ssim |"
}
manim_size="$(mb "$SRC_DIR/$SRC_REL")"
echo "| (Manim's own output) | libx264 CRF 23, inside the render | - | $manim_size | 1 |"
enc_row libx264 false "libx264 (CPU)" "CRF 20, preset medium"
enc_row h264_vaapi true "h264_vaapi (iGPU)" "QP 20, low-power VDEnc"
# Manim's own encoder settings, timed standalone, to show what share of a render is encoding.
t0=$(date +%s.%N)
docker run --rm --network none --user "$(id -u):$(id -g)" -v "$WORK:/w" "$IMAGE" exec \
  ffmpeg -y -hide_banner -nostats -loglevel error -i "/w/cairo-cpu/$SRC_REL" -c:v libx264 -crf 23 -preset medium -pix_fmt yuv420p /w/enc-manim-settings.mp4
t1=$(date +%s.%N)
echo "| libx264 (CPU) | CRF 23, preset medium (Manim's settings), standalone | $(python3 -c "print(f'{$t1-$t0:.1f}')") | $(mb "$WORK/enc-manim-settings.mp4") | - |"

# d) parity: OpenGL vs Cairo output, and host-native vs container.
echo
echo "## Output parity (SSIM, 1 = identical)"
echo
GL_REL="$(field "$WORK/gl-gpu/out/summary.json" "d['media_video']")"
s_gl="$(docker run --rm --network none --user "$(id -u):$(id -g)" -v "$WORK:/w:ro" "$IMAGE" exec \
        ffmpeg -hide_banner -nostats -i "/w/gl-gpu/$GL_REL" -i "/w/cairo-cpu/$SRC_REL" -lavfi ssim -f null - 2>&1 | sed -n 's/.*All:\([0-9.]*\).*/\1/p' | tail -1)"
echo "- OpenGL (iGPU) vs Cairo, same scene: SSIM $s_gl"
if [ -n "${MANIM_HOST_BIN:-}" ]; then
  H="$WORK/host"; rm -rf "$H"; mkdir -p "$H"; cp "$SCENE" "$H/scene.py"
  t0=$(date +%s.%N)
  (cd "$H" && "$MANIM_HOST_BIN" render -qh --format mp4 --progress_bar none --media_dir "$H/media" scene.py Bench >"$H.log" 2>&1)
  t1=$(date +%s.%N)
  HV="$(find "$H/media/videos" -name Bench.mp4 -not -path '*partial*' | head -1)"
  s_host="$(ffmpeg -hide_banner -nostats -i "$HV" -i "$SRC_DIR/$SRC_REL" -lavfi ssim -f null - 2>&1 | sed -n 's/.*All:\([0-9.]*\).*/\1/p' | tail -1)"
  echo "- Host-native Manim (same lock file) vs container, Cairo final: SSIM $s_host; host render $(python3 -c "print(f'{$t1-$t0:.1f}')") s wall (container: ${RES[cairo-cpu]%%|*} s)"
fi
