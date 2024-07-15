# Requirements
from .agent_skills import AgentSkillsPlugin, AgentSkillsRequirement
from .jupyter import JupyterPlugin, JupyterRequirement
from .mixin import PluginMixin
from .requirement import Plugin, PluginRequirement
from .swe_agent_commands import SWEAgentCommandsRequirement

__all__ = [
    'Plugin',
    'PluginMixin',
    'PluginRequirement',
    'AgentSkillsRequirement',
    'AgentSkillsPlugin',
    'JupyterRequirement',
    'JupyterPlugin',
    'SWEAgentCommandsRequirement',
]

ALL_PLUGINS = {
    'jupyter': JupyterPlugin,
    'agent_skills': AgentSkillsPlugin,
}
