#!/bin/bash

set -e

# add agent_skills to PATH
echo 'export PATH=/opendevin/plugins/agent_skills:$PATH' >> ~/.bashrc

# add agent_skills to PYTHONPATH
echo 'export PYTHONPATH=/opendevin/plugins/agent_skills:$PYTHONPATH' >> ~/.bashrc

source ~/.bashrc

pip install flake8 python-docx PyPDF2 python-pptx pylatexenc openai opencv-python
