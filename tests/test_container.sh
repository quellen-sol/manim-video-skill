#!/usr/bin/env bash
# End-to-end test of the container route. Run from anywhere; needs Docker. About 3 minutes once
# the image is built (the first build takes about 6 minutes).
#
#   tests/test_container.sh [--no-tts] [--no-gpu]
#
# Checks: the image builds and is current; a silent preview with Text, MathTex, Tex and Axes
# renders (CPU default, network none) with video, report and stills owned by the caller; --frames
# and --still work; a narrated job reaches Kokoro from inside the container (voiceover and mux
# modes) without the key appearing in any output; the image refuses root; bad job.json and
# ManimGL code are rejected; a GPU-override run sees the render node (if the host has one);
# no containers or networks are left behind.
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
R="$ROOT/skills/manim-video/scripts/render-in-container.sh"
WORK="$ROOT/out/test-container"
IMAGE="${MANIM_IMAGE:-manim-video:local}"
TTS=1; GPU=1
for a in "$@"; do case "$a" in --no-tts) TTS=0 ;; --no-gpu) GPU=0 ;; *) echo "unknown option $a" >&2; exit 2 ;; esac; done

PASS=0; FAIL=0
pass() { printf 'PASS  %s\n' "$*"; PASS=$((PASS+1)); }
fail() { printf 'FAIL  %s\n' "$*"; FAIL=$((FAIL+1)); }
skip() { printf 'SKIP  %s\n' "$*"; }
field() { python3 -c "import json,sys; print(json.load(open(sys.argv[1])).get(sys.argv[2], ''))" "$@"; }

rm -rf "$WORK"; mkdir -p "$WORK"
cp -r "$ROOT/tests/jobs/smoke" "$ROOT/tests/jobs/narrated" "$ROOT/tests/jobs/mux" "$WORK/"
containers_before="$(docker ps -aq --filter label=com.docker.compose.service=manim | wc -l)"
networks_before="$(docker network ls -q | sort | tr '\n' ' ')"

# 1. image
if "$R" --build >/dev/null 2>&1 && "$R" --status >/dev/null; then pass "image builds and is current: $("$R" --status)"
else fail "image build"; fi

# 2. silent preview on the CPU default
out="$("$R" "$WORK/smoke" 2>&1)"; rc=$?
if [ $rc -eq 0 ] && [ -f "$WORK/smoke/out/Smoke-preview.mp4" ]; then pass "smoke preview renders (exit 0)"; else fail "smoke preview (exit $rc): $(printf '%s' "$out" | tail -3)"; fi
grep -q "network none" <<<"$out" && grep -q "GPU off" <<<"$out" && pass "default job: GPU off, network none" || fail "default job isolation"
[ "$(field "$WORK/smoke/out/summary.json" checks)" = PASS ] && pass "smoke checks PASS" || fail "smoke checks: $(field "$WORK/smoke/out/summary.json" checks)"
ls "$WORK"/smoke/out/stills/sheet_*.png >/dev/null 2>&1 && pass "contact sheets written" || fail "no contact sheets"
grep -q "LayoutGuard: active" "$WORK/smoke/out/report.md" && pass "LayoutGuard ran" || fail "LayoutGuard did not run"
grep -q "MathTex\|Tex(" "$WORK/smoke/scene.py" && ! grep -qi "latex error" "$WORK/smoke/out/render.log" && pass "MathTex/Tex compiled (LaTeX in the image)" || fail "LaTeX"
owner="$(stat -c %u:%g "$WORK/smoke/out/Smoke-preview.mp4")"
[ "$owner" = "$(id -u):$(id -g)" ] && pass "output owned by the caller ($owner)" || fail "output owner $owner"
[ "$(stat -c %a "$WORK/smoke/scene.py")" = "$(stat -c %a "$ROOT/tests/jobs/smoke/scene.py")" ] && pass "job sources untouched" || fail "job sources changed"

# 3. --frames and --still
"$R" "$WORK/smoke" --frames --at 3,9 >/dev/null 2>&1 && [ "$(ls "$WORK"/smoke/out/frames/frame_*.png 2>/dev/null | wc -l)" -eq 2 ] \
  && pass "--frames --at extracts stills without re-rendering" || fail "--frames"
"$R" "$WORK/smoke" --still 2 >/dev/null 2>&1 && ls "$WORK"/smoke/out/stills-full/anim_2-*.png >/dev/null 2>&1 \
  && [ "$(python3 -c "import struct,sys; d=open(sys.argv[1],'rb').read(24); print(struct.unpack('>II', d[16:24]))" "$(ls "$WORK"/smoke/out/stills-full/anim_2-*.png | head -1)")" = "(1920, 1080)" ] \
  && pass "--still 2 renders a 1920x1080 PNG" || fail "--still"

