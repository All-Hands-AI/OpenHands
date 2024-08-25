#!/bin/bash
set -eo pipefail

image_name=$1
org_name=$2
push=0
if [[ $3 == "--push" ]]; then
  push=1
fi
tag_suffix=$4

echo "Building: $image_name"
tags=()

OPENHANDS_BUILD_VERSION="dev"

cache_tag_base="buildcache"
cache_tag="$cache_tag_base"

if [[ -n $GITHUB_SHA ]]; then
  git_hash=$(git rev-parse --short "$GITHUB_SHA")
  tags+=("$git_hash")
fi

if [[ -n $GITHUB_REF_NAME ]]; then
  # check if ref name is a version number
  if [[ $GITHUB_REF_NAME =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    major_version=$(echo "$GITHUB_REF_NAME" | cut -d. -f1)
    minor_version=$(echo "$GITHUB_REF_NAME" | cut -d. -f1,2)
    tags+=("$major_version" "$minor_version")
    tags+=("latest")
  fi
  sanitized_ref_name=$(echo "$GITHUB_REF_NAME" | sed 's/[^a-zA-Z0-9.-]\+/-/g')
  OPENHANDS_BUILD_VERSION=$sanitized_ref_name
  sanitized_ref_name=$(echo "$sanitized_ref_name" | tr '[:upper:]' '[:lower:]') # lower case is required in tagging
  tags+=("$sanitized_ref_name")
  cache_tag+="-${sanitized_ref_name}"
fi

if [[ -n $tag_suffix ]]; then
  cache_tag+="-${tag_suffix}"
  for i in "${!tags[@]}"; do
    tags[$i]="${tags[$i]}-$tag_suffix"
  done
fi

echo "Tags: ${tags[@]}"

if [[ "$image_name" == "openhands" ]]; then
  dir="./containers/app"
elif [[ "$image_name" == "runtime" ]]; then
  dir="./containers/runtime"
else
  dir="./containers/$image_name"
fi

if [[ (! -f "$dir/Dockerfile") && "$image_name" != "runtime" ]]; then
  # Allow runtime to be built without a Dockerfile
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

# If $DOCKER_IMAGE_HASH_TAG is set, add it to the tags
if [[ -n "$DOCKER_IMAGE_HASH_TAG" ]]; then
  tags+=("$DOCKER_IMAGE_HASH_TAG")
fi
# If $DOCKER_IMAGE_TAG is set, add it to the tags
if [[ -n "$DOCKER_IMAGE_TAG" ]]; then
  tags+=("$DOCKER_IMAGE_TAG")
fi

DOCKER_REPOSITORY="$DOCKER_REGISTRY/$DOCKER_ORG/$DOCKER_IMAGE"
DOCKER_REPOSITORY=${DOCKER_REPOSITORY,,} # lowercase
echo "Repo: $DOCKER_REPOSITORY"
echo "Base dir: $DOCKER_BASE_DIR"

args=""
for tag in "${tags[@]}"; do
  args+=" -t $DOCKER_REPOSITORY:$tag"
done

if [[ $push -eq 1 ]]; then
  args+=" --push"
  args+=" --cache-to=type=registry,ref=$DOCKER_REPOSITORY:$cache_tag,mode=max"
fi

echo "Args: $args"

docker buildx build \
  $args \
  --build-arg OPENHANDS_BUILD_VERSION="$OPENHANDS_BUILD_VERSION" \
  --cache-from=type=registry,ref=$DOCKER_REPOSITORY:$cache_tag \
  --cache-from=type=registry,ref=$DOCKER_REPOSITORY:$cache_tag_base-main \
  --platform linux/amd64,linux/arm64 \
  --provenance=false \
  -f "$dir/Dockerfile" \
  "$DOCKER_BASE_DIR"
