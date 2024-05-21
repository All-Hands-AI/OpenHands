#!/bin/bash

python ./evaluation/mint/infer.py \
    --subset math \
    --max-iterations 5 \
    --eval-n-limit 1
