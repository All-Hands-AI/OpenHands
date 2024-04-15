#!/bin/bash
set -eo pipefail

echo "Building docker images..."
tags=(latest)
if [[ -n $GITHUB_REF_NAME ]]; then
  # check if ref name is a version number
  if [[ $GITHUB_REF_NAME =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    major_version=$(echo $GITHUB_REF_NAME | cut -d. -f1)
    minor_version=$(echo $GITHUB_REF_NAME | cut -d. -f1,2)
    tags+=($major_version $minor_version)
  fi
  tags+=($GITHUB_REF_NAME)
fi
echo "Tags: ${tags[@]}"

for dir in ./containers/*; do
  echo -e "\n\n======\nBuilding $dir\n"
  if [ ! -f $dir/Dockerfile ]; then
    echo "No Dockerfile found, skipping"
    break
  fi
  if [ ! -f $dir/config.sh ]; then
    echo "No config.sh found for Dockerfile, skipping"
    break
  fi
  source $dir/config.sh
  echo "Repo: $DOCKER_REPOSITORY"
  echo "Base dir: $DOCKER_BASE_DIR"
  docker pull $DOCKER_REPOSITORY:main || true # try to get any cached layers
  tag_args=""
  for tag in ${tags[@]}; do
    tag_args+=" -t $DOCKER_REPOSITORY:$tag"
  done
  docker build $tag_args -f $dir/Dockerfile $DOCKER_BASE_DIR
  if [[ $1 == "--push" ]]; then
    for tag in ${tags[@]}; do
      docker push $DOCKER_REPOSITORY:$tag
    done
  fi
done
