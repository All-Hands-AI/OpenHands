#!/bin/bash

# Default Mode from SWE-Bench
# https://github.com/princeton-nlp/SWE-agent/blob/ca54d5556b9db4f4f2be21f09530ce69a72c0305/config/configs/default_sys-env_window100-detailed_cmd_format-last_5_history-1_demos.yaml#L103-L106
echo 'source /opendevin/plugins/swe_agent_commands/_setup_default_env.sh' >> ~/.bashrc

echo 'source /opendevin/plugins/swe_agent_commands/defaults.sh' >> ~/.bashrc
echo 'source /opendevin/plugins/swe_agent_commands/search.sh' >> ~/.bashrc
echo 'source /opendevin/plugins/swe_agent_commands/edit_linting.sh' >> ~/.bashrc
