"""
Subprocess-based bash session implementation that inherits from BashSession
but replaces the tmux implementation with individual subprocess calls.
This is similar to the Anthropic approach but simpler.
"""

import os
import subprocess
import time

from openhands.core.logger import openhands_logger as logger
from openhands.events.action import CmdRunAction
from openhands.events.observation import ErrorObservation
from openhands.events.observation.commands import CmdOutputObservation
from openhands.runtime.utils.base_bash import BashSession
from openhands.runtime.utils.bash_constants import TIMEOUT_MESSAGE_TEMPLATE
from openhands.runtime.utils.tmux_bash import BashCommandStatus


class SubprocessBashSession(BashSession):
    """
    A bash session implementation using individual subprocess calls
    instead of tmux, while maintaining the same interface as BashSession.
    """

    def __init__(
        self,
        work_dir: str,
        username: str | None = None,
        no_change_timeout_seconds: int = 30,
        max_memory_mb: int | None = None,
    ):
        # Initialize parent class attributes
        super().__init__(work_dir, username, no_change_timeout_seconds, max_memory_mb)

    def initialize(self) -> None:
        """Initialize the bash session."""
        logger.debug(
            f'Initializing subprocess bash session with work dir: {self.work_dir}'
        )

        # Set initial state
        self.prev_status: BashCommandStatus | None = None
        self.prev_output: str = ''
        self._closed: bool = False
        self._cwd = os.path.abspath(self.work_dir)
        self._initialized = True
        self._current_process: subprocess.Popen | None = None

        logger.debug(
            f'Subprocess bash session initialized with work dir: {self.work_dir}'
        )

    def close(self) -> None:
        """Clean up the session."""
        if self._current_process and self._current_process.poll() is None:
            self._current_process.terminate()
            try:
                self._current_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._current_process.kill()
        self._closed = True

    def interrupt(self) -> None:
        """Interrupt the currently running command (Ctrl+C equivalent)."""
        if self._current_process and self._current_process.poll() is None:
            logger.debug('Interrupting current command')
            self._current_process.terminate()
            self.prev_status = BashCommandStatus.INTERRUPTED

    def get_status(self) -> BashCommandStatus | None:
        """Get the status of the last command."""
        return self.prev_status

    def is_running(self) -> bool:
        """Check if a command is currently running."""
        return (
            self._current_process is not None and self._current_process.poll() is None
        )

    def execute(self, action: CmdRunAction) -> CmdOutputObservation | ErrorObservation:
        """Execute a command in the bash session using subprocess."""
        from openhands.events.observation.commands import CmdOutputMetadata

        if not self._initialized:
            raise RuntimeError('Bash session is not initialized')

        logger.debug(f'RECEIVED ACTION: {action}')
        command = action.command.strip()
        is_input: bool = action.is_input

        # Handle input commands - not supported in this simple implementation
        if is_input:
            return ErrorObservation(
                content=f"Subprocess bash session does not support interactive input. The command '{command}' was not sent to any process."
            )

        # Handle empty commands
        if command == '':
            return CmdOutputObservation(
                content='ERROR: No command provided.',
                command='',
                metadata=CmdOutputMetadata(),
            )

        # Check for multiple commands (reuse original logic)
        from openhands.runtime.utils.bash import split_bash_commands

        splited_commands = split_bash_commands(command)
        if len(splited_commands) > 1:
            return ErrorObservation(
                content=(
                    f'ERROR: Cannot execute multiple commands at once.\n'
                    f'Please run each command separately OR chain them into a single command via && or ;\n'
                    f'Provided commands:\n{"\n".join(f"({i + 1}) {cmd}" for i, cmd in enumerate(splited_commands))}'
                )
            )

        start_time = time.time()

        try:
            # Prepare the command
            from openhands.runtime.utils.bash import escape_bash_special_chars

            escaped_command = escape_bash_special_chars(command)
            logger.debug(f'EXECUTING COMMAND: {escaped_command!r}')

            # Set effective timeout
            effective_timeout = action.timeout if action.timeout else 30.0

            # Execute the command using subprocess
            self._current_process = subprocess.Popen(
                ['bash', '-c', escaped_command],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=self._cwd,
            )

            try:
                stdout, stderr = self._current_process.communicate(
                    timeout=effective_timeout
                )
                exit_code = self._current_process.returncode

                # Check if process was interrupted (negative exit codes indicate signals)
                if exit_code < 0:
                    self.prev_status = BashCommandStatus.INTERRUPTED
                else:
                    self.prev_status = BashCommandStatus.COMPLETED

                # Combine output and error
                combined_output = stdout
                if stderr:
                    combined_output += f'\n{stderr}'

                # Update working directory if it's a cd command
                if command.strip().startswith('cd '):
                    try:
                        # Try to get the new working directory
                        pwd_process = subprocess.run(
                            ['bash', '-c', f'{escaped_command}; pwd'],
                            capture_output=True,
                            text=True,
                            cwd=self._cwd,
                            timeout=5.0,
                        )
                        if pwd_process.returncode == 0:
                            new_cwd = pwd_process.stdout.strip().split('\n')[-1]
                            if os.path.isdir(new_cwd):
                                self._cwd = new_cwd
                    except Exception:
                        pass  # Ignore errors in pwd detection

                # Create metadata
                metadata = CmdOutputMetadata()
                metadata.exit_code = exit_code
                metadata.working_dir = self._cwd

                self.prev_output = ''

                return CmdOutputObservation(
                    content=combined_output.rstrip() if combined_output else '',
                    command=command,
                    metadata=metadata,
                )

            except subprocess.TimeoutExpired:
                # Handle timeout
                self._current_process.kill()
                elapsed_time = time.time() - start_time

                # Try to get partial output
                try:
                    stdout, stderr = self._current_process.communicate(timeout=1.0)
                    partial_output = stdout
                    if stderr:
                        partial_output += f'\n{stderr}'
                except subprocess.TimeoutExpired:
                    partial_output = ''

                metadata = CmdOutputMetadata()
                metadata.suffix = (
                    f'\n[The command timed out after {elapsed_time:.1f} seconds. '
                    f'{TIMEOUT_MESSAGE_TEMPLATE}]'
                )

                self.prev_status = BashCommandStatus.HARD_TIMEOUT

                return CmdOutputObservation(
                    content=partial_output.rstrip() if partial_output else '',
                    command=command,
                    metadata=metadata,
                )

            finally:
                # Clear current process reference
                self._current_process = None

        except Exception as e:
            logger.error(f'Error executing command "{command}": {e}')
            return ErrorObservation(
                content=f'Error executing command "{command}": {str(e)}'
            )

    def _ready_for_next_command(self) -> None:
        """Reset state for next command."""
        pass

    def _get_pane_content(self) -> str:
        """Get current output."""
        return ''

    @property
    def cwd(self) -> str:
        """Get current working directory."""
        return self._cwd
