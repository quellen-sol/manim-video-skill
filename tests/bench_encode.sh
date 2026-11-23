#!/usr/bin/env bash
# Post-render hardware encode on this host: re-encode one finished video with libx264 (Manim's
# settings) and the GPU encoders the image has, then report time, size and SSIM against the input.
# Usage: tests/bench_encode.sh VIDEO.mp4      (Linux with /dev/dri; run on a quiet host)
# Environment: MANIM_IMAGE (default manim-video:local).
set -uo pipefail
IMAGE="${MANIM_IMAGE:-manim-video:local}"
SRC="$(realpath "${1:?usage: tests/bench_encode.sh VIDEO.mp4}")"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/manim-encode.XXXXXX")"; trap 'rm -rf "$WORK"' EXIT
cp "$SRC" "$WORK/in.mp4"
NODE="$(ls /dev/dri/renderD* 2>/dev/null | head -1)"
GPU=(); [ -n "$NODE" ] && GPU=(--device /dev/dri --group-add "$(stat -c %g "$NODE")" --group-add "$(stat -c %g "$(ls /dev/dri/card* | head -1)")")
run() { docker run --rm --network none --user "$(id -u):$(id -g)" "${GPU[@]}" -v "$WORK:/w" "$IMAGE" exec "$@"; }
mb() { stat -c %s "$1" | awk '{printf "%.1f", $1/1e6}'; }
echo "Input: $(basename "$SRC"), $(mb "$WORK/in.mp4") MB"
echo
echo "| Encoder | Settings | Encode s | Size MB | SSIM vs input |"
echo "|---|---|---|---|---|"
enc() {  # LABEL SETTINGS OUTNAME ffmpeg-args...
  local label="$1" settings="$2" out="$3"; shift 3
  local t0 t1 err
  t0=$(date +%s.%N)
  err="$(run ffmpeg -y -hide_banner -nostats -loglevel error "$@" "/w/$out" 2>&1)"
  t1=$(date +%s.%N)
  if [ ! -s "$WORK/$out" ]; then echo "| $label | $settings | failed: $(printf '%s' "$err" | tr '\n' ' ' | cut -c1-120) | - | - |"; return; fi
  local ssim
  ssim="$(run ffmpeg -hide_banner -nostats -i "/w/$out" -i /w/in.mp4 -lavfi ssim -f null - 2>&1 | sed -n 's/.*All:\([0-9.]*\).*/\1/p' | tail -1)"
  echo "| $label | $settings | $(python3 -c "print(f'{$t1-$t0:.1f}')") | $(mb "$WORK/$out") | $ssim |"
  rm -f "$WORK/$out"
}
enc "libx264 (CPU)" "CRF 23, preset medium (Manim's own settings)" x264.mp4 -i /w/in.mp4 -c:v libx264 -crf 23 -preset medium -pix_fmt yuv420p
if [ -n "$NODE" ]; then
  VA=(-vaapi_device "$NODE" -i /w/in.mp4 -vf "format=nv12,hwupload")
  enc "h264_vaapi (iGPU)" "QP 20 (the job's \"encode\": \"h264_vaapi\")" va20.mp4 "${VA[@]}" -c:v h264_vaapi -qp 20
  enc "h264_vaapi (iGPU)" "QP 26" va26.mp4 "${VA[@]}" -c:v h264_vaapi -qp 26
  enc "h264_vaapi (iGPU)" "QP 30" va30.mp4 "${VA[@]}" -c:v h264_vaapi -qp 30
  enc "hevc_vaapi (iGPU)" "QP 26" hevc26.mp4 "${VA[@]}" -c:v hevc_vaapi -qp 26
  enc "h264_qsv (iGPU)" "global_quality 23" qsv.mp4 -init_hw_device "qsv=hw:$NODE" -i /w/in.mp4 -c:v h264_qsv -global_quality 23
else
  echo "| (GPU encoders) | no /dev/dri render node on this host | - | - | - |"
fi
