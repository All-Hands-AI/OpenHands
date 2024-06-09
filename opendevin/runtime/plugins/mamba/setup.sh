#!/bin/bash

set -e

if [ ! -d "/opendevin/miniforge3" ]; then
    wget "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"
    mkdir -p /opendevin
    bash Miniforge3-$(uname)-$(uname -m).sh -b -p /opendevin/miniforge3
#    /opendevin/miniforge3/bin/mamba init bash
fi
bash -c ". /opendevin/miniforge3/etc/profile.d/conda.sh && conda config --set changeps1 False && conda config --append channels conda-forge"
echo "export PATH=/opendevin/miniforge3/bin:$PATH" >> ~/.bashrc
