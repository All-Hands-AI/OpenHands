#!/bin/bash
# args: <custom_base_image> <custom_image_tag>

set -euo pipefail

###
OPENHANDS_WORKSPACE=$(git rev-parse --show-toplevel)

cd "$OPENHANDS_WORKSPACE/" || exit 1

# custom sandbox base image
IMAGE="${1:-nikolaik/python-nodejs:python3.12-nodejs22}"
# custom sandbox image tag
TAG="${2:-custom-sandbox:latest}"

mkdir -p "$OPENHANDS_WORKSPACE/containers/custom-sandbox/local"

poetry run python3 openhands/runtime/utils/runtime_build.py \
	--base_image "$IMAGE" \
	--build_folder ./containers/custom-sandbox/local

docker buildx build \
	--progress "plain" \
	--tag "$TAG" \
	--load \
	./containers/custom-sandbox/local

###
