#!/usr/bin/env bash
# Set up the manim-video toolchain. No root, no sudo, no system packages.
#
# Usage: setup_env.sh [--host] [--no-image]
#
#  default   build the render image manim-video:local from ../docker/ (the container route, the
#            default way to render). Needs Docker with the compose plugin and membership of the
#            docker group. Takes about 6 minutes the first time; later runs reuse the build cache.
#  --host    also set up the host route (a fallback for local testing and comparisons):
#            a venv at $MANIM_HOST_VENV with the same pinned Python packages as the image
#            (docker/requirements.lock), and, only if the system ffmpeg is missing or broken, a
#            static ffmpeg/ffprobe in $MANIM_VIDEO_HOME/bin. The host route needs system packages
#            that this script cannot install (it reports what is missing): python3-venv and
#            python3-dev, libcairo2-dev, libpango1.0-dev, pkg-config, a C compiler, and LaTeX
#            (texlive-latex-extra, texlive-fonts-recommended, texlive-science, tipa, dvisvgm).
#  --no-image  skip the image build
#
# Idempotent. Ends by running check_env.sh.
set -euo pipefail
# shellcheck source=_env.sh
. "$(dirname "${BASH_SOURCE[0]}")/_env.sh"

DO_HOST=0; DO_IMAGE=1
for a in "$@"; do
  case "$a" in
    --host) DO_HOST=1 ;;
    --no-image) DO_IMAGE=0 ;;
    -h|--help) sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "setup_env.sh: unknown option $a" >&2; exit 2 ;;
  esac
done

if [ $DO_IMAGE -eq 1 ]; then
  if ! docker_ok; then
    echo "image: Docker is not usable by this user (not installed, daemon down, or not in the docker group)." >&2
    echo "  Ask an administrator, or use the host route: setup_env.sh --host --no-image" >&2
    exit 1
  fi
  "$SCRIPTS_DIR/render-in-container.sh" --build
fi

if [ $DO_HOST -eq 1 ]; then
  echo "host route:"
  MISSING=()
  have python3 && python3 -c 'import sys, venv; sys.exit(sys.version_info < (3, 11))' 2>/dev/null \
    || MISSING+=("python3 >= 3.11 with venv (python3-venv)")
  PYINC="$(python3 -c 'import sysconfig; print(sysconfig.get_paths()["include"])' 2>/dev/null || true)"
  [ -n "$PYINC" ] && [ -f "$PYINC/Python.h" ] || MISSING+=("Python headers (python3-dev)")
  have pkg-config && pkg-config --exists cairo 2>/dev/null || MISSING+=("Cairo headers (libcairo2-dev, pkg-config)")
  have pkg-config && pkg-config --exists pangocairo 2>/dev/null || MISSING+=("Pango headers (libpango1.0-dev)")
  have cc || MISSING+=("a C compiler (build-essential)")
  have latex || MISSING+=("LaTeX (texlive-latex-extra texlive-fonts-recommended texlive-science tipa)")
  have dvisvgm || MISSING+=("dvisvgm")
  if [ ${#MISSING[@]} -gt 0 ]; then
    echo "  The host route needs system packages this script cannot install (no root):" >&2
    printf '    - %s\n' "${MISSING[@]}" >&2
    echo "  Ask an administrator to install them, or keep using the container route." >&2
    exit 1
  fi
  if [ -x "$MANIM_HOST_VENV/bin/manim" ] && "$MANIM_HOST_VENV/bin/manim" --version 2>/dev/null | grep -q "v$MANIM_VERSION"; then
    echo "  venv: $MANIM_HOST_VENV already has Manim Community v$MANIM_VERSION"
  else
    echo "  venv: creating $MANIM_HOST_VENV"
    python3 -m venv "$MANIM_HOST_VENV"
    LOCK="$SKILL_DIR/docker/requirements.lock"
    if python3 -c 'import sys; sys.exit(sys.version_info[:2] != (3, 12))' && [ "$(uname -m)" = x86_64 ]; then
      # Same pinned, hash-checked packages as the image (the lock targets CPython 3.12 on x86_64).
      "$MANIM_HOST_VENV/bin/pip" install --no-cache-dir --require-hashes --no-deps -r "$LOCK"
    else
      echo "  note: the lock file targets CPython 3.12 on x86_64; installing unpinned dependencies" >&2
      "$MANIM_HOST_VENV/bin/pip" install --no-cache-dir "manim==$MANIM_VERSION" "manim-voiceover==0.4.0"
    fi
    "$MANIM_HOST_VENV/bin/manim" --version 2>/dev/null | grep -q "v$MANIM_VERSION" \
      || { echo "  venv: manim did not install correctly" >&2; exit 1; }
  fi
  if works ffmpeg && works ffprobe; then
    echo "ffmpeg: present ($(command -v ffmpeg))"
  elif [ "$(uname -s)-$(uname -m)" != "Linux-x86_64" ]; then
    echo "ffmpeg: missing, and no static build is configured for $(uname -s)-$(uname -m)." >&2
    echo "  Install ffmpeg with your package manager (or ask an administrator), then re-run." >&2
    exit 1
  else
    URL="${FFMPEG_STATIC_URL:-https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz}"
    DL="$MANIM_VIDEO_HOME/downloads/ffmpeg-static"
    mkdir -p "$DL" "$MANIM_VIDEO_HOME/bin"
    echo "ffmpeg: downloading $URL"
    curl -fsSL -o "$DL/ffmpeg.tar.xz" "$URL"
    curl -fsSL -o "$DL/ffmpeg.tar.xz.md5" "$URL.md5"
    (cd "$DL" && echo "$(awk '{print $1}' ffmpeg.tar.xz.md5)  ffmpeg.tar.xz" | md5sum -c -)
    TOP="$(tar -tJf "$DL/ffmpeg.tar.xz" | head -1 | cut -d/ -f1)"
    tar -xJf "$DL/ffmpeg.tar.xz" -C "$MANIM_VIDEO_HOME/bin" --strip-components=1 "$TOP/ffmpeg" "$TOP/ffprobe"
    echo "ffmpeg: installed $("$MANIM_VIDEO_HOME/bin/ffmpeg" -version | head -1 | awk '{print $3}') into $MANIM_VIDEO_HOME/bin"
  fi
fi


echo
if [ $DO_HOST -eq 1 ]; then "$SCRIPTS_DIR/check_env.sh" --host; else "$SCRIPTS_DIR/check_env.sh"; fi
