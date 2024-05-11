#!/bin/bash
# THIS SCRIPT ONLY NEED TO BE RUN ONCE BEFORE EVALUATION

EVAL_DOCKER_IMAGE=ghcr.io/opendevin/eval-swe-bench:builder
EVAL_WORKSPACE="evaluation/swe_bench/eval_workspace"
EVAL_WORKSPACE=$(realpath $EVAL_WORKSPACE)

SETUP_INSTANCE_FILENAME=swe-bench-test.json # OR swe-bench-test-lite.json

if [ ! -d $EVAL_WORKSPACE ]; then
    mkdir -p $EVAL_WORKSPACE
fi

if [ -f $EVAL_WORKSPACE/swe_env_setup.sh ]; then
    rm $EVAL_WORKSPACE/swe_env_setup.sh
fi
cp evaluation/swe_bench/scripts/_swe_env_setup.sh $EVAL_WORKSPACE/swe_env_setup.sh
cp evaluation/swe_bench/scripts/swe_entry.sh $EVAL_WORKSPACE/swe_entry.sh
cp evaluation/swe_bench/scripts/get_model_report.sh $EVAL_WORKSPACE/get_model_report.sh
cp evaluation/swe_bench/scripts/get_agent_report.sh $EVAL_WORKSPACE/get_agent_report.sh
cp evaluation/swe_bench/scripts/process_output_json_file.py $EVAL_WORKSPACE/process_output_json_file.py
cp evaluation/swe_bench/scripts/merge_fine_grained_report.py $EVAL_WORKSPACE/merge_fine_grained_report.py

docker run \
    -v $EVAL_WORKSPACE:/swe_util \
    -e UID=$(id -u) \
    --rm -it $EVAL_DOCKER_IMAGE \
    bash -c "useradd -rm -d /home/opendevin -s /bin/bash -u $(id -u) opendevin && su opendevin -c 'bash /swe_util/swe_env_setup.sh $SETUP_INSTANCE_FILENAME'"
#
