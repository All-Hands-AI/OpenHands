#!/bin/bash

set -xeo pipefail
mkdir -p data/processed
python3 scripts/download_test_data.py

# Download an example output file (FROM claude-2)
# https://gist.github.com/sorendunn/9f1f1fade59f986b4925b6633f9ff165
mkdir -p data/predictions
wget https://huggingface.co/datasets/OpenDevin/Devin-SWE-bench-output/raw/main/devin_swe_outputs.json -O data/predictions/devin_swe_outputs.json
