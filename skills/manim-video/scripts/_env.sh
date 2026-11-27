# shellcheck shell=bash
# Shared defaults for the manim-video scripts. Sourced, not executed.
# Every value can be overridden from the environment.

SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck disable=SC2034  # used by the scripts that source this file
SKILL_DIR="$(dirname "$SCRIPTS_DIR")"

# User-space tool home ($MANIM_VIDEO_HOME/bin may hold a static ffmpeg/ffprobe from
# setup_env.sh --host). The system ffmpeg is used when it runs; the static build is only a
# fallback for a missing or broken one (for example a missing shared library).
MANIM_VIDEO_HOME="${MANIM_VIDEO_HOME:-$HOME/.local/share/manim-video}"
if ! { command -v ffmpeg >/dev/null 2>&1 && ffmpeg -version >/dev/null 2>&1 \
       && command -v ffprobe >/dev/null 2>&1 && ffprobe -version >/dev/null 2>&1; }; then
  case ":$PATH:" in
    *":$MANIM_VIDEO_HOME/bin:"*) ;;
    *) [ -d "$MANIM_VIDEO_HOME/bin" ] && PATH="$MANIM_VIDEO_HOME/bin:$PATH" ;;
  esac
fi
export PATH MANIM_VIDEO_HOME

MANIM_VERSION="${MANIM_VERSION:-0.22.1}"
# Container route (the default): image tag, pulled (render-in-container.sh --pull) or built from
# ../docker/ (--build).
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
