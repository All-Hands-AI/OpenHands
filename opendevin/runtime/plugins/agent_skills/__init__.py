import os
from dataclasses import dataclass

from opendevin.runtime.plugins.agent_skills.agentskills import DOCUMENTATION
from opendevin.runtime.plugins.requirement import PluginRequirement


@dataclass
class AgentSkillsRequirement(PluginRequirement):
    name: str = 'agent_skills'
    host_src: str = os.path.dirname(
        os.path.abspath(__file__)
    )  # The directory of this file (opendevin/runtime/plugins/jupyter)
    sandbox_dest: str = '/opendevin/plugins/agent_skills'
    bash_script_path: str = 'setup.sh'
    documentation: str = DOCUMENTATION
