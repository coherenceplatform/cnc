FROM  us-docker.pkg.dev/coherence-public/public/cnc_base

ARG CNC_VERSION="0.1.40"

RUN pip install --no-cache-dir --upgrade pip && \
    pip cache purge && \
    pip install cocnc==${CNC_VERSION}
