#!/usr/bin/env bash
# Render a manim-video job in the render container. This is the default render path.
#
# Usage:
#   render-in-container.sh JOB_DIR [--quality preview|final] [--animations A,B] [--gpu | --no-gpu]
#                              [--no-build]
#   render-in-container.sh JOB_DIR --frames [--at T1,T2 | --count N | --anims --from S --to S | --cues]
#                                              more stills from the last render (no re-render),
#                                              written to JOB_DIR/out/frames/
#   render-in-container.sh JOB_DIR --still K   PNG at final resolution of the frame after animation K
#                                              (0-based, as in stills/index.txt) -> out/stills-full/
#   render-in-container.sh --build             build or rebuild the image (manim-video:local)
#   render-in-container.sh --status            is the image present and built from these sources?
#   render-in-container.sh --doctor [--gpu]    versions, fonts, LaTeX, EGL and VA-API in the image
#
# JOB_DIR holds scene.py, job.json and optional assets/ (references/container.md). The container
# sees JOB_DIR read-only at /job and writes only JOB_DIR/out/:
#   out/<Scene>-<quality>.mp4   the video             out/report.md, report.json  automated checks
#   out/stills/sheet_NN.png     contact sheets        out/stills/frame_*.png      full-size stills
#   out/stills/index.txt        tile -> time -> beat  out/summary.json            machine summary
#   out/render.log              full render log       out/media/                  Manim's cache
#
# --gpu / --no-gpu override job.json "gpu" (default off). The GPU only helps the OpenGL renderer
# and h264_vaapi encoding; the default Cairo renderer is CPU-only.
#
# Exit status: 0 rendered and checks passed (WARNs allowed), 1 rendered but a check FAILed,
# 2 bad job or usage, 3 Docker or image problem, 4 render failed, 130 interrupted.
#
# Environment (all optional):
#   MANIM_IMAGE      image tag (default manim-video:local)
#   KOKORO_API_KEY   given to narrated jobs only, by name, never printed. If unset, it is read from
#                    KOKORO_ENV_FILE (default ~/.config/agent-stack/gateway.env, if readable).
#   KOKORO_BASE_URL, KOKORO_MODEL, KOKORO_VOICE   defaults for narrated jobs (job.json wins)
#   MANIM_TTS_NETWORK  network for narrated jobs: bridge (default; the host is reached through
#                    host.docker.internal = the host gateway) or host (fallback if that route is
#                    blocked, e.g. by a host firewall)
set -euo pipefail

SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
SKILL_DIR="$(dirname "$SCRIPTS_DIR")"
DOCKER_DIR="$SKILL_DIR/docker"
export MANIM_IMAGE="${MANIM_IMAGE:-manim-video:local}"

note() { echo "render-in-container: $*"; }
fail() { local code="$1"; shift; echo "render-in-container: $*" >&2; exit "$code"; }
usage() { sed -n '2,/^set -euo pipefail/p' "${BASH_SOURCE[0]}" | sed '$d; s/^# \{0,1\}//'; exit "${1:-2}"; }

[ "$(id -u)" -ne 0 ] || fail 2 "refusing to run as root; run as the user who owns the job directory"
command -v docker >/dev/null 2>&1 || fail 3 "docker is not installed. Host fallback: scripts/render.sh (references/environment.md)"
docker info >/dev/null 2>&1 || fail 3 "cannot talk to the Docker daemon (is this user in the docker group?). Host fallback: scripts/render.sh"
docker compose version >/dev/null 2>&1 || fail 3 "the docker compose plugin (v2+) is missing"

