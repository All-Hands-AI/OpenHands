# Requirements
from openhands.runtime.plugins.agent_skills import (
    AgentSkillsPlugin,
    AgentSkillsRequirement,
)
from openhands.runtime.plugins.jupyter import JupyterPlugin, JupyterRequirement
from openhands.runtime.plugins.requirement import Plugin, PluginRequirement
from openhands.runtime.plugins.vscode import VSCodePlugin, VSCodeRequirement

__all__ = [
    'Plugin',
    'PluginRequirement',
    'AgentSkillsRequirement',
    'AgentSkillsPlugin',
    'JupyterRequirement',
    'JupyterPlugin',
    'VSCodeRequirement',
    'VSCodePlugin',
]

ALL_PLUGINS = {
    'jupyter': JupyterPlugin,
    'agent_skills': AgentSkillsPlugin,
    'vscode': VSCodePlugin,
}
