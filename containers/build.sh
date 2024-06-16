#!/bin/bash
set -eo pipefail

image_name=$1
org_name=$2
platform=$3

echo "Building: $image_name for platform: $platform"
tags=()

OPEN_DEVIN_BUILD_VERSION="dev"

cache_tag_base="buildcache"
cache_tag="$cache_tag_base"

if [[ -n $GITHUB_REF_NAME ]]; then
  # check if ref name is a version number
  if [[ $GITHUB_REF_NAME =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    major_version=$(echo "$GITHUB_REF_NAME" | cut -d. -f1)
    minor_version=$(echo "$GITHUB_REF_NAME" | cut -d. -f1,2)
    tags+=("$major_version" "$minor_version")
  fi
  sanitized=$(echo "$GITHUB_REF_NAME" | sed 's/[^a-zA-Z0-9.-]\+/-/g')
  OPEN_DEVIN_BUILD_VERSION=$sanitized
  cache_tag+="-${sanitized}"
  tags+=("$sanitized")
fi
echo "Tags: ${tags[@]}"

if [[ "$image_name" == "opendevin" ]]; then
  dir="./containers/app"
else
  dir="./containers/$image_name"
fi

if [[ ! -f "$dir/Dockerfile" ]]; then
  echo "No Dockerfile found"
  exit 1
fi
if [[ ! -f "$dir/config.sh" ]]; then
  echo "No config.sh found for Dockerfile"
  exit 1
fi

source "$dir/config.sh"

if [[ -n "$org_name" ]]; then
  DOCKER_ORG="$org_name"
fi

echo "Base dir: $DOCKER_BASE_DIR"

output_image="/tmp/${image_name}_image_${platform}.tar"

docker buildx build \
  --build-arg OPEN_DEVIN_BUILD_VERSION="$OPEN_DEVIN_BUILD_VERSION" \
  --platform linux/$platform \
  --provenance=false \
  -f "$dir/Dockerfile" \
  --output type=docker,dest="$output_image" \
  "$DOCKER_BASE_DIR"

echo "${tags[*]}" > tags.txt
