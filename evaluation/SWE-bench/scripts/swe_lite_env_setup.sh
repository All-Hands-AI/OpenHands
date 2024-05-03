#!/bin/bash
# THIS SCRIPT ONLY NEED TO BE RUN ONCE BEFORE EVALUATION

EVAL_DOCKER_IMAGE=ghcr.io/opendevin/eval-swe-bench:latest
EVAL_WORKSPACE="evaluation/SWE-bench/eval_workspace"
EVAL_WORKSPACE=$(realpath $EVAL_WORKSPACE)

if [ ! -d $EVAL_WORKSPACE ]; then
    mkdir -p $EVAL_WORKSPACE
fi

if [ -f $EVAL_WORKSPACE/swe_lite_env_setup.sh ]; then
    rm $EVAL_WORKSPACE/swe_lite_env_setup.sh
fi
cp evaluation/SWE-bench/scripts/_swe_lite_env_setup.sh $EVAL_WORKSPACE/swe_lite_env_setup.sh
cp evaluation/SWE-bench/scripts/swe_entry.sh $EVAL_WORKSPACE/swe_entry.sh

docker run \
    -v $EVAL_WORKSPACE:/swe_util \
    -e UID=$(id -u) \
    --rm -it $EVAL_DOCKER_IMAGE \
    bash -c "useradd -rm -d /home/opendevin -s /bin/bash -u $(id -u) opendevin && su opendevin -c 'bash /swe_util/swe_lite_env_setup.sh'"
#
