#!/bin/bash
set -eo pipefail

image_name=$1
push=0
if [[ $2 == "--push" ]]; then
  push=1
fi

echo -e "\n\n======\nBuilding $image_name\n"
tags=(latest)
if [[ -n $GITHUB_REF_NAME ]]; then
  # check if ref name is a version number
  if [[ $GITHUB_REF_NAME =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    major_version=$(echo $GITHUB_REF_NAME | cut -d. -f1)
    minor_version=$(echo $GITHUB_REF_NAME | cut -d. -f1,2)
    tags+=($major_version $minor_version)
  fi
  tags+=(echo $GITHUB_REF_NAME | sed 's/[^a-zA-Z0-9.-]\+/-/g')
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
echo "Repo: $DOCKER_REPOSITORY"
echo "Base dir: $DOCKER_BASE_DIR"
docker pull $DOCKER_REPOSITORY:main || true # try to get any cached layers
tag_args=""
for tag in ${tags[@]}; do
  tag_args+=" -t $DOCKER_REPOSITORY:$tag"
done

docker buildx build \
  $tag_args \
  --platform linux/amd64,linux/arm64 \
  -f $dir/Dockerfile $DOCKER_BASE_DIR

if [[ $push -eq 1 ]]; then
  for tag in ${tags[@]}; do
    docker push $DOCKER_REPOSITORY:$tag
  done
fi
