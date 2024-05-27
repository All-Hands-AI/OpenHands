import os
from dataclasses import dataclass

from opendevin.runtime.plugins.requirement import PluginRequirement


@dataclass
class MambaRequirement(PluginRequirement):
    name: str = 'mamba'
    host_src: str = os.path.dirname(
        os.path.abspath(__file__)
    )
    sandbox_dest: str = '/opendevin/plugins/mamba'
    bash_script_path: str = 'setup.sh'
    documentation: str = ''
