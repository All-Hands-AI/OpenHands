#!/bin/bash

set -e

# add agent_skills to PATH
echo 'export PATH=/opendevin/plugins/agent_skills:$PATH' >> ~/.bashrc
export PATH=/opendevin/plugins/agent_skills:$PATH

# add agent_skills to PYTHONPATH
echo 'export PYTHONPATH=/opendevin/plugins/agent_skills:$PYTHONPATH' >> ~/.bashrc
export PYTHONPATH=/opendevin/plugins/agent_skills:$PYTHONPATH
