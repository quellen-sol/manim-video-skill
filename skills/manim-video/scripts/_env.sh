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

MANIM_VERSION="${MANIM_VERSION:-0.22.1}"
# Container route (the default): image tag built from ../docker/ by render-in-container.sh --build.
MANIM_IMAGE="${MANIM_IMAGE:-manim-video:local}"
# Host route (the fallback): a venv made by `setup_env.sh --host`, or manim on PATH.
MANIM_HOST_VENV="${MANIM_HOST_VENV:-$MANIM_VIDEO_HOME/venv}"
export MANIM_IMAGE MANIM_HOST_VENV

# Kokoro (OpenAI-compatible TTS). The API key is read from KOKORO_API_KEY only.
KOKORO_BASE_URL="${KOKORO_BASE_URL:-http://127.0.0.1:8880/v1}"
KOKORO_MODEL="${KOKORO_MODEL:-kokoro}"
KOKORO_VOICE="${KOKORO_VOICE:-af_heart}"
export KOKORO_BASE_URL KOKORO_MODEL KOKORO_VOICE

have() { command -v "$1" >/dev/null 2>&1; }

# True if the tool exists *and* runs (catches binaries with missing libraries).
works() { have "$1" && "$1" -version >/dev/null 2>&1; }

docker_ok() { have docker && docker info >/dev/null 2>&1; }

# Path of a working host Manim Community (venv first, then PATH), or nothing.
host_manim() {
  local m
  for m in "$MANIM_HOST_VENV/bin/manim" "$(command -v manim 2>/dev/null || true)"; do
    [ -n "$m" ] && [ -x "$m" ] || continue
    if "$m" --version 2>/dev/null | grep -q "Manim Community"; then echo "$m"; return 0; fi
  done
}
