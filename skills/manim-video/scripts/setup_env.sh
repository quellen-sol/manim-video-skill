#!/usr/bin/env bash
# Install the manim-video toolchain in user space. No root, no sudo, no system packages.
#
# Usage: setup_env.sh [--no-ffmpeg] [--no-docker]
#
#  1. ffmpeg + ffprobe: if not already on PATH, downloads the static Linux amd64 build from
#     johnvansickle.com into $MANIM_VIDEO_HOME/bin (default ~/.local/share/manim-video/bin) after an
#     md5 check. Used by frames.py, qa_check.py and narrate_mux.py on the host.
#  2. Docker image: pulls manimcommunity/manim:v0.22.1 (Manim + TeX Live) and builds the derived
#     image manim-video:0.22.1 (adds manim-voiceover, ffmpeg, sox) from scripts/docker/Dockerfile.
#     Needs membership of the docker group; runs no long-lived container.
#
# Idempotent: steps already done are skipped. If something needs root (for example a local Manim
# install needs libcairo2-dev and libpango1.0-dev), this script stops and says so instead.
set -euo pipefail
# shellcheck source=_env.sh
. "$(dirname "${BASH_SOURCE[0]}")/_env.sh"

DO_FFMPEG=1; DO_DOCKER=1
for a in "$@"; do
  case "$a" in
    --no-ffmpeg) DO_FFMPEG=0 ;;
    --no-docker) DO_DOCKER=0 ;;
    -h|--help) sed -n '2,16p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "setup_env.sh: unknown option $a" >&2; exit 2 ;;
  esac
done

mkdir -p "$MANIM_VIDEO_HOME/bin"

if [ $DO_FFMPEG -eq 1 ]; then
  if works ffmpeg && works ffprobe; then
    echo "ffmpeg: present ($(command -v ffmpeg))"
  elif [ "$(uname -s)-$(uname -m)" != "Linux-x86_64" ]; then
    echo "ffmpeg: missing, and no static build is configured for $(uname -s)-$(uname -m)." >&2
    echo "  Install ffmpeg with your package manager (or ask an administrator), then re-run." >&2
    exit 1
  else
    URL="${FFMPEG_STATIC_URL:-https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz}"
    DL="$MANIM_VIDEO_HOME/downloads/ffmpeg-static"
    mkdir -p "$DL"
    echo "ffmpeg: downloading $URL"
    curl -fsSL -o "$DL/ffmpeg.tar.xz" "$URL"
    curl -fsSL -o "$DL/ffmpeg.tar.xz.md5" "$URL.md5"
    (cd "$DL" && echo "$(awk '{print $1}' ffmpeg.tar.xz.md5)  ffmpeg.tar.xz" | md5sum -c -)
    TOP="$(tar -tJf "$DL/ffmpeg.tar.xz" | head -1 | cut -d/ -f1)"
    tar -xJf "$DL/ffmpeg.tar.xz" -C "$MANIM_VIDEO_HOME/bin" --strip-components=1 "$TOP/ffmpeg" "$TOP/ffprobe"
    echo "ffmpeg: installed $("$MANIM_VIDEO_HOME/bin/ffmpeg" -version | head -1 | awk '{print $3}') into $MANIM_VIDEO_HOME/bin"
  fi
fi

if [ $DO_DOCKER -eq 1 ]; then
  if ! docker_ok; then
    echo "docker: not usable by this user. Options:" >&2
    echo "  - ask an administrator to add you to the docker group (needs root), or" >&2
    echo "  - install Manim Community locally (needs libcairo2-dev, libpango1.0-dev, pkg-config;" >&2
    echo "    see references/environment.md), then use MANIM_BACKEND=local." >&2
    exit 1
  fi
  if docker image inspect "$MANIM_BASE_IMAGE" >/dev/null 2>&1; then
    echo "docker: base image $MANIM_BASE_IMAGE present"
  else
    echo "docker: pulling $MANIM_BASE_IMAGE"
    docker pull "$MANIM_BASE_IMAGE"
  fi
  if docker image inspect "$MANIM_IMAGE" >/dev/null 2>&1; then
    echo "docker: derived image $MANIM_IMAGE present"
  else
    echo "docker: building $MANIM_IMAGE (adds manim-voiceover, ffmpeg, sox)"
    docker build --build-arg "MANIM_IMAGE=$MANIM_BASE_IMAGE" -t "$MANIM_IMAGE" "$SCRIPTS_DIR/docker"
  fi
fi

echo
"$SCRIPTS_DIR/check_env.sh"
