from dataclasses import dataclass

from opendevin.runtime.plugins.agent_skills.agentskills import DOCUMENTATION
from opendevin.runtime.plugins.requirement import Plugin, PluginRequirement


@dataclass
class AgentSkillsRequirement(PluginRequirement):
    name: str = 'agent_skills'
    documentation: str = DOCUMENTATION


class AgentSkillsPlugin(Plugin):
    name: str = 'agent_skills'
