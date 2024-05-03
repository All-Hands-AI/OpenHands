#!/bin/bash
set -eo pipefail

image_name=$1
org_name=$2
push=0
if [[ $3 == "--push" ]]; then
  push=1
fi

echo -e "Building: $image_name"
tags=()

OPEN_DEVIN_BUILD_VERSION="dev"

cache_tag_base="buildcache"
cache_tag="$cache_tag_base"

if [[ -n $GITHUB_REF_NAME ]]; then
  # check if ref name is a version number
  if [[ $GITHUB_REF_NAME =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    major_version=$(echo $GITHUB_REF_NAME | cut -d. -f1)
    minor_version=$(echo $GITHUB_REF_NAME | cut -d. -f1,2)
    tags+=($major_version $minor_version)
  fi
  sanitized=$(echo $GITHUB_REF_NAME | sed 's/[^a-zA-Z0-9.-]\+/-/g')
  OPEN_DEVIN_BUILD_VERSION=$sanitized
  cache_tag+="-${sanitized}"
  tags+=($sanitized)
fi
echo "Tags: ${tags[@]}"

dir=./containers/$image_name
if [ ! -f $dir/Dockerfile ]; then
  echo "No Dockerfile found"
  exit 1
fi
if [ ! -f $dir/config.sh ]; then
  echo "No config.sh found for Dockerfile"
  exit 1
fi
source $dir/config.sh
if [[ -n "$org_name" ]]; then
  DOCKER_ORG="$org_name"
fi
DOCKER_REPOSITORY=$DOCKER_REGISTRY/$DOCKER_ORG/$DOCKER_IMAGE
DOCKER_REPOSITORY=${DOCKER_REPOSITORY,,} # lowercase
echo "Repo: $DOCKER_REPOSITORY"
echo "Base dir: $DOCKER_BASE_DIR"

args=""
for tag in ${tags[@]}; do
  args+=" -t $DOCKER_REPOSITORY:$tag"
done
if [[ $push -eq 1 ]]; then
  args+=" --push"
  args+=" --cache-to=type=registry,ref=$DOCKER_REPOSITORY:$cache_tag,mode=max"
fi

docker buildx build \
  $args \
  --build-arg OPEN_DEVIN_BUILD_VERSION=$OPEN_DEVIN_BUILD_VERSION \
  --cache-from=type=registry,ref=$DOCKER_REPOSITORY:$cache_tag \
  --cache-from=type=registry,ref=$DOCKER_REPOSITORY:$cache_tag_base-main \
  --platform linux/amd64,linux/arm64 \
  --provenance=false \
  -f $dir/Dockerfile $DOCKER_BASE_DIR
