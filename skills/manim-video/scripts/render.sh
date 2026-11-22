#!/usr/bin/env bash
# Render a Manim Community scene file headlessly (Docker image or local install).
#
# Usage: render.sh <preview|final|still> SCENE_FILE.py [SceneName ...] [-- extra manim args]
#
#   preview  fast review render: 854x480 at 15 fps (-ql)
#   final    deliverable: 1920x1080 at 60 fps (-qh)
#   still    PNG of the last frame at final quality (-s -qh). Add "-- -n 0,K" to stop
#            after animation K, to inspect small text at full resolution.
#
# With no SceneName, every Scene in the file is rendered (-a).
# Prints one "VIDEO: <path>" or "IMAGE: <path>" line per new output file.
#
# Environment (all optional):
#   MANIM_BACKEND    auto | docker | local     (auto: local manim if installed, else docker)
#   PREVIEW_QUALITY  l (default) | m           FINAL_QUALITY  h (default) | p | k | m
#   MANIM_NETWORK    auto | none | tts         (auto: tts if the file uses KokoroService/VoiceoverScene)
#   MANIM_IMAGE      docker image (default manim-video:0.22.1, built by setup_env.sh)
#   KOKORO_BASE_URL, KOKORO_MODEL, KOKORO_VOICE, KOKORO_API_KEY   narration settings
#
# The scene file's directory is the project directory: keep the scene, its assets and
# its output (media/) there. Only that directory is visible to the Docker renderer.
set -euo pipefail
# shellcheck source=_env.sh
. "$(dirname "${BASH_SOURCE[0]}")/_env.sh"

usage() { sed -n '2,24p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit "${1:-2}"; }

[ $# -ge 2 ] || usage
MODE="$1"; shift
SCENE_FILE="$1"; shift
case "$MODE" in preview|final|still) ;; -h|--help) usage 0 ;; *) echo "render.sh: unknown mode '$MODE'" >&2; usage ;; esac
[ -f "$SCENE_FILE" ] || { echo "render.sh: no such file: $SCENE_FILE" >&2; exit 2; }
case "$SCENE_FILE" in *.py) ;; *) echo "render.sh: scene file must end in .py" >&2; exit 2 ;; esac

SCENES=(); EXTRA=()
while [ $# -gt 0 ]; do
  if [ "$1" = "--" ]; then shift; EXTRA=("$@"); break; fi
  SCENES+=("$1"); shift
done
[ ${#SCENES[@]} -gt 0 ] || SCENES=(-a)

PROJECT_DIR="$(cd "$(dirname "$SCENE_FILE")" && pwd -P)"
REL="$(basename "$SCENE_FILE")"
STEM="${REL%.py}"

case "$MODE" in
  preview) QFLAGS=("-q${PREVIEW_QUALITY:-l}") ;;
  final)   QFLAGS=("-q${FINAL_QUALITY:-h}") ;;
  still)   QFLAGS=("-q${FINAL_QUALITY:-h}" -s) ;;
esac

# Pre-flight: refuse ManimGL idioms, which fail or misbehave under Manim Community.
GL_HITS="$(grep -nE '\b(manimlib|manimgl|ShowCreation|ShowCreationThenDestruction|TexMobject|TextMobject|GraphScene|InteractiveScene|TexText)\b|^\s*CONFIG\s*=|self\.embed\(|\.fix_in_frame\(' "$PROJECT_DIR/$REL" | grep -vE '^[0-9]+:\s*#' || true)"
if [ -n "$GL_HITS" ]; then
  echo "$GL_HITS" >&2
  echo "render.sh: the lines above use ManimGL (3b1b/manim) idioms. This skill targets Manim Community:" >&2
  echo "  ShowCreation->Create, TexMobject->MathTex, TextMobject/TexText->Tex, CONFIG dict->__init__ args," >&2
  echo "  GraphScene->Axes, no self.embed(), fix_in_frame->add_fixed_in_frame_mobjects. See references/api-cheatsheet.md." >&2
  exit 2
fi

