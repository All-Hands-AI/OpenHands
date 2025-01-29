import warnings
from dataclasses import dataclass

from openhands.runtime.plugins.agent_skills import agentskills
from openhands.runtime.plugins.requirement import Plugin, PluginRequirement

warnings.warn(
    "The agent_skills module is deprecated and will be removed in version 0.22.0. "
    "Please migrate to the function calling interface. "
    "See https://docs.all-hands.dev/usage/migration/agent-skills-to-function-calls for details.",
    DeprecationWarning,
    stacklevel=2
)


@dataclass
class AgentSkillsRequirement(PluginRequirement):
    name: str = 'agent_skills'
    documentation: str = agentskills.DOCUMENTATION


class AgentSkillsPlugin(Plugin):
    name: str = 'agent_skills'
