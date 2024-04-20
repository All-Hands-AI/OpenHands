import os
from typing import List, Protocol, Tuple
from opendevin.logger import opendevin_logger as logger
from opendevin.sandbox.plugins.requirement import PluginRequirement


class HasExecuteProtocol(Protocol):
    # https://stackoverflow.com/questions/51930339/ how-do-i-correctly-add-type-hints-to-mixin-classes

    def execute(self, cmd: str) -> Tuple[int, str]:
        ...


class PluginMixin:
    """Mixin for Sandbox to support plugins."""

    def init_plugins(self: HasExecuteProtocol,
                     requirements: List[PluginRequirement],
                     plugin_dir: str = '/opendevin/plugins'
                     ):
        """Load a plugin into the sandbox."""
        for requirement in requirements:
            # Execute the bash script
            abs_path_to_bash_script = os.path.join(plugin_dir, requirement.bash_script_path)
            logger.info(f'Initalizing plugin {requirement.name} by executing [{abs_path_to_bash_script}] in the sandbox.')
            exit_code, output = self.execute(abs_path_to_bash_script)
            if exit_code != 0:
                raise RuntimeError(f'Failed to initialize plugin {requirement.name} with exit code {exit_code} and output {output}')
            logger.info(f'Plugin {requirement.name} initialized successfully\n:{output}')

        exit_code, output = self.execute('source ~/.bashrc')
        if exit_code != 0:
            raise RuntimeError(f'Failed to source ~/.bashrc with exit code {exit_code} and output {output}')
        logger.info('Sourced ~/.bashrc successfully')
