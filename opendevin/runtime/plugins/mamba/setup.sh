#!/bin/bash

set -e

apt install -y sudo -o Dpkg::Options::="--force-confnew"

if [ ! -d "/opendevin/miniforge3" ]; then
#    wget "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"
    mkdir -p /opendevin
    bash /workspace/Miniforge3-$(uname)-$(uname -m).sh -b -p /opendevin/miniforge3
    export PATH=/opendevin/miniforge3/bin:$PATH
    /opendevin/miniforge3/bin/mamba init bash

    /bin/bash -c "/opendevin/miniforge3/bin/mamba create -n od python==3.11.5 -y"
    /bin/bash -c ". /opendevin/miniforge3/etc/profile.d/conda.sh && conda config --set changeps1 False && conda config --append channels conda-forge"
    echo ". /opendevin/miniforge3/etc/profile.d/conda.sh && conda activate od" >> ~/.bashrc
fi
source ~/.bashrc
bash -c ". /opendevin/miniforge3/etc/profile.d/conda.sh && conda activate od"
