# Docker Build Guide

## Builder

This constructs docker container used for `evaluation/swe_bench/scripts/prepare_swe_utils.sh` that downloads the datasets.

```bash
pushd evaluation/swe_bench
# This builds base image with basic dependencies
docker build -t ghcr.io/opendevin/eval-swe-bench:builder -f ./scripts/docker/Dockerfile.builder .
# This builds image with SWE-Bench conda environment pre-installed
docker build -t ghcr.io/opendevin/eval-swe-bench:builder_with_conda -f ./scripts/docker/Dockerfile.builder_with_conda .
```
