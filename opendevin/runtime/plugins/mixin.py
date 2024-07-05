import os
import signal
import time
from typing import Callable, Protocol, Union

from pexpect.exceptions import EOF, TIMEOUT

from opendevin.core.logger import opendevin_logger as logger
from opendevin.core.schema import CancellableStream
from opendevin.runtime.plugins.requirement import PluginRequirement


class SandboxProtocol(Protocol):
    # https://stackoverflow.com/questions/51930339/how-do-i-correctly-add-type-hints-to-mixin-classes
    @property
    def plugin_initialized(self) -> bool:
        # This is a protocol method that should be implemented by classes adhering to this protocol
        pass

    @property
    def initialize_plugins(self) -> bool: ...

    def execute(
        self, cmd: str, stream: bool = False
    ) -> tuple[int, str | CancellableStream]: ...

    def copy_to(self, host_src: str, sandbox_dest: str, recursive: bool = False): ...


def _source_bashrc(sandbox: SandboxProtocol):
    exit_code1, output1 = sandbox.execute('source /opendevin/bash.bashrc')
    if exit_code1 != 0:
        raise RuntimeError(
            f'Failed to source /opendevin/bash.bashrc with exit code {exit_code1} and output: {output1}'
        )
    exit_code2, output2 = sandbox.execute('source ~/.bashrc')
    if exit_code2 != 0:
        raise RuntimeError(
            f'Failed to source ~/.bashrc with exit code {exit_code2} and output: {output2}'
        )
    logger.info('Sourced /opendevin/bash.bashrc and ~/.bashrc successfully')


def _handle_stream_output(output: CancellableStream, plugin_name: str):
    total_output = ''
    exit_code_value = None
    start_time = time.time()
    minor_timeout = 10
    timeout = 30
    last_output_time = start_time

    try:
        for line in output:
            line = line.rstrip()
            logger.info(f'>>> {line}')
            total_output += line + '\n'
            last_output_time = time.time()

            if line.endswith('[PEXPECT]$') or '[PEXPECT]$' in line:
                logger.debug('Detected [PEXPECT]$ prompt, ending stream.')
                break

            if time.time() - start_time > timeout:
                logger.warning(f'Execution timed out after {timeout} seconds.')
                break

            if time.time() - last_output_time > minor_timeout:
                logger.warning(f'No output for {minor_timeout} seconds, ending stream.')
                break

    except (EOF, TIMEOUT) as e:
        logger.warning(f'Stream interrupted: {e}')
    finally:
        try:
            exit_code_value = output.exit_code()
        except Exception as e:
            logger.error(f'Failed to get exit code: {e}')
            exit_code_value = -1
        output.close()

    if exit_code_value is not None and exit_code_value != 0:
        raise RuntimeError(
            f'Failed to initialize plugin {plugin_name} with exit code {exit_code_value} and output: {total_output.strip()}'
        )
    logger.info(f'Plugin {plugin_name} initialized successfully')


class PluginMixin:
    """Mixin for Sandbox to support plugins."""

    def __init__(self):
        self._execute_func: (
            Callable[[str, bool], tuple[int, Union[str, CancellableStream]]] | None
        ) = None

    @property
    def plugin_initialized(self) -> bool:
        return getattr(self, '_plugin_initialized', False)

    def set_execute_func(self, func: Callable):
        self._execute_func = func

    def execute(
        self, cmd: str, stream: bool = False
    ) -> tuple[int, Union[str, CancellableStream]]:
        if self._execute_func is None:
            raise NotImplementedError(
                'Execute function not set. Use set_execute_func to set it.'
            )

        # Implement a timeout mechanism
        def timeout_handler(signum, frame):
            raise TimeoutError('Command execution timed out')

        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(300)  # Set a 5-minute timeout

        try:
            result = self._execute_func(cmd, stream)
            signal.alarm(0)  # Cancel the alarm
            return result
        except TimeoutError:
            logger.error(f'Command execution timed out: {cmd}')
            raise
        finally:
            signal.alarm(0)  # Ensure the alarm is cancelled

    def init_plugins(self: SandboxProtocol, requirements: list[PluginRequirement]):
        """Load a plugin into the sandbox."""

        if self.plugin_initialized:
            logger.info('Plugins already initialized, skipping.')
            return

        if not self.initialize_plugins:
            logger.info('Skipping plugin initialization in the sandbox')
            setattr(self, '_plugin_initialized', True)
            return

        logger.info('Initializing plugins in the sandbox')

        # clean-up ~/.bashrc and touch ~/.bashrc
        exit_code, output = self.execute('rm -f ~/.bashrc && touch ~/.bashrc')
        if exit_code != 0:
            logger.warning(
                f'Failed to clean-up ~/.bashrc with exit code {exit_code} and output: {output}'
            )

        for index, requirement in enumerate(requirements, 1):
            logger.info(
                f'Initializing plugin {index}/{len(requirements)}: {requirement.name}'
            )

            try:
                # source bashrc file when plugin loads
                logger.info(f'Sourcing for {requirement.name}.')
                _source_bashrc(self)
                logger.info(f'Sourcing done for {requirement.name}.')

                # copy over the files
                self.copy_to(
                    requirement.host_src, requirement.sandbox_dest, recursive=True
                )
                logger.info(
                    f'Copied files from [{requirement.host_src}] to [{requirement.sandbox_dest}] inside sandbox.'
                )

                # Execute the bash script
                abs_path_to_bash_script = os.path.join(
                    requirement.sandbox_dest, requirement.bash_script_path
                )
                logger.info(f'Executing [{abs_path_to_bash_script}] in the sandbox.')

                exit_code, output = self.execute(abs_path_to_bash_script, stream=True)
                if isinstance(output, CancellableStream):
                    _handle_stream_output(output, requirement.name)
                else:
                    if exit_code != 0:
                        raise RuntimeError(
                            f'Failed to initialize plugin {requirement.name} with exit code {exit_code} and output: {output}'
                        )
                    logger.info(f'Plugin {requirement.name} initialized successfully.')

                logger.info(f'Finished initializing plugin: {requirement.name}')

            except Exception as e:
                logger.error(f'Error initializing plugin {requirement.name}: {str(e)}')
                raise
            finally:
                if isinstance(output, CancellableStream):
                    output.close()  # Ensure the stream is closed

        # Source bashrc one final time after all plugins are initialized
        _source_bashrc(self)
        logger.info('All plugins initialized successfully')
        setattr(self, '_plugin_initialized', True)
