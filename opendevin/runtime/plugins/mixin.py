import os
from typing import Protocol

from opendevin.core.logger import opendevin_logger as logger
from opendevin.core.schema import CancellableStream
from opendevin.runtime.plugins.requirement import PluginRequirement
from opendevin.runtime.utils.async_utils import async_to_sync


class SandboxProtocol(Protocol):
    # https://stackoverflow.com/questions/51930339/how-do-i-correctly-add-type-hints-to-mixin-classes

    @property
    def initialize_plugins(self) -> bool: ...

    def execute(
        self, cmd: str, stream: bool = False
    ) -> tuple[int, str | CancellableStream]: ...

    async def execute_async(
        self, cmd: str, stream: bool = False
    ) -> tuple[int, str | CancellableStream]: ...

    def copy_to(self, host_src: str, sandbox_dest: str, recursive: bool = False): ...

    async def copy_to_async(
        self, host_src: str, sandbox_dest: str, recursive: bool = False
    ): ...

    async def _source_bashrc_async(self) -> None: ...

    async def _init_plugins_async(self, plugins: list[PluginRequirement]) -> None: ...

    @property
    def plugin_initialized(self) -> bool: ...

    @plugin_initialized.setter
    def plugin_initialized(self, value: bool): ...


class PluginMixin:
    """Mixin for Sandbox to support plugins."""

    # @async_to_sync
    def source_bashrc(self: SandboxProtocol):
        return self._source_bashrc_async()

    async def _source_bashrc_async(self: SandboxProtocol):
        exit_code, output = await self.execute_async(
            'source /opendevin/bash.bashrc && source ~/.bashrc'
        )
        if exit_code != 0:
            raise RuntimeError(
                f'Failed to source /opendevin/bash.bashrc and ~/.bashrc with exit code {exit_code} and output: {output}'
            )
        logger.info('Sourced /opendevin/bash.bashrc and ~/.bashrc successfully')

    def init_plugins(self: SandboxProtocol, requirements: list[PluginRequirement]):
        return async_to_sync(self._init_plugins_async)(requirements)

    async def _init_plugins_async(
        self: SandboxProtocol, requirements: list[PluginRequirement]
    ):
        """Load plugins into the sandbox."""
        if hasattr(self, 'plugin_initialized') and self.plugin_initialized:
            return

        # Check if the sandbox is initialized
        if hasattr(self, 'initialized') and not self.initialized:
            logger.info('Sandbox not initialized. Initializing now...')
            if hasattr(self, 'initialize'):
                await self.initialize()
            else:
                logger.warning(
                    'Sandbox has no initialize method. Proceeding without initialization.'
                )

        if self.initialize_plugins:
            logger.info('Initializing plugins in the sandbox')

            # clean-up ~/.bashrc and touch ~/.bashrc
            exit_code, output = await self.execute_async(
                'rm -f ~/.bashrc && touch ~/.bashrc'
            )
            if exit_code != 0:
                logger.warning(
                    f'Failed to clean-up ~/.bashrc with exit code {exit_code} and output: {output}'
                )

            for requirement in requirements:
                # source bashrc file when plugin loads
                await self._source_bashrc_async()

                # copy over the files
                await self.copy_to_async(
                    requirement.host_src, requirement.sandbox_dest, recursive=True
                )
                logger.info(
                    f'Copied files from [{requirement.host_src}] to [{requirement.sandbox_dest}] inside sandbox.'
                )

                abs_path_to_bash_script = os.path.join(
                    requirement.sandbox_dest, requirement.bash_script_path
                )
                logger.info(
                    f'Initializing plugin [{requirement.name}] by executing [{abs_path_to_bash_script}] in the sandbox.'
                )
                exit_code, output = await self.execute_async(
                    abs_path_to_bash_script, stream=True
                )
                if isinstance(output, CancellableStream):
                    total_output = ''
                    for line in output:
                        line = line.rstrip()
                        logger.info(f'>>> {line}')
                        total_output += line + ' '
                    _exit_code = output.exit_code()
                    output.close()
                    if _exit_code != 0:
                        raise RuntimeError(
                            f'Failed to initialize plugin {requirement.name} with exit code {_exit_code} and output: {total_output.strip()}'
                        )
                    logger.info(f'Plugin {requirement.name} initialized successfully')
                else:
                    if exit_code != 0:
                        raise RuntimeError(
                            f'Failed to initialize plugin {requirement.name} with exit code {exit_code} and output: {output}'
                        )
                    logger.info(f'Plugin {requirement.name} initialized successfully.')
        else:
            logger.info('Skipping plugin initialization in the sandbox')

        if len(requirements) > 0:
            await self._source_bashrc_async()

        self.plugin_initialized = True
