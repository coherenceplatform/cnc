# Building the cnc image

```bash
# From the base directory of this repository

# base image all others are based on
docker build -t cnc_base -f cncbuilder/Dockerfile.base .

# Builds "prod" image (installs cnc from pypi)
docker build -t us-docker.pkg.dev/coherence-public/public/cnc -f cncbuilder/Dockerfile .

# Builds "dev" image (installs cnc from local fs)
docker build -t my_cnc_dev_image -f cncbuilder/Dockerfile.dev .
```
