#!/bin/bash

mkdir evaluation/swe_bench/eval_workspace
pushd evaluation/swe_bench/eval_workspace
git clone -b xw/od-fix https://github.com/OpenDevin/SWE-bench-docker.git
cd SWE-bench-docker
scripts/pull_docker_images.sh docker/ xingyaoww
