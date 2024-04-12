#!/bin/bash
echo "Container hostname: $(hostname)"
echo "Container IP: $(hostname -i)"
echo "Environment variables:"
env | grep NVIDIA
echo "Python environment and executables status:"
echo "Default '$(which python3)'" python3 --version
echo "PIP executable '$(which pip)' pip --version"
echo "Python executable in ${VENV_NAME}: $(conda run -n ${VENV_NAME} python3 --version)"
echo "Python executable in ${VENV_NAME}: $(conda run -n ${VENV_NAME} pip --version)"
echo "Conda environments info:"
conda info --envs
echo "Nvidia CUDA properties:"
nvidia-smi
# echo "Force-loading the default Ollama model:"
