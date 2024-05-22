#!/bin/bash

export PYTHONPATH=$(pwd)
# poetry shell

python ./evaluation/mint/run_infer.py \
    --subset math \
    --max-iterations 5 \
    --max_propose_solution 2 \
    --eval-n-limit 1
