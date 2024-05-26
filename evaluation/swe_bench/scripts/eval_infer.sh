#!/bin/bash

PROCESS_FILEPATH=$1
if [ -z "$PROCESS_FILEPATH" ]; then
    echo "Error: PROCESS_FILEPATH is empty. Usage: ./eval_infer.sh <output_file>"
    exit 1
fi

if [ ! -f $PROCESS_FILEPATH ]; then
    echo "Error: $PROCESS_FILEPATH is not a file"
    exit 1
fi

PROCESS_FILEPATH=$(realpath $PROCESS_FILEPATH)
FILE_DIR=$(dirname $PROCESS_FILEPATH)
FILE_NAME=$(basename $PROCESS_FILEPATH)
mkdir -p $FILE_DIR/eval_logs
mkdir -p $FILE_DIR/swe_bench_format

echo "Evaluating $FILE_NAME @ $FILE_DIR"
echo "Merged output file with fine-grained report will be saved to $FILE_DIR"

docker run --rm \
    -v $FILE_DIR:/swe_bench_output \
    -e MINICONDA3=/swe_util/miniforge3 \
    -e OD_SWE_BENCH=/swe_util/OD-SWE-bench \
    -e EVAL_DATA_DIR=/swe_util/eval_data \
    -w /swe_util \
    ghcr.io/opendevin/eval-swe-bench:full-v1.2.1 \
    bash -c "./get_agent_report.sh --output-file /swe_bench_output/$FILE_NAME \
    --agent-name CodeActAgent \
    --dataset swe-bench-test-lite \
    --experiment-name test_experiment \
    --merge-report && cp -r /swe_util/eval_data/eval_logs/test_experiment/* /swe_bench_output/eval_logs \
    && cp -r /swe_util/eval_data/outputs/* /swe_bench_output/swe_bench_format/"
