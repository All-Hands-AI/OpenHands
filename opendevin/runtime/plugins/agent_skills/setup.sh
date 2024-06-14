#!/bin/bash

set -e

OPENDEVIN_PYTHON_INTERPRETER=/opendevin/miniforge3/bin/python
# check if OPENDEVIN_PYTHON_INTERPRETER exists and it is usable
if [ -z "$OPENDEVIN_PYTHON_INTERPRETER" ] ||  [ ! -x "$OPENDEVIN_PYTHON_INTERPRETER" ]; then
    echo "OPENDEVIN_PYTHON_INTERPRETER is not usable. Please pull the latest Docker image!"
    exit 1
fi

# add agent_skills to PATH
echo 'export PATH=/opendevin/plugins/agent_skills:$PATH' >> ~/.bashrc

# add agent_skills to PYTHONPATH
echo 'export PYTHONPATH=/opendevin/plugins/agent_skills:$PYTHONPATH' >> ~/.bashrc

source ~/.bashrc

$OPENDEVIN_PYTHON_INTERPRETER -m pip install flake8 python-docx PyPDF2 python-pptx pylatexenc openai opencv-python
