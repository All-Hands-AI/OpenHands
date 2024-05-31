#!/bin/bash

set -e

# add agent_skills to PATH
echo 'export PATH=/opendevin/plugins/agent_skills:$PATH' >> ~/.bashrc
export PATH=/opendevin/plugins/agent_skills:$PATH

# add agent_skills to PYTHONPATH
echo 'export PYTHONPATH=/opendevin/plugins/agent_skills:$PYTHONPATH' >> ~/.bashrc
export PYTHONPATH=/opendevin/plugins/agent_skills:$PYTHONPATH

pip install flake8 python-docx PyPDF2 python-pptx pylatexenc openai opencv-python
