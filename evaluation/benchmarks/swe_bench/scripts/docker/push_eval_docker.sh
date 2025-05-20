#!/usr/bin/env bash

# This is ONLY used for pushing docker images created by https://github.com/princeton-nlp/SWE-bench/blob/main/docs/20240627_docker/README.md

DOCKER_NAMESPACE=$1
# check if DOCKER_NAMESPACE is set
if [ -z "$DOCKER_NAMESPACE" ]; then
    echo "Usage: $0 <docker_namespace>"
    exit 1
fi

# target namespace
image_list=$(docker image ls --format '{{.Repository}}:{{.Tag}}' | grep sweb | grep -v $DOCKER_NAMESPACE)

# There are three tiers of images
# - base
# - env
# - eval (instance level)

for image in $image_list; do
    echo "=============================="
    echo "Image: $image"
    # rename image by replace "__" with "_s_" to comply with docker naming convention
    new_image_name=${image//__/_s_}
    docker tag $image $DOCKER_NAMESPACE/$new_image_name
    echo "Tagged $image to $DOCKER_NAMESPACE/$new_image_name"

    docker push $DOCKER_NAMESPACE/$new_image_name
    echo "Pushed $DOCKER_NAMESPACE/$new_image_name"
done
