#!/usr/bin/env bash
# Check that everything the manim-video skill needs is present. Read-only; installs nothing
# (it may run short-lived containers with --rm).
#
# Usage: check_env.sh [--host] [--gpu] [--tts] [--fonts]
#   (default) the container route: Docker, the compose plugin, the render image (present and
#            built from these sources), Manim/LaTeX/voiceover inside it, and Kokoro reachable
#            both from the host and from a container (host.docker.internal)
#   --host   also the host route (fallback): host Manim, Python, LaTeX, dvisvgm, ffmpeg/ffprobe
#   --gpu    also the GPU inside the container: /dev/dri, OpenGL (EGL) device, VA-API H.264 encode
#   --tts    also synthesize one short test clip with Kokoro (from the host)
#   --fonts  list the font families inside the image (with --host: on the host)
# Exit status: 0 if silent rendering works on the container route (or on the host route with
# --host and no Docker), 1 if not. Narration and GPU problems are reported as WARN.
set -uo pipefail
# shellcheck source=_env.sh
. "$(dirname "${BASH_SOURCE[0]}")/_env.sh"

HOST=0; GPU=0; TTS_TEST=0; FONTS=0
for a in "$@"; do
  case "$a" in
    --host) HOST=1 ;;
    --gpu) GPU=1 ;;
    --tts) TTS_TEST=1 ;;
    --fonts) FONTS=1 ;;
    -h|--help) sed -n '2,15p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "check_env.sh: unknown option $a" >&2; exit 2 ;;
  esac
done
CFAILS=0; HFAILS=0; WARNS=0; NARR=""; CONTAINER_OK=0; HOST_OK=0
ok()    { printf '  OK    %s\n' "$*"; }
warn()  { printf '  WARN  %s\n' "$*"; WARNS=$((WARNS+1)); }
cfail() { printf '  FAIL  %s\n' "$*"; CFAILS=$((CFAILS+1)); }
hfail() { printf '  FAIL  %s\n' "$*"; HFAILS=$((HFAILS+1)); }
info()  { printf '  INFO  %s\n' "$*"; }

echo "manim-video environment check (skill: $SKILL_DIR)"

echo "[container route: the default]"
if ! have docker; then cfail "docker is not installed"
elif ! docker_ok; then cfail "cannot talk to the Docker daemon (is this user in the docker group?)"
else
  ok "docker $(docker version -f '{{.Server.Version}}' 2>/dev/null)"
  if docker compose version >/dev/null 2>&1; then ok "$(docker compose version | head -1)"
  else cfail "the docker compose plugin is missing"; fi
  STATUS="$("$SCRIPTS_DIR/render-in-container.sh" --status 2>&1)"; RC=$?
  case $RC in
    0) ok "$STATUS" ;;
    1) warn "$STATUS" ;;
    *) cfail "$STATUS" ;;
  esac
  if [ $RC -le 1 ]; then
    IMG_RUN=(docker run --rm --network none --user "$(id -u):$(id -g)" "$MANIM_IMAGE")
    REPORT="$("${IMG_RUN[@]}" doctor 2>&1)"
    MV="$(printf '%s\n' "$REPORT" | sed -n 's/^manim *//p')"
    case "$MV" in *"v$MANIM_VERSION"*) ok "image: $MV" ;; *) cfail "image: manim ${MV:-did not run}" ;; esac
    LX="$(printf '%s\n' "$REPORT" | sed -n 's/^latex *//p')"; DV="$(printf '%s\n' "$REPORT" | sed -n 's/^dvisvgm *//p')"
    [ -n "$LX" ] && [ -n "$DV" ] && ok "image: LaTeX ($LX) + $DV" || cfail "image: LaTeX or dvisvgm missing"
    VO="$(printf '%s\n' "$REPORT" | sed -n 's/^voiceover *//p')"
    [ -n "$VO" ] && ok "image: manim-voiceover $VO" || { warn "image: manim-voiceover missing"; NARR="fallback only"; }
    ok "image: $(printf '%s\n' "$REPORT" | sed -n 's/^fonts *//p') (default text font)"
    if [ $FONTS -eq 1 ] && [ $HOST -eq 0 ]; then
      echo "[fonts in the image]"
      docker run --rm --network none --user "$(id -u):$(id -g)" "$MANIM_IMAGE" exec sh -c 'fc-list : family | sort -u' | sed 's/^/  /'
    fi
    if [ $GPU -eq 1 ]; then
      echo "[GPU in the container (opt-in)]"
      if ls /dev/dri/renderD* >/dev/null 2>&1; then
        "$SCRIPTS_DIR/render-in-container.sh" --doctor --gpu --no-build 2>&1 \
          | grep -E '^(uid|dri nodes|opengl|vaapi|h264 encode)' | sed 's/^/  INFO  /'
      else
        info "no /dev/dri render node on this host: GPU paths unavailable (CPU rendering is unaffected)"
      fi
    fi
  fi
fi
[ $CFAILS -eq 0 ] && CONTAINER_OK=1

