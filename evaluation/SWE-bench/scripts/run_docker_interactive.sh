#!/bin/bash

DOCKER_IMAGE=ghcr.io/opendevin/eval-swe-bench:v0.1
WORK_DIR=`pwd`

docker run \
    -it \
    --rm \
    --user root \
    --ipc=host --ulimit memlock=-1 --ulimit stack=67108864 \
    -v $WORK_DIR:/swe-bench \
    -w /swe-bench \
    $DOCKER_IMAGE \
    /bin/bash -c "usermod -u $(id -u) swe-bench && su swe-bench"
