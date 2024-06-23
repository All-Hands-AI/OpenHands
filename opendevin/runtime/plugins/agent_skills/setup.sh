#!/bin/bash

set -e

# add agent_skills to PATH
echo 'export PATH=/opendevin/plugins/agent_skills:$PATH' >> ~/.bashrc
export PATH=/opendevin/plugins/agent_skills:$PATH

# add agent_skills to PYTHONPATH
echo 'export PYTHONPATH=/opendevin/plugins/agent_skills:$PYTHONPATH' >> ~/.bashrc
export PYTHONPATH=/opendevin/plugins/agent_skills:$PYTHONPATH

pip install flake8 python-docx PyPDF2 python-pptx pylatexenc openai opencv-python litellm diskcache==5.6.3 grep-ast==0.3.2 tree-sitter==0.21.3 tree-sitter-languages==1.10.2 gitpython networkx scipy
