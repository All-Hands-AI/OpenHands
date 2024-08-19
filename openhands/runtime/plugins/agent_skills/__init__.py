from dataclasses import dataclass

from openhands.runtime.plugins.requirement import Plugin, PluginRequirement

from . import agentskills


@dataclass
class AgentSkillsRequirement(PluginRequirement):
    name: str = 'agent_skills'
    documentation: str = agentskills.DOCUMENTATION


class AgentSkillsPlugin(Plugin):
    name: str = 'agent_skills'
