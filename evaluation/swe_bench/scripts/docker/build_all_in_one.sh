#!/bin/bash

pushd evaluation/SWE-bench
docker build -t ghcr.io/opendevin/eval-swe-bench-all:lite-v1.0 -f ./scripts/docker/Dockerfile.all-in-one .
