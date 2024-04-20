import os
from opendevin.sandbox.plugins.requirement import PluginRequirement


class JupyterRequirement(PluginRequirement):
    def __init__(self):
        super().__init__(
            'jupyter',
            os.path.join('jupyter', 'setup.sh')
        )
