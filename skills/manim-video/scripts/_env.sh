# Shared defaults for the manim-video scripts. Sourced, not executed.
# Every value can be overridden from the environment.

SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
SKILL_DIR="$(dirname "$SCRIPTS_DIR")"

# User-space tool home: static ffmpeg/ffprobe live in $MANIM_VIDEO_HOME/bin. It goes first on
# PATH, because a system ffmpeg can be installed but broken (missing shared libraries).
MANIM_VIDEO_HOME="${MANIM_VIDEO_HOME:-$HOME/.local/share/manim-video}"
case ":$PATH:" in
  *":$MANIM_VIDEO_HOME/bin:"*) ;;
  *) [ -d "$MANIM_VIDEO_HOME/bin" ] && PATH="$MANIM_VIDEO_HOME/bin:$PATH" ;;
esac
export PATH MANIM_VIDEO_HOME

# Rendering backend: auto | docker | local
MANIM_BACKEND="${MANIM_BACKEND:-auto}"
MANIM_VERSION="${MANIM_VERSION:-0.22.1}"
# Derived image built by setup_env.sh (adds manim-voiceover, ffmpeg, sox).
MANIM_IMAGE="${MANIM_IMAGE:-manim-video:$MANIM_VERSION}"
MANIM_BASE_IMAGE="${MANIM_BASE_IMAGE:-manimcommunity/manim:v$MANIM_VERSION}"

# Kokoro (OpenAI-compatible TTS). The API key is read from KOKORO_API_KEY only.
KOKORO_BASE_URL="${KOKORO_BASE_URL:-http://127.0.0.1:8880/v1}"
KOKORO_MODEL="${KOKORO_MODEL:-kokoro}"
KOKORO_VOICE="${KOKORO_VOICE:-af_heart}"
export KOKORO_BASE_URL KOKORO_MODEL KOKORO_VOICE

have() { command -v "$1" >/dev/null 2>&1; }

# True if the tool exists *and* runs (catches binaries with missing libraries).
works() { have "$1" && "$1" -version >/dev/null 2>&1; }

docker_ok() { have docker && docker info >/dev/null 2>&1; }

local_manim_ok() {
  have manim && manim --version 2>/dev/null | grep -q "Manim Community"
}

# Prints the backend that will be used, or nothing if none is available.
resolve_backend() {
  case "$MANIM_BACKEND" in
    docker) docker_ok && echo docker ;;
    local) local_manim_ok && echo local ;;
    *)
      if local_manim_ok; then echo local
      elif docker_ok; then echo docker
      fi ;;
  esac
}

# Image to run: the derived image if present, else the official base image.
resolve_image() {
  if docker image inspect "$MANIM_IMAGE" >/dev/null 2>&1; then echo "$MANIM_IMAGE"
  elif docker image inspect "$MANIM_BASE_IMAGE" >/dev/null 2>&1; then echo "$MANIM_BASE_IMAGE"
  fi
}
