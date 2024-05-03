#!/bin/bash
# THIS SCRIPT ONLY NEED TO BE RUN ONCE BEFORE EVALUATION
set -e
# throw error if user name is not opendevin
if [ "$USER" != "opendevin" ]; then
    echo "Error: This script is intended to be run by the 'opendevin' user only." >&2
    exit 1
fi

# =======================================================
# Install & Setup Conda

# install if swe-util does NOT have conda
if [ ! -d /swe_util/miniconda3 ]; then
    pushd /swe_util
    echo "Downloading and installing Miniconda3"
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O Miniconda3-latest-Linux-x86_64.sh
    bash Miniconda3-latest-Linux-x86_64.sh -b -p /swe_util/miniconda3
fi
echo 'export PATH=/swe_util/miniconda3/bin:$PATH' >> ~/.bashrc
eval "$(/swe_util/miniconda3/bin/conda shell.bash hook)"
conda init bash
source ~/.bashrc
conda config --set changeps1 False
conda config --append channels conda-forge

# =======================================================
# Install swe-bench-eval environment if it does not exist
# ENV_EXISTS=$(conda info --envs)
ENV_EXISTS=$(conda info --envs | awk '/swe-bench-eval/ {print $1}')
echo "ENV_EXISTS: $ENV_EXISTS"
if [ -z "$ENV_EXISTS" ]; then
    echo "Environment swe-bench-eval does not exist. Creating the environment."
    conda create -n swe-bench-eval python==3.11.5 -y
    conda activate swe-bench-eval
    pip install requests python-dotenv GitPython datasets pandas beautifulsoup4 ghapi
fi
conda activate swe-bench-eval
echo 'swe-bench-eval environment is ready.'

# =======================================================
# Read the swe-bench-test-lite.json file and extract the required item based on instance_id
INSTANCE_DATA_FILE=/swe_util/eval_data/instances/swe-bench-test-lite.json
echo "Instace data file loaded: $INSTANCE_DATA_FILE"

# =======================================================
# generate testbed & conda environment for ALL instances in the test file
echo "Generating testbed & conda environment for all instances in the test file"
python3 /swe_util/OD-SWE-bench/swebench/harness/engine_testbed.py \
    --instances_path $INSTANCE_DATA_FILE \
    --log_dir /swe_util/eval_data/testbed_logs \
    --conda_path /swe_util/miniconda3 \
    --testbed /swe_util/eval_data/testbeds \
    --timeout 1000

# Check every log in /swe_util/eval_data/testbed_logs to see if they contains "Init Succeeded"
# If not, print the log file name and exit
for log_file in /swe_util/eval_data/testbed_logs/*; do
    if ! grep -q "Init Succeeded" $log_file; then
        echo "Error: $log_file does not contain 'Init Succeeded'"
        exit 1
    fi
done
echo "All logs contain 'Init Succeeded'. Testbed & conda environment setup is successful."
