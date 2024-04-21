import os
from dataclasses import dataclass
from opendevin.sandbox.plugins.requirement import PluginRequirement


@dataclass
class JupyterRequirement(PluginRequirement):
    name: str = 'jupyter'
    bash_script_path: str = os.path.join('jupyter', 'setup.sh')
