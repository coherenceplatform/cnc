FROM  us-docker.pkg.dev/coherence-public/public/cnc_base

ARG CNC_VERSION="0.1.40"

RUN pip cache purge && \
    pip install --no-cache-dir cocnc==${CNC_VERSION}
