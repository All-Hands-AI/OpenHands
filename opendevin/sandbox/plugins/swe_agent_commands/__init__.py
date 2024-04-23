import os
from dataclasses import dataclass
from opendevin.sandbox.plugins.requirement import PluginRequirement


@dataclass
class SWEAgentCommandsRequirement(PluginRequirement):
    name: str = 'swe_agent_commands'
    host_src: str = os.path.dirname(os.path.abspath(__file__))
    sandbox_dest: str = '/opendevin/plugins/swe_agent_commands'
    bash_script_path: str = 'setup.sh'
