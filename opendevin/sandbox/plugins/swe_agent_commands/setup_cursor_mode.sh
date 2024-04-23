#!/bin/bash

# Cursor Mode from SWE-Bench
# https://github.com/princeton-nlp/SWE-agent/blob/ca54d5556b9db4f4f2be21f09530ce69a72c0305/config/configs/default_sys-env_cursors_window100-detailed_cmd_format-last_5_history-1_demos.yaml#L108-L111
echo 'source /opendevin/plugins/swe_agent_commands/_setup_cursor_mode_env.sh' >> ~/.bashrc

echo 'source /opendevin/plugins/swe_agent_commands/cursors_defaults.sh' >> ~/.bashrc
echo 'source /opendevin/plugins/swe_agent_commands/cursors_edit_linting.sh' >> ~/.bashrc
echo 'source /opendevin/plugins/swe_agent_commands/search.sh' >> ~/.bashrc