# Hash of everything baked into the image, to spot a stale image after the skill changes.
source_sha() {
  ( export LC_ALL=C; cd "$SKILL_DIR" &&
    cat docker/Dockerfile docker/requirements.lock docker/manim_job.py scripts/*.py ) | sha256sum | cut -c1-16
}

build_image() {
  local logdir log
  logdir="${XDG_CACHE_HOME:-$HOME/.cache}/manim-video"; mkdir -p "$logdir"
  log="$logdir/build-$(date +%Y%m%d-%H%M%S).log"
  note "building $MANIM_IMAGE (first build: about 6 minutes; later builds reuse the cache). Log: $log"
  if ! SOURCE_SHA="$(source_sha)" JOB_DIR="$SKILL_DIR" \
       docker compose --progress plain -f "$DOCKER_DIR/compose.yml" build manim >"$log" 2>&1; then
    tail -n 30 "$log" >&2
    fail 3 "image build failed; full log: $log"
  fi
  note "built $MANIM_IMAGE ($(docker image inspect -f '{{.Size}}' "$MANIM_IMAGE" | awk '{printf "%.2f GB", $1/1e9}'))"
}

ensure_image() {
  local have want
  have="$(docker image inspect -f '{{index .Config.Labels "org.manim-video.source-sha"}}' "$MANIM_IMAGE" 2>/dev/null || true)"
  want="$(source_sha)"
  if [ -z "$have" ]; then
    [ "$NO_BUILD" = 1 ] && fail 3 "image $MANIM_IMAGE not found; run: $0 --build"
    build_image
  elif [ "$have" != "$want" ] && [ "$have" != "<no value>" ]; then
    if [ "$NO_BUILD" = 1 ]; then
      note "warning: $MANIM_IMAGE was built from older skill sources ($have, now $want); rebuild with --build"
    else
      note "image is older than the skill's sources; rebuilding"
      build_image
    fi
  fi
}

# ---- arguments -------------------------------------------------------------------------------
JOB_DIR=""; QUALITY=""; GPU_FLAG=""; NO_BUILD=0; ACTION=render; FRAME_ARGS=(); STILL_K=""; ANIMS=""
while [ $# -gt 0 ]; do
  if [ "$ACTION" = frames ]; then FRAME_ARGS+=("$1"); shift; continue; fi
  case "$1" in
    --frames) ACTION=frames; shift ;;
    --quality) [ $# -ge 2 ] || usage; QUALITY="$2"; shift 2 ;;
    --quality=*) QUALITY="${1#*=}"; shift ;;
    --preview|--final) QUALITY="${1#--}"; shift ;;
    --animations) [ $# -ge 2 ] || usage; ANIMS="$2"; shift 2 ;;
    --gpu) GPU_FLAG=1; shift ;;
    --no-gpu) GPU_FLAG=0; shift ;;
    --no-build) NO_BUILD=1; shift ;;
    --build) ACTION=build; shift ;;
    --status) ACTION=status; shift ;;
    --still) [ $# -ge 2 ] || usage; ACTION=still; STILL_K="$2"; shift 2 ;;
    --doctor) ACTION=doctor; shift ;;
    -h|--help) usage 0 ;;
    -*) echo "render-in-container: unknown option $1" >&2; usage ;;
    *) [ -z "$JOB_DIR" ] || usage; JOB_DIR="$1"; shift ;;
  esac
done
case "$QUALITY" in ""|preview|final) ;; *) fail 2 "--quality must be preview or final" ;; esac

if [ "$ACTION" = build ]; then build_image; exit 0; fi
if [ "$ACTION" = status ]; then
  have="$(docker image inspect -f '{{index .Config.Labels "org.manim-video.source-sha"}}' "$MANIM_IMAGE" 2>/dev/null || true)"
  want="$(source_sha)"
  if [ -z "$have" ]; then echo "image $MANIM_IMAGE: missing (build: $0 --build)"; exit 2; fi
  size="$(docker image inspect -f '{{.Size}}' "$MANIM_IMAGE" | awk '{printf "%.2f GB", $1/1e9}')"
  if [ "$have" = "$want" ]; then echo "image $MANIM_IMAGE: current ($size, sources $want)"; exit 0; fi
  echo "image $MANIM_IMAGE: stale (built from $have, sources now $want; the next render rebuilds it)"; exit 1
fi
case "$STILL_K" in ""|*[!0-9]*) [ "$ACTION" = still ] && fail 2 "--still needs an animation number (0-based)" ;; esac

# ---- per-run compose project: unique name, removed on exit -----------------------------------
COMPOSE_FILES=(-f "$DOCKER_DIR/compose.yml")
export HOST_UID HOST_GID MANIM_NETWORK=none
HOST_UID="$(id -u)"; HOST_GID="$(id -g)"

enable_gpu() {
  local node card
  node="$(ls /dev/dri/renderD* 2>/dev/null | head -n 1 || true)"
  if [ -z "$node" ]; then
    note "warning: GPU requested but this host has no /dev/dri render node; rendering on the CPU"
    return 0
  fi
  card="$(ls /dev/dri/card* 2>/dev/null | head -n 1 || true)"
  VIDEO_GID="$(getent group video | cut -d: -f3 || true)"
  RENDER_GID="$(getent group render | cut -d: -f3 || true)"
  [ -n "$RENDER_GID" ] || RENDER_GID="$(stat -c %g "$node")"
  [ -n "$VIDEO_GID" ] || VIDEO_GID="$(stat -c %g "${card:-$node}")"
  export VIDEO_GID RENDER_GID
  COMPOSE_FILES+=(-f "$DOCKER_DIR/compose.gpu.yml")
  GPU_ON=1
}

PROJECT=""; CHILD=""
cleanup() {
  [ -n "$CHILD" ] && kill "$CHILD" 2>/dev/null || true
  [ -n "$PROJECT" ] || return 0
  local ids
  ids="$(docker ps -aq --filter "label=com.docker.compose.project=$PROJECT" 2>/dev/null || true)"
  # shellcheck disable=SC2086
  [ -z "$ids" ] || docker rm -f $ids >/dev/null 2>&1 || true
  docker compose -p "$PROJECT" "${COMPOSE_FILES[@]}" down --remove-orphans --timeout 5 >/dev/null 2>&1 || true
}
trap cleanup EXIT
trap 'echo; note "interrupted; removing the container"; exit 130' INT TERM

new_project() {
  local slug
  slug="$(basename "$1" | tr '[:upper:]' '[:lower:]' | tr -c 'a-z0-9' '-' | sed -E 's/-+/-/g; s/^-//; s/-$//' | cut -c1-24)"
  PROJECT="manim-${slug:-job}-$(date +%Y%m%d%H%M%S)-$$"
}

# Run the compose service in the background and wait, so INT/TERM reach the trap at once.
run_service() {
  docker compose --progress quiet -p "$PROJECT" "${COMPOSE_FILES[@]}" run --rm -T manim "$@" &
  CHILD=$!
  set +e; wait "$CHILD"; local rc=$?; set -e
  CHILD=""
  return "$rc"
}

GPU_ON=0
if [ "$ACTION" = doctor ]; then
  ensure_image
  [ "$GPU_FLAG" = 1 ] && enable_gpu
  JOB_DIR="$(mktemp -d)"; mkdir -p "$JOB_DIR/out"
  export JOB_DIR
  new_project doctor
  set +e; run_service doctor; rc=$?; set -e
  cleanup; PROJECT=""
  rm -rf "$JOB_DIR"
  exit "$rc"
fi

# ---- render ------------------------------------------------------------------------------------
[ -n "$JOB_DIR" ] || usage
[ -d "$JOB_DIR" ] || fail 2 "no such job directory: $JOB_DIR"
JOB_DIR="$(cd "$JOB_DIR" && pwd -P)"
[ -f "$JOB_DIR/job.json" ] || fail 2 "$JOB_DIR has no job.json (template: templates/job.json)"
export JOB_DIR
mkdir -p "$JOB_DIR/out"
[ -w "$JOB_DIR/out" ] || fail 2 "$JOB_DIR/out is not writable by $(id -un)"

ensure_image

# Validate job.json in a throwaway container (no network, no mounts) and read the settings.
INFO="$(docker run --rm -i --network none --user "$HOST_UID:$HOST_GID" --read-only --cap-drop ALL \
          --security-opt no-new-privileges "$MANIM_IMAGE" inspect < "$JOB_DIR/job.json")" || {
  printf '%s\n' "$INFO" | sed -n 's/^ERROR=/render-in-container: bad job.json: /p' >&2
  exit 2
}
J_SCENE=""; J_GPU=0; J_NARRATION=0; J_NETWORK=none
while IFS='=' read -r k v; do
  case "$k" in
    SCENE) J_SCENE="$v" ;;
    GPU) [ "$v" = 1 ] && J_GPU=1 ;;
    NARRATION) [ "$v" = 1 ] && J_NARRATION=1 ;;
    NETWORK) [ "$v" = bridge ] && J_NETWORK=bridge ;;
  esac
done <<< "$INFO"

MANIM_NETWORK="$J_NETWORK"
if [ "$MANIM_NETWORK" = bridge ]; then
  case "${MANIM_TTS_NETWORK:-bridge}" in
    bridge|host) MANIM_NETWORK="${MANIM_TTS_NETWORK:-bridge}" ;;
    *) fail 2 "MANIM_TTS_NETWORK must be bridge or host" ;;
  esac
fi
WANT_GPU="$J_GPU"; [ -n "$GPU_FLAG" ] && WANT_GPU="$GPU_FLAG"
if [ "$ACTION" = frames ]; then   # still extraction needs no network, key or GPU
  MANIM_NETWORK=none; J_NARRATION=0; WANT_GPU=0
fi
[ "$WANT_GPU" = 1 ] && enable_gpu

if [ "$J_NARRATION" = 1 ]; then
  if [ -z "${KOKORO_API_KEY:-}" ]; then
    envfile="${KOKORO_ENV_FILE:-$HOME/.config/agent-stack/gateway.env}"
    if [ -r "$envfile" ]; then
      KOKORO_API_KEY="$(sed -n -E 's/^(export[[:space:]]+)?KOKORO_API_KEY=//p' "$envfile" | tail -n 1)"
      KOKORO_API_KEY="${KOKORO_API_KEY%\"}"; KOKORO_API_KEY="${KOKORO_API_KEY#\"}"
      KOKORO_API_KEY="${KOKORO_API_KEY%\'}"; KOKORO_API_KEY="${KOKORO_API_KEY#\'}"
      [ -n "$KOKORO_API_KEY" ] && note "narration: using KOKORO_API_KEY from $envfile (passed by name; value not shown)"
    fi
  fi
  [ -n "${KOKORO_API_KEY:-}" ] && export KOKORO_API_KEY || unset KOKORO_API_KEY
else
  unset KOKORO_API_KEY   # silent jobs never see the key
fi

new_project "$JOB_DIR"
note "job $JOB_DIR: scene $J_SCENE, GPU $([ "$GPU_ON" = 1 ] && echo "on (video $VIDEO_GID, render $RENDER_GID)" || echo off), network $MANIM_NETWORK"
if [ "$ACTION" = frames ]; then
  ARGS=(frames "${FRAME_ARGS[@]}")
elif [ "$ACTION" = still ]; then
  ARGS=(still "$STILL_K")
else
  ARGS=(render); [ -n "$QUALITY" ] && ARGS+=(--quality "$QUALITY"); [ -n "$ANIMS" ] && ARGS+=(--animations "$ANIMS")
fi
set +e; run_service "${ARGS[@]}"; RC=$?; set -e
cleanup; PROJECT=""

OUT="$JOB_DIR/out"
shopt -s nullglob
for f in "$OUT"/*.mp4; do echo "VIDEO: $f"; done
if [ "$ACTION" = still ]; then
  for f in "$OUT"/stills-full/anim_"$STILL_K"*.png; do echo "IMAGE: $f"; done
  exit "$RC"
fi
if [ "$ACTION" = frames ]; then
  for f in "$OUT"/frames/sheet_*.png; do echo "SHEET: $f"; done
  [ -f "$OUT/frames/index.txt" ] && echo "INDEX: $OUT/frames/index.txt"
  exit "$RC"
fi
for f in "$OUT"/stills/sheet_*.png; do echo "SHEET: $f"; done
[ -f "$OUT/stills/index.txt" ] && echo "INDEX: $OUT/stills/index.txt"
[ -f "$OUT/report.md" ] && echo "REPORT: $OUT/report.md"
[ -f "$OUT/render.log" ] && echo "LOG: $OUT/render.log"
exit "$RC"
