#!/usr/bin/env bash
# Check that everything the manim-video skill needs is present. Read-only; installs nothing.
#
# Usage: check_env.sh [--tts]     (--tts also synthesizes one short test clip with Kokoro)
#
# Checks: render backend (Docker image or local Manim Community), Manim version, Python >= 3.11,
# LaTeX + dvisvgm, manim-voiceover, host ffmpeg/ffprobe (for frames.py and qa_check.py), host
# python3 >= 3.11 (for the helper scripts), and Kokoro TTS reachability.
# Exit status: 0 if silent rendering works, 1 if not. Narration problems are reported as WARN.
set -uo pipefail
# shellcheck source=_env.sh
. "$(dirname "${BASH_SOURCE[0]}")/_env.sh"

TTS_TEST=0; [ "${1:-}" = "--tts" ] && TTS_TEST=1
FAILS=0; WARNS=0
ok()   { printf '  OK    %s\n' "$*"; }
warn() { printf '  WARN  %s\n' "$*"; WARNS=$((WARNS+1)); }
fail() { printf '  FAIL  %s\n' "$*"; FAILS=$((FAILS+1)); }

pyver_ok() { "$1" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null; }

echo "manim-video environment check (skill: $SKILL_DIR)"

echo "[host helpers]"
if have python3 && pyver_ok python3; then ok "python3 $(python3 -c 'import platform; print(platform.python_version())')"
else fail "python3 >= 3.11 not found (needed by frames.py, qa_check.py, narrate_mux.py)"; fi
for t in ffmpeg ffprobe; do
  if works "$t"; then ok "$t: $(command -v "$t") ($("$t" -version 2>/dev/null | head -1 | awk '{print $3}'))"
  elif have "$t"; then fail "$t at $(command -v "$t") does not run (broken install?); run scripts/setup_env.sh for a static build"
  else fail "$t not found (run scripts/setup_env.sh to fetch a static build into $MANIM_VIDEO_HOME/bin)"; fi
done

echo "[renderer]"
BACKEND="$(resolve_backend)"
RUN=()
if [ -z "$BACKEND" ]; then
  fail "no renderer: no local Manim Community and no usable Docker (MANIM_BACKEND=$MANIM_BACKEND)"
elif [ "$BACKEND" = docker ]; then
  IMAGE="$(resolve_image)"
  if [ -z "$IMAGE" ]; then
    fail "Docker works but neither $MANIM_IMAGE nor $MANIM_BASE_IMAGE is present (run scripts/setup_env.sh)"
  else
    ok "backend: docker, image $IMAGE"
    [ "$IMAGE" = "$MANIM_IMAGE" ] || warn "using the base image; narration needs $MANIM_IMAGE (scripts/setup_env.sh)"
    RUN=(docker run --rm --network none -e HOME=/tmp "$IMAGE")
  fi
else
  ok "backend: local ($(command -v manim))"
  RUN=(env)
fi

if [ ${#RUN[@]} -gt 0 ]; then
  REPORT="$("${RUN[@]}" sh -c '
    manim --version 2>/dev/null | head -1
    python3 -c "import sys; print(\"python\", sys.version.split()[0])" 2>/dev/null || python -c "import sys; print(\"python\", sys.version.split()[0])"
    command -v latex >/dev/null && echo "latex yes" || echo "latex no"
    command -v dvisvgm >/dev/null && echo "dvisvgm yes" || echo "dvisvgm no"
    python3 -c "import manim_voiceover" 2>/dev/null && echo "voiceover yes" || echo "voiceover no"
  ' 2>/dev/null)"
  MV="$(printf '%s\n' "$REPORT" | grep -m1 'Manim Community' || true)"
  if [ -n "$MV" ]; then
    case "$MV" in *"v$MANIM_VERSION"*) ok "$MV" ;; *) warn "$MV (skill is written for v$MANIM_VERSION)" ;; esac
  else fail "manim did not run in the renderer"; fi
  PV="$(printf '%s\n' "$REPORT" | sed -n 's/^python //p')"
  case "$PV" in 3.1[1-9]*|3.[2-9][0-9]*) ok "renderer python $PV" ;; *) fail "renderer python ${PV:-missing} (need >= 3.11)" ;; esac
  if printf '%s\n' "$REPORT" | grep -q 'latex yes' && printf '%s\n' "$REPORT" | grep -q 'dvisvgm yes'; then
    ok "LaTeX + dvisvgm (MathTex/Tex available)"
  else
    warn "LaTeX or dvisvgm missing in the renderer: use Text/MarkupText instead of MathTex/Tex, or the Docker backend"
  fi
  if printf '%s\n' "$REPORT" | grep -q 'voiceover yes'; then ok "manim-voiceover installed"
  else warn "manim-voiceover missing in the renderer: narration must use narrate_mux.py (fallback)"; fi
fi

echo "[narration: Kokoro at $KOKORO_BASE_URL, model $KOKORO_MODEL, voice $KOKORO_VOICE]"
if [ -n "${KOKORO_API_KEY:-}" ]; then ok "KOKORO_API_KEY is set (value not shown)"
else echo "  INFO  KOKORO_API_KEY is not set (fine if the server needs no key)"; fi
# The key goes to curl through a file descriptor, so it never appears in a process listing.
kcurl() {
  if [ -n "${KOKORO_API_KEY:-}" ]; then
    curl -H @<(printf 'Authorization: Bearer %s\n' "$KOKORO_API_KEY") "$@"
  else curl "$@"; fi
}
CODE="$(kcurl -s -o /dev/null -w '%{http_code}' --max-time 5 "$KOKORO_BASE_URL/models" 2>/dev/null)"
if [ "$CODE" = 200 ]; then ok "Kokoro reachable ($KOKORO_BASE_URL/models -> 200)"
else warn "Kokoro not reachable ($KOKORO_BASE_URL/models -> ${CODE:-no answer}); narrated videos will not work"; fi
if [ $TTS_TEST -eq 1 ] && [ "$CODE" = 200 ]; then
  TMP="$(mktemp --suffix=.mp3)"
  HTTP="$(kcurl -s -o "$TMP" -w '%{http_code}' --max-time 60 -H 'Content-Type: application/json' \
    -d "{\"model\":\"$KOKORO_MODEL\",\"voice\":\"$KOKORO_VOICE\",\"input\":\"Testing narration.\",\"response_format\":\"mp3\"}" \
    "$KOKORO_BASE_URL/audio/speech")"
  if [ "$HTTP" = 200 ] && works ffprobe; then
    D="$(ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "$TMP" 2>/dev/null)"
    ok "TTS test clip: ${D:-?}s of audio"
  else warn "TTS test failed (HTTP $HTTP)"; fi
  rm -f "$TMP"
fi

echo
if [ $FAILS -gt 0 ]; then echo "RESULT: NOT READY ($FAILS fail, $WARNS warn). Fix the FAIL lines (scripts/setup_env.sh)."; exit 1; fi
echo "RESULT: READY for silent rendering ($WARNS warn)."
