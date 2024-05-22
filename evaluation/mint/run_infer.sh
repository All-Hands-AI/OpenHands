#!/bin/bash

export PYTHONPATH=$(pwd)
# poetry shell

python ./evaluation/mint/run_infer.py \
    --subset math \
    --max-iterations 5 \
    --eval-n-limit 1