if [ $HOST -eq 1 ]; then
  echo "[host route: the fallback]"
  pyver_ok() { "$1" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null; }
  if have python3 && pyver_ok python3; then ok "python3 $(python3 -c 'import platform; print(platform.python_version())')"
  else hfail "python3 >= 3.11 not found (needed by frames.py, qa_check.py, narrate_mux.py)"; fi
  for t in ffmpeg ffprobe; do
    if works "$t"; then ok "$t: $(command -v "$t") ($("$t" -version 2>/dev/null | head -1 | awk '{print $3}'))"
    elif have "$t"; then hfail "$t at $(command -v "$t") does not run (broken install?); setup_env.sh --host fetches a static build"
    else hfail "$t not found (setup_env.sh --host fetches a static build into $MANIM_VIDEO_HOME/bin)"; fi
  done
  M="$(host_manim)"
  if [ -z "$M" ]; then hfail "no host Manim Community ($MANIM_HOST_VENV/bin/manim or manim on PATH): setup_env.sh --host"
  else
    MV="$("$M" --version 2>/dev/null | grep -m1 'Manim Community')"
    case "$MV" in *"v$MANIM_VERSION"*) ok "$MV ($M)" ;; *) warn "$MV (skill is written for v$MANIM_VERSION)" ;; esac
    "$(dirname "$M")/python" -c 'import manim_voiceover' >/dev/null 2>&1 && ok "manim-voiceover in the host Manim's Python" \
      || warn "manim-voiceover missing on the host: narration there must use narrate_mux.py"
  fi
  if have latex && have dvisvgm; then ok "LaTeX + dvisvgm on the host"
  else warn "LaTeX or dvisvgm missing on the host: MathTex/Tex will fail there"; fi
  if [ $FONTS -eq 1 ]; then echo "[host fonts]"; fc-list : family 2>/dev/null | sort -u | sed 's/^/  /'; fi
  [ $HFAILS -eq 0 ] && HOST_OK=1
fi

echo "[narration: Kokoro at $KOKORO_BASE_URL, model $KOKORO_MODEL, voice $KOKORO_VOICE]"
KEYSRC=""
if [ -n "${KOKORO_API_KEY:-}" ]; then KEYSRC="environment"
elif [ -r "${KOKORO_ENV_FILE:-$HOME/.config/agent-stack/gateway.env}" ] \
     && grep -qE '^(export[[:space:]]+)?KOKORO_API_KEY=.' "${KOKORO_ENV_FILE:-$HOME/.config/agent-stack/gateway.env}"; then
  KEYSRC="${KOKORO_ENV_FILE:-$HOME/.config/agent-stack/gateway.env} (render-in-container.sh reads it)"
fi
if [ -n "$KEYSRC" ]; then ok "KOKORO_API_KEY available from $KEYSRC (value not shown)"
else info "KOKORO_API_KEY not set (fine if the server needs no key)"; fi
# The key goes to curl through a file descriptor, so it never appears in a process listing.
kcurl() {
  if [ -n "${KOKORO_API_KEY:-}" ]; then
    curl -H @<(printf 'Authorization: Bearer %s\n' "$KOKORO_API_KEY") "$@"
  else curl "$@"; fi
}
CODE="$(kcurl -s -o /dev/null -w '%{http_code}' --max-time 5 "$KOKORO_BASE_URL/models" 2>/dev/null)"
if [ "$CODE" = 200 ]; then ok "Kokoro reachable from the host ($KOKORO_BASE_URL/models -> 200)"
else warn "Kokoro not reachable from the host ($KOKORO_BASE_URL/models -> ${CODE:-no answer}); narrated videos will not work"
     NARR="NOT READY (TTS server unreachable)"; fi
if [ $CONTAINER_OK -eq 1 ] && [ "$CODE" = 200 ]; then
  CURL_URL="$(printf '%s' "$KOKORO_BASE_URL" | sed -E 's#//(127\.0\.0\.1|localhost)([:/]|$)#//host.docker.internal\2#')"
  if docker run --rm --add-host host.docker.internal:host-gateway --user "$(id -u):$(id -g)" "$MANIM_IMAGE" exec \
       python3 -c "import socket, sys, urllib.parse as u; p = u.urlsplit(sys.argv[1]); socket.create_connection((p.hostname, p.port or 80), timeout=5)" \
       "$CURL_URL" >/dev/null 2>&1; then
    ok "Kokoro reachable from a container ($CURL_URL)"
  else
    warn "Kokoro not reachable from a container at $CURL_URL; try MANIM_TTS_NETWORK=host"
    NARR="${NARR:-container route needs MANIM_TTS_NETWORK=host}"
  fi
fi
if [ $TTS_TEST -eq 1 ] && [ "$CODE" = 200 ]; then
  TMP="$(mktemp --suffix=.mp3)"
  HTTP="$(kcurl -s -o "$TMP" -w '%{http_code}' --max-time 60 -H 'Content-Type: application/json' \
    -d "{\"model\":\"$KOKORO_MODEL\",\"voice\":\"$KOKORO_VOICE\",\"input\":\"Testing narration.\",\"response_format\":\"mp3\"}" \
    "$KOKORO_BASE_URL/audio/speech")"
  if [ "$HTTP" = 200 ]; then ok "TTS test clip: $(wc -c < "$TMP") bytes of mp3"
  else warn "TTS test failed (HTTP $HTTP)"; NARR="NOT READY (TTS test failed)"; fi
  rm -f "$TMP"
fi

echo
if [ $CONTAINER_OK -eq 1 ]; then
  echo "RESULT: READY on the container route ($WARNS warn). Render with scripts/render-in-container.sh JOB_DIR."
  [ $HOST -eq 1 ] && { [ $HOST_OK -eq 1 ] && echo "        Host route (render.sh) also ready." || echo "        Host route (render.sh) NOT ready: see the FAIL lines above."; }
  echo "        Narration: ${NARR:-READY (manim-voiceover + Kokoro)}."
  exit 0
fi
if [ $HOST -eq 1 ] && [ $HOST_OK -eq 1 ]; then
  echo "RESULT: container route NOT READY; host route READY ($WARNS warn). Render with scripts/render.sh (fallback)."
  exit 0
fi
echo "RESULT: NOT READY. Fix the FAIL lines: scripts/setup_env.sh builds the image (needs Docker);"
echo "        scripts/setup_env.sh --host sets up the host fallback."
exit 1