# 4. rejections
printf '{"scene": "Smoke", "qualty": "final"}\n' > "$WORK/smoke/job.json"
"$R" "$WORK/smoke" >/dev/null 2>&1; rc=$?
[ $rc -eq 2 ] && pass "job.json typo rejected (exit 2)" || fail "job.json typo: exit $rc"
mkdir -p "$WORK/gl"; printf 'from manim import *\nclass S(Scene):\n    def construct(self):\n        self.play(ShowCreation(Circle()))\n' > "$WORK/gl/scene.py"
printf '{"scene": "S"}\n' > "$WORK/gl/job.json"
out="$("$R" "$WORK/gl" 2>&1)"; rc=$?
[ $rc -eq 2 ] && grep -q "ManimGL" <<<"$out" && pass "ManimGL idiom refused (exit 2)" || fail "ManimGL refusal: exit $rc"
out="$(docker run --rm --user 0:0 "$IMAGE" render 2>&1)"; rc=$?
[ $rc -eq 3 ] && grep -q "refusing to run as root" <<<"$out" && pass "image refuses uid 0 (exit 3)" || fail "root refusal: exit $rc"
out="$(docker run --rm --user 1000:0 "$IMAGE" doctor 2>&1)"; rc=$?
[ $rc -eq 3 ] && pass "image refuses gid 0 (exit 3)" || fail "gid 0 refusal: exit $rc"

# 5. narration from inside the container
if [ $TTS -eq 1 ] && curl -s -o /dev/null --max-time 5 http://127.0.0.1:8880/v1/models; then
  out="$("$R" "$WORK/narrated" 2>&1)"; rc=$?
  if [ $rc -eq 0 ] && grep -q "network bridge" <<<"$out" && grep -q "1 audio stream" "$WORK/narrated/out/report.md"; then
    pass "narrated job (voiceover + KokoroService) reaches Kokoro from the container; audio present"
  else fail "narrated job (exit $rc): $(printf '%s' "$out" | tail -3)"; fi
  out="$("$R" "$WORK/mux" 2>&1)"; rc=$?
  if [ $rc -eq 0 ] && grep -q "1 audio stream" "$WORK/mux/out/report.md"; then pass "mux-mode narration renders with audio"
  else fail "mux job (exit $rc): $(printf '%s' "$out" | tail -3)"; fi
  envfile="${KOKORO_ENV_FILE:-$HOME/.config/agent-stack/gateway.env}"
  key="${KOKORO_API_KEY:-$( [ -r "$envfile" ] && sed -n -E 's/^(export[[:space:]]+)?KOKORO_API_KEY=//p' "$envfile" | tail -n 1 | tr -d "\"'")}"
  if [ -n "$key" ]; then
    if grep -rqF -- "Bearer $key" "$WORK"; then fail "the key appears in job output"; else pass "no bearer token in any job output"; fi
  else skip "no KOKORO_API_KEY available; key-leak check skipped"; fi
  unset key
else
  skip "Kokoro not reachable at 127.0.0.1:8880 (or --no-tts); narration tests skipped"
fi

# 6. GPU override
if [ $GPU -eq 1 ] && ls /dev/dri/renderD* >/dev/null 2>&1; then
  out="$("$R" --doctor --gpu 2>&1)"
  grep -q "dri nodes    \['/dev/dri/renderD" <<<"$out" && pass "GPU override: render node visible ($(grep '^opengl' <<<"$out" | sed 's/  */ /g'))" || fail "GPU override doctor"
  cp -r "$ROOT/tests/jobs/smoke" "$WORK/smoke-gpu"
  out="$("$R" "$WORK/smoke-gpu" --gpu 2>&1)"; rc=$?
  [ $rc -eq 0 ] && grep -q "GPU on" <<<"$out" && pass "GPU-override render (compose.gpu.yml)" || fail "GPU render (exit $rc)"
else
  skip "no /dev/dri render node (or --no-gpu); GPU override not tested"
fi

# 7. nothing left behind
containers_after="$(docker ps -aq --filter label=com.docker.compose.service=manim | wc -l)"
[ "$containers_after" -eq "$containers_before" ] && pass "no stray containers" || fail "stray containers: $containers_after (before: $containers_before)"
[ "$(docker network ls -q | sort | tr '\n' ' ')" = "$networks_before" ] && pass "no new networks" || fail "network list changed"

echo
echo "test_container: $PASS passed, $FAIL failed"
[ $FAIL -eq 0 ]
