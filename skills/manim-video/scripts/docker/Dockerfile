# Derived render image for the manim-video skill.
# Base: the official Manim Community image (Manim 0.22.1, TeX Live, Python in /opt/venv).
# Adds: manim-voiceover (narration sync), plus ffmpeg and sox CLIs so audio helpers work
# inside the container too. Build with scripts/setup_env.sh (or:
#   docker build -t manim-video:0.22.1 docker/ ).
ARG MANIM_IMAGE=manimcommunity/manim:v0.22.1
FROM ${MANIM_IMAGE}
USER root
RUN apt-get update \
 && apt-get install -y --no-install-recommends ffmpeg sox \
 && rm -rf /var/lib/apt/lists/* \
 && /opt/venv/bin/python -m pip install --no-cache-dir "manim-voiceover==0.4.0"
USER manimuser
WORKDIR /manim
