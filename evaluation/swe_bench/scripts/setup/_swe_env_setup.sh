#!/bin/bash
# THIS SCRIPT ONLY NEED TO BE RUN ONCE BEFORE EVALUATION
set -e

function setup_environment_and_testbed {
    local instance_file_name=$1

    # throw error if user name is not opendevin
    if [ "$USER" != "opendevin" ]; then
        echo "Error: This script is intended to be run by the 'opendevin' user only." >&2
        exit 1
    fi

    # =======================================================
    # Install & Setup Conda

    # assume /swe_util/miniforge3 already exists
    # install if swe-util does NOT have conda
    if [ ! -d /swe_util/miniforge3 ]; then
        pushd /swe_util
        echo "Downloading and installing Miniforge3"
        wget "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"
        bash Miniforge3-$(uname)-$(uname -m).sh -b -p /swe_util/miniforge3
    fi

    echo 'export PATH=/swe_util/miniforge3/bin:$PATH' >> ~/.bashrc
    eval "$(/swe_util/miniforge3/bin/conda shell.bash hook)"
    conda init bash
    source ~/.bashrc
    conda config --set changeps1 False
    conda config --append channels conda-forge

    # =======================================================
    # Install swe-bench-eval environment if it does not exist
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
    # Read the swe-bench-test-lite.json / swe-bench-test.json file and extract the required item based on instance_id
    INSTANCE_DATA_FILE=/swe_util/eval_data/instances/$instance_file_name
    echo "Instance data file loaded: $INSTANCE_DATA_FILE"

    # =======================================================
    # generate testbed & conda environment for ALL instances in the test file
    echo "Generating testbed & conda environment for all instances in the test file"
    export PYTHONPATH=/swe_util/OD-SWE-bench:$PYTHONPATH
    python3 /swe_util/OD-SWE-bench/swebench/harness/engine_testbed.py \
        --instances_path $INSTANCE_DATA_FILE \
        --log_dir /swe_util/eval_data/testbed_logs \
        --conda_path /swe_util/miniforge3 \
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
}

# check if $1 is either swe-bench-test-lite.json or swe-bench-test.json
if [ "$1" != "swe-bench-test-lite.json" ] && [ "$1" != "swe-bench-test.json" ]; then
    echo "Error: Invalid input file name. Please provide either swe-bench-test-lite.json or swe-bench-test.json"
    exit 1
fi

# call the function
echo "Calling setup_environment_and_testbed with $1"
setup_environment_and_testbed $1
