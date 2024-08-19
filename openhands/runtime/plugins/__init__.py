# Requirements
from .agent_skills import AgentSkillsPlugin, AgentSkillsRequirement
from .jupyter import JupyterPlugin, JupyterRequirement
from .requirement import Plugin, PluginRequirement

__all__ = [
    'Plugin',
    'PluginRequirement',
    'AgentSkillsRequirement',
    'AgentSkillsPlugin',
    'JupyterRequirement',
    'JupyterPlugin',
]

ALL_PLUGINS = {
    'jupyter': JupyterPlugin,
    'agent_skills': AgentSkillsPlugin,
}
