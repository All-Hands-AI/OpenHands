#!/bin/bash

env_name=$1

if [ -z "$1" ]; then
  echo "Usage: convert-to-conda-env.sh <env_name>"
  exit 1
fi

conda create -y --name ${env_name} python=3.12 cudatoolkit pandas numba
conda env export --name ${env_name} -f /tmp/environment.yaml
conda activate ${env_name}
pip install -r requirements.txt
conda env update --prune --name ${env_name} --file /tmp/environment.yaml
echo "Activate new environment with 'conda activate ${env_name}'"