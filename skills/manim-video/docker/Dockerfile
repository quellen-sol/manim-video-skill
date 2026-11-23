# manim-video render image (tag: manim-video:local).
#
# The canonical renderer for the manim-video skill. An agent writes a job directory (scene.py,
# job.json, optional assets/) and scripts/render-in-container.sh runs this image on it through
# docker/compose.yml. The contract is in references/container.md.
#
# Contents: Manim Community 0.22.1, manim-voiceover 0.4.0, the skill's helpers (KokoroService,
# LayoutGuard, frames.py, qa_check.py, narrate_mux.py), ffmpeg/ffprobe, TeX Live 2023 (latex-base,
# latex-extra, fonts-recommended, science, tipa) with dvisvgm, Cairo/Pango with Noto fonts, Mesa
# EGL/GL (llvmpipe on CPU, iris on an Intel iGPU) and Intel VA-API (iHD driver, vainfo).
#
# Platforms: linux/amd64 and linux/arm64 (Apple Silicon under Docker Desktop, arm64 Linux). The
# same digest, snapshot and lock serve both: the base digest is a multi-arch index, the snapshot
# service carries the arm64 (ports) archive under the same URL, and docker/requirements.lock holds
# hashes for every wheel and sdist (on arm64, glcontext and moderngl build from their sdists with
# g++ only). amd64-only: the Intel VA-API driver (intel-media-va-driver). Docker builds for the
# host's own platform by default; cross-build with `docker buildx build --platform linux/arm64`.
#
# Reproducible inputs:
#   - the base image is pinned by digest (UBUNTU_DIGEST);
#   - every apt install resolves against one dated snapshot of the Ubuntu archive
#     (snapshot.ubuntu.com, APT_SNAPSHOT), so package versions do not drift;
#   - Python packages are pinned with hashes in docker/requirements.lock (uv pip compile).
# Layers are not byte-identical across builds (file timestamps differ); the software is.
#
# Build context: the skill directory (the parent of docker/). Build with
#   scripts/render-in-container.sh --build        (or: docker compose -f docker/compose.yml build)

ARG UBUNTU_DIGEST=sha256:9c7f200c07e3d4a03e7249d2c16bf66a51120fb876aa2242cf31451412543289
ARG APT_SNAPSHOT=20261120T000000Z

FROM ubuntu:24.04@${UBUNTU_DIGEST} AS base
ARG APT_SNAPSHOT
ARG TARGETARCH
ENV DEBIAN_FRONTEND=noninteractive LANG=C.UTF-8 LC_ALL=C.UTF-8
# The snapshot service is HTTPS-only and the base image has no CA bundle, so bootstrap
# ca-certificates from the frozen noble release pocket (it never changes; amd64 lives on
# archive.ubuntu.com, arm64 on ports.ubuntu.com), then point apt at the dated snapshot only.
# Package integrity comes from the archive's GPG signatures either way.
RUN case "${TARGETARCH:-amd64}" in \
      amd64|i386) BOOT=http://archive.ubuntu.com/ubuntu ;; \
      *) BOOT=http://ports.ubuntu.com/ubuntu-ports ;; \
    esac \
 && echo "deb [signed-by=/usr/share/keyrings/ubuntu-archive-keyring.gpg] $BOOT noble main" > /tmp/boot.list \
 && apt-get -o Dir::Etc::SourceList=/tmp/boot.list -o Dir::Etc::SourceParts=/nonexistent update \
 && apt-get -o Dir::Etc::SourceList=/tmp/boot.list -o Dir::Etc::SourceParts=/nonexistent \
      install -y --no-install-recommends ca-certificates \
 && rm -rf /var/lib/apt/lists/* /tmp/boot.list \
 && printf '%s\n' "Types: deb" "URIs: https://snapshot.ubuntu.com/ubuntu/${APT_SNAPSHOT}/" \
      "Suites: noble noble-updates noble-security" "Components: main universe restricted multiverse" \
      "Signed-By: /usr/share/keyrings/ubuntu-archive-keyring.gpg" > /etc/apt/sources.list.d/ubuntu.sources

# ---- build stage: wheels that compile against the Cairo and Pango headers ------------------
FROM base AS build
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      ca-certificates python3.12 python3.12-venv python3.12-dev build-essential pkg-config \
      libcairo2-dev libpango1.0-dev \
 && rm -rf /var/lib/apt/lists/*
COPY docker/requirements.lock /tmp/requirements.lock
RUN python3.12 -m venv /opt/venv \
 && /opt/venv/bin/pip install --no-cache-dir --require-hashes --no-deps -r /tmp/requirements.lock \
 && /opt/venv/bin/pip check

# ---- runtime stage ---------------------------------------------------------------------------
FROM base AS runtime
ARG TARGETARCH
# amd64-only packages: the Intel VA-API driver (h264_vaapi on Intel iGPUs).
RUN ARCH_PKGS="" \
 && case "${TARGETARCH:-amd64}" in amd64) ARCH_PKGS="intel-media-va-driver" ;; esac \
 && apt-get update \
 && apt-get install -y --no-install-recommends \
      ca-certificates python3.12 \
      libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libpangoft2-1.0-0 fontconfig \
      fonts-noto-core fonts-noto-mono fonts-dejavu-core \
      ffmpeg sox \
      texlive-latex-base texlive-latex-extra texlive-fonts-recommended texlive-science \
      dvisvgm tipa \
      libegl1 libgl1 libegl-mesa0 libgl1-mesa-dri libgbm1 \
      vainfo $ARCH_PKGS \
 && rm -rf /var/lib/apt/lists/* \
 && fc-cache -f \
 && { userdel --remove ubuntu 2>/dev/null || true; } \
 && groupadd --gid 1000 manim \
 && useradd --uid 1000 --gid 1000 --no-create-home --home-dir /tmp/home --shell /usr/sbin/nologin manim

COPY --from=build /opt/venv /opt/venv

ENV PATH=/opt/venv/bin:$PATH \
    PYTHONPATH=/opt/manim-video/scripts \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOME=/tmp/home \
    XDG_CACHE_HOME=/tmp/cache \
    TEXMFVAR=/tmp/cache/texmf-var \
    TZ=Etc/UTC \
    MANIM_VIDEO_IMAGE=1

COPY scripts/*.py /opt/manim-video/scripts/
COPY docker/manim_job.py /usr/local/bin/manim-job
RUN chmod -R u=rwX,go=rX /opt/manim-video /usr/local/bin/manim-job \
 && chmod 0755 /usr/local/bin/manim-job \
 && python3 -m compileall -q /opt/manim-video/scripts \
 && dpkg-query -W -f '${Package}=${Version}\n' > /opt/manim-video/apt-packages.txt \
 && pip freeze --all > /opt/manim-video/python-packages.txt \
 && manim --version | grep -q 'v0.22.1'

ARG APT_SNAPSHOT
ARG SOURCE_SHA=unknown
LABEL org.opencontainers.image.title="manim-video" \
      org.opencontainers.image.description="Manim Community render image for the manim-video skill" \
      org.opencontainers.image.licenses="MIT" \
      org.manim-video.manim="0.22.1" \
      org.manim-video.manim-voiceover="0.4.0" \
      org.manim-video.apt-snapshot="${APT_SNAPSHOT}" \
      org.manim-video.arch="${TARGETARCH}" \
      org.manim-video.source-sha="${SOURCE_SHA}"

USER 1000:1000
WORKDIR /job
ENTRYPOINT ["/usr/local/bin/manim-job"]
CMD ["render"]
