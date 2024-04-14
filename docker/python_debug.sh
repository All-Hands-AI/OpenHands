#!/bin/bash

echo "Miniconda environment info:"
echo "Python executable in ${VENV_NAME}: $(conda run -n ${VENV_NAME} python3 --version)"
echo "Python executable in ${VENV_NAME}: $(conda run -n ${VENV_NAME} pip --version)"
echo "Conda environments info:"
conda info --envs

echo "Python3 info:"
echo "Default python3 executable: '$(which python3)'" --version
echo "PIP executable '$(which pip)' pip --version"

echo "Python environment variables:"
env | grep PYTHON