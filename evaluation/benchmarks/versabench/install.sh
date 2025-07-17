#!/bin/bash
set -e
echo 'Installing Versabench_cache'

# Create target directory if it doesn't exist
mkdir -p ./evaluation/benchmarks/versabench/versabench_cache

## Multi-SWE-bench

# Clone the dataset repo if it hasn't been cloned yet
if [ ! -d ./evaluation/benchmarks/versabench/versabench_cache/Multi-SWE-bench ]; then
  git clone https://huggingface.co/datasets/ByteDance-Seed/Multi-SWE-bench \
    ./evaluation/benchmarks/versabench/versabench_cache/Multi-SWE-bench

# Create the 'all' subdirectory
mkdir -p ./evaluation/benchmarks/versabench/versabench_cache/Multi-SWE-bench/java/all

# Concatenate all .jsonl files in java/ into all.jsonl
cat ./evaluation/benchmarks/versabench/versabench_cache/Multi-SWE-bench/java/*.jsonl \
  > ./evaluation/benchmarks/versabench/versabench_cache/Multi-SWE-bench/java/all/all.jsonl

# Run the Python script with poetry
poetry run python ./evaluation/benchmarks/multi_swe_bench/scripts/data/data_change.py \
  --input ./evaluation/benchmarks/versabench/versabench_cache/Multi-SWE-bench/java/all/all.jsonl \
  --output ./evaluation/benchmarks/versabench/versabench_cache/Multi-SWE-bench/java/all/all_updated_clean.jsonl

fi

#SWT bench
if [ ! -d ./evaluation/benchmarks/versabench/versabench_cache/swt-bench ]; then
    git clone   https://github.com/logic-star-ai/swt-bench ./evaluation/benchmarks/versabench/versabench_cache/swt-bench
    #Subshell () ensures environment changes (like source) don’t leak out. and pushd/popd ensures directory is restored.
    (
        pushd ./evaluation/benchmarks/versabench/versabench_cache/swt-bench
        python -m venv .venv
        source .venv/bin/activate
        pip install -e .
        deactivate
        popd
    )
fi
echo 'Finished installing Versabench_cache'
