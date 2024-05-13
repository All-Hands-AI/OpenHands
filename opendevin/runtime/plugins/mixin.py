import os
from typing import Protocol

from opendevin.core.logger import opendevin_logger as logger
from opendevin.runtime.plugins.requirement import PluginRequirement


class SandboxProtocol(Protocol):
    # https://stackoverflow.com/questions/51930339/how-do-i-correctly-add-type-hints-to-mixin-classes

    def execute(self, cmd: str) -> tuple[int, str]: ...

    def copy_to(self, host_src: str, sandbox_dest: str, recursive: bool = False): ...


class PluginMixin:
    """Mixin for Sandbox to support plugins."""

    def init_plugins(self: SandboxProtocol, requirements: list[PluginRequirement]):
        """Load a plugin into the sandbox."""

        # clean-up ~/.bashrc and touch ~/.bashrc
        exit_code, output = self.execute('rm -f ~/.bashrc && touch ~/.bashrc')

        for requirement in requirements:
            # copy over the files
            self.copy_to(requirement.host_src, requirement.sandbox_dest, recursive=True)
            logger.info(
                f'Copied files from [{requirement.host_src}] to [{requirement.sandbox_dest}] inside sandbox.'
            )

            # Execute the bash script
            abs_path_to_bash_script = os.path.join(
                requirement.sandbox_dest, requirement.bash_script_path
            )
            logger.info(
                f'Initializing plugin [{requirement.name}] by executing [{abs_path_to_bash_script}] in the sandbox.'
            )
            exit_code, output = self.execute(abs_path_to_bash_script)
            if exit_code != 0:
                raise RuntimeError(
                    f'Failed to initialize plugin {requirement.name} with exit code {exit_code} and output {output}'
                )
            logger.info(f'Plugin {requirement.name} initialized successfully.')

        if len(requirements) > 0:
            exit_code, output = self.execute('source ~/.bashrc')
            if exit_code != 0:
                raise RuntimeError(
                    f'Failed to source ~/.bashrc with exit code {exit_code} and output {output}'
                )
            logger.info('Sourced ~/.bashrc successfully')
