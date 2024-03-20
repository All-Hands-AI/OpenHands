#!/bin/bash

DOCKER_IMAGE=opendevin/eval-swe-bench:v0.1
WORK_DIR=`pwd`

docker run \
    -it \
    --rm \
    --user $(id -u):$(id -g) \
    --ipc=host --ulimit memlock=-1 --ulimit stack=67108864 \
    -v $WORK_DIR:/swe-bench \
    $DOCKER_IMAGE \
    bash -c "cd /swe-bench && bash"
