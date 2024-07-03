FROM  us-docker.pkg.dev/coherence-public/public/cnc_base

ARG CNC_VERSION="0.1.68"

RUN --mount=type=cache,target=/root/.cache/pip \
    pip cache purge && \
    pip install --no-cache-dir cocnc==${CNC_VERSION}
