#!/bin/bash

export PIP_CACHE_DIR=$HOME/.cache/pip
pip install flake8

# Default Mode from SWE-Bench
# https://github.com/princeton-nlp/SWE-agent/blob/ca54d5556b9db4f4f2be21f09530ce69a72c0305/config/configs/default_sys-env_window100-detailed_cmd_format-last_5_history-1_demos.yaml#L103-L106
echo 'source /opendevin/plugins/swe_agent_commands/_setup_default_env.sh' >> ~/.bashrc

# make _split_string (py) available
echo 'export PATH=$PATH:/opendevin/plugins/swe_agent_commands' >> ~/.bashrc

echo 'source /opendevin/plugins/swe_agent_commands/defaults.sh' >> ~/.bashrc
echo 'source /opendevin/plugins/swe_agent_commands/search.sh' >> ~/.bashrc
echo 'source /opendevin/plugins/swe_agent_commands/edit_linting.sh' >> ~/.bashrc

echo 'export SWE_CMD_WORK_DIR="/opendevin/plugins/swe_agent_commands/workdir"' >> ~/.bashrc
sudo mkdir -p /opendevin/plugins/swe_agent_commands/workdir
sudo chmod 777 /opendevin/plugins/swe_agent_commands/workdir
