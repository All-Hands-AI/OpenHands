from dataclasses import dataclass

from openhands.runtime.plugins.agent_skills.agentskills import DOCUMENTATION
from openhands.runtime.plugins.requirement import Plugin, PluginRequirement


@dataclass
class AgentSkillsRequirement(PluginRequirement):
    name: str = 'agent_skills'
    documentation: str = DOCUMENTATION


class AgentSkillsPlugin(Plugin):
    name: str = 'agent_skills'