NETWORK="${MANIM_NETWORK:-auto}"
if [ "$NETWORK" = auto ]; then
  if grep -qE 'VoiceoverScene|KokoroService' "$PROJECT_DIR/$REL"; then NETWORK=tts; else NETWORK=none; fi
fi

BACKEND="$(resolve_backend)"
if [ -z "$BACKEND" ]; then
  echo "render.sh: no renderer available (MANIM_BACKEND=$MANIM_BACKEND)." >&2
  echo "  Run scripts/check_env.sh, then scripts/setup_env.sh to install the Docker image." >&2
  exit 3
fi

mkdir -p "$PROJECT_DIR/media/logs"
STAMP="$(date +%Y%m%d-%H%M%S)"
LOG="$PROJECT_DIR/media/logs/$STEM-$MODE-$STAMP.log"
MARKER="$PROJECT_DIR/media/.render-$STAMP-$$"
touch "$MARKER"
CONTAINER="manim-video-$STAMP-$$"
cleanup() {
  rm -f "$MARKER"
  # If this script is interrupted, do not leave the render container running.
  if [ "${BACKEND:-}" = docker ] && docker ps -q --filter "name=^$CONTAINER\$" 2>/dev/null | grep -q .; then
    docker kill "$CONTAINER" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT
trap 'exit 130' INT TERM

# Manim keeps only 100 partial movies by default and deletes older ones, which breaks
# frames.py's per-animation timing for longer scenes. The limit has no CLI flag, and a
# --config_file replaces the project's manim.cfg, so write a merged copy with the limit raised.
CFG="media/manim-video.cfg"
python3 - "$PROJECT_DIR/manim.cfg" "$PROJECT_DIR/$CFG" <<'PY'
import configparser, os, sys
cp = configparser.ConfigParser(interpolation=None)
if os.path.exists(sys.argv[1]):
    cp.read(sys.argv[1])
if not cp.has_section("CLI"):
    cp.add_section("CLI")
cp.set("CLI", "max_files_cached", "100000")
with open(sys.argv[2], "w") as f:
    cp.write(f)
PY

MANIM_ARGS=(manim "${QFLAGS[@]}" --progress_bar none --config_file "$CFG" "$REL" "${SCENES[@]}")
# Narrated scenes: reusing cached partial movies lets the picture drift from the audio, so
# always re-render them (the TTS clips stay cached in media/voiceovers/).
if [ "$NETWORK" = tts ] && [[ " ${EXTRA[*]:-} " != *" --disable_caching "* ]]; then
  MANIM_ARGS+=(--disable_caching)
fi
[ ${#EXTRA[@]} -gt 0 ] && MANIM_ARGS+=("${EXTRA[@]}")

START=$(date +%s)
set +e
if [ "$BACKEND" = docker ]; then
  IMAGE="$(resolve_image)"
  if [ -z "$IMAGE" ]; then
    echo "render.sh: no Manim image found ($MANIM_IMAGE or $MANIM_BASE_IMAGE). Run scripts/setup_env.sh." >&2
    exit 3
  fi
  DARGS=(run --rm --name "$CONTAINER" --user "$(id -u):$(id -g)" -e HOME=/tmp -e COLUMNS=200
         -e PYTHONPATH=/skill/scripts -e PYTHONDONTWRITEBYTECODE=1
         -v "$PROJECT_DIR:/manim" -v "$SCRIPTS_DIR:/skill/scripts:ro" -w /manim)
  if [ "$NETWORK" = tts ]; then
    if [ "$IMAGE" = "$MANIM_BASE_IMAGE" ]; then
      echo "render.sh: narration needs the derived image $MANIM_IMAGE (manim-voiceover). Run scripts/setup_env.sh." >&2
      exit 3
    fi
    # Inside the container, the host's loopback is host.docker.internal.
    URL="$(printf '%s' "$KOKORO_BASE_URL" | sed -E 's#//(127\.0\.0\.1|localhost)([:/]|$)#//host.docker.internal\2#')"
    DARGS+=(--add-host=host.docker.internal:host-gateway -e "KOKORO_BASE_URL=$URL" -e KOKORO_MODEL -e KOKORO_VOICE)
    # Pass the key through by name only, so its value never appears in a command line.
    [ -n "${KOKORO_API_KEY:-}" ] && DARGS+=(-e KOKORO_API_KEY)
  else
    DARGS+=(--network none)
  fi
  echo "render.sh: $MODE $REL ${SCENES[*]} (docker: $IMAGE, network: $NETWORK)"
  docker "${DARGS[@]}" "$IMAGE" "${MANIM_ARGS[@]}" >"$LOG" 2>&1
  RC=$?
else
  echo "render.sh: $MODE $REL ${SCENES[*]} (local: $(command -v manim))"
  (cd "$PROJECT_DIR" && COLUMNS=200 PYTHONPATH="$SCRIPTS_DIR${PYTHONPATH:+:$PYTHONPATH}" "${MANIM_ARGS[@]}") >"$LOG" 2>&1
  RC=$?
fi
set -e
ELAPSED=$(( $(date +%s) - START ))

# Surface warnings from manim_qa.LayoutGuard and narration_timeline.Timeline, if the scene uses them.
if grep -q 'LAYOUT-GUARD active' "$LOG"; then
  echo "render.sh: layout guard active"
elif grep -q 'LayoutGuard' "$PROJECT_DIR/$REL"; then
  echo "render.sh: WARNING the scene mentions LayoutGuard but it did not run (import failed, or not mixed in first)"
fi
if grep -qE '^.*(LAYOUT [^-]|LAYOUT$|NARRATION)' "$LOG"; then
  echo "---- scene warnings (LayoutGuard / Timeline) ----"
  grep -hE 'LAYOUT |NARRATION' "$LOG" | grep -v 'LAYOUT-GUARD' | sed -E 's/^.*(LAYOUT|NARRATION)/\1/' \
    | awk '!seen[$0]++' | head -80
fi

if [ $RC -ne 0 ]; then
  echo "render.sh: FAILED after ${ELAPSED}s (exit $RC). Last lines of $LOG:" >&2
  tail -n 60 "$LOG" >&2
  if grep -qiE 'latex error|LaTeX compilation error|! Undefined control sequence|! Missing' "$LOG"; then
    echo "render.sh: this is a LaTeX error. See references/troubleshooting.md (LaTeX)." >&2
  fi
  exit $RC
fi

echo "render.sh: ok in ${ELAPSED}s. Log: $LOG"
FOUND=0
while IFS= read -r f; do
  FOUND=1
  case "$f" in
    *.png)
      if [ "$MODE" = still ]; then
        # Manim reuses one file name per scene; keep every still for before/after comparisons.
        mkdir -p "$PROJECT_DIR/media/stills"
        KEEP="$PROJECT_DIR/media/stills/$(basename "${f%.png}")-$STAMP.png"
        cp "$f" "$KEEP"; f="$KEEP"
      fi
      echo "IMAGE: $f" ;;
    *)
      INFO=""
      if works ffprobe; then
        INFO="$(ffprobe -v error -select_streams v:0 -show_entries stream=width,height,r_frame_rate:format=duration \
                 -of default=nw=1:nk=1 "$f" 2>/dev/null | tr '\n' ' ' || true)"
      fi
      echo "VIDEO: $f${INFO:+  [w h fps dur: $INFO]}" ;;
  esac
done < <(find "$PROJECT_DIR/media" -newer "$MARKER" -type f \( -name '*.mp4' -o -name '*.mov' -o -name '*.webm' -o -name '*.gif' -o -name '*.png' \) \
           -not -path '*/partial_movie_files/*' -not -path '*/Tex/*' -not -path '*/texts/*' -not -path '*/stills/*' \
           -not -path '*/frames_*' 2>/dev/null | sort)
[ $FOUND -eq 1 ] || echo "render.sh: render succeeded but no new output file was found under $PROJECT_DIR/media" >&2
