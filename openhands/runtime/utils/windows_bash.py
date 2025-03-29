import os
import re
import time
import traceback
import uuid
from enum import Enum
from typing import Optional
import subprocess
import json
from pathlib import Path
import signal  # Add signal import for Windows signal handling
import tempfile

from openhands.core.logger import openhands_logger as logger
from openhands.events.action import CmdRunAction
from openhands.events.observation import ErrorObservation
from openhands.events.observation.commands import (
    CMD_OUTPUT_PS1_END,
    CmdOutputMetadata,
    CmdOutputObservation,
)
from openhands.utils.shutdown_listener import should_continue


def split_bash_commands(commands):
    if not commands.strip():
        return ['']
    try:
        # For Windows PowerShell, we'll split on semicolons and newlines
        # This is a simplified version since PowerShell has different command separators
        return [cmd.strip() for cmd in commands.split(';') if cmd.strip()]
    except Exception:
        logger.debug(
            f'Failed to parse PowerShell commands\n'
            f'[input]: {commands}\n'
            f'[warning]: {traceback.format_exc()}\n'
            f'The original command will be returned as is.'
        )
        return [commands]


def escape_powershell_special_chars(command: str) -> str:
    """Escapes characters that have special meaning in PowerShell."""
    if command.strip() == '':
        return ''

    # Escape special characters in PowerShell
    special_chars = ['`', '$', '"', "'", ';', '|', '&', '>', '<', '(', ')']
    for char in special_chars:
        command = command.replace(char, f'`{char}')
    return command


class BashCommandStatus(Enum):
    CONTINUE = 'continue'
    COMPLETED = 'completed'
    NO_CHANGE_TIMEOUT = 'no_change_timeout'
    HARD_TIMEOUT = 'hard_timeout'


def _remove_command_prefix(command_output: str, command: str) -> str:
    return command_output.lstrip().removeprefix(command.lstrip()).lstrip()


class WindowsBashSession:
    POLL_INTERVAL = 0.5
    HISTORY_LIMIT = 10_000
    PS1 = CmdOutputMetadata.to_ps1_prompt()

    def __init__(
        self,
        work_dir: str,
        username: str | None = None,
        no_change_timeout_seconds: int = 30,
        max_memory_mb: int | None = None,
    ):
        self.NO_CHANGE_TIMEOUT_SECONDS = no_change_timeout_seconds
        self.work_dir = work_dir
        self.username = username
        self._initialized = False
        self.max_memory_mb = max_memory_mb
        self._process: Optional[subprocess.Popen] = None
        self._output_buffer = []
        self._last_output = ""
        self._cwd = os.path.abspath(work_dir)

    def initialize(self):
        """Initialize the PowerShell session."""
        # Create a temporary script file for PowerShell initialization
        self._temp_dir = Path(tempfile.mkdtemp())
        self._init_script = self._temp_dir / "init.ps1"
        self._command_script = self._temp_dir / "command.ps1"
        
        # Write initialization script with more robust setup
        init_script_content = f'''
Set-Location "{self.work_dir}"
$OutputEncoding = [System.Text.Encoding]::UTF8
$PSDefaultParameterValues["*:Encoding"] = "utf8"
$MaximumHistoryCount = {self.HISTORY_LIMIT}
$env:PROMPT = "{self.PS1}"

# Function to handle commands
function Process-Command {{
    param($command)
    try {{
        Invoke-Expression $command
    }} catch {{
        Write-Error $_.Exception.Message
        exit 1
    }}
}}

# Main command processing loop
while ($true) {{
    $input = Read-Host
    if ($input -eq "exit") {{ break }}
    Process-Command $input
}}
'''
        self._init_script.write_text(init_script_content)
        
        # Create PowerShell process with more robust settings
        powershell_command = [
            'powershell.exe',
            '-NoProfile',
            '-NonInteractive',
            '-ExecutionPolicy', 'Bypass',
            '-WindowStyle', 'Hidden',  # Hide the window to prevent interaction issues
            '-File', str(self._init_script)
        ]

        if self.username and self.username.lower() in ['root', 'openhands']:
            # For elevated privileges, we'll use Start-Process with RunAs
            powershell_command = [
                'powershell.exe',
                '-NoProfile',
                '-NonInteractive',
                '-ExecutionPolicy', 'Bypass',
                '-WindowStyle', 'Hidden',
                '-Command',
                f'Start-Process powershell -Verb RunAs -ArgumentList "-NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File \\"{self._init_script}\\"'
            ]

        logger.debug(f'Initializing PowerShell session with command: {powershell_command}')
        
        self._process = subprocess.Popen(
            powershell_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            bufsize=1,
            universal_newlines=True,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
        )
        
        # Wait for the process to be ready
        time.sleep(1)
        
        # Verify the process is running
        if self._process.poll() is not None:
            # Try to get any error output
            error_output = self._process.stderr.read() if self._process.stderr else "No error output available"
            raise RuntimeError(f'PowerShell process failed to start. Error: {error_output}')
        
        # Store the last command for interactive input handling
        self.prev_status: BashCommandStatus | None = None
        self.prev_output: str = ''
        self._closed: bool = False
        logger.debug(f'PowerShell session initialized with work dir: {self.work_dir}')
        self._initialized = True

    def __del__(self):
        """Ensure the session is closed when the object is destroyed."""
        self.close()

    def _send_command(self, command: str) -> None:
        """Send a command to the PowerShell process."""
        if not self._process:
            raise RuntimeError('PowerShell session is not initialized')
        
        try:
            # Check if process is still running
            if self._process.poll() is not None:
                raise RuntimeError('PowerShell process has terminated')
            
            # Write command to temporary script file
            self._command_script.write_text(command)
            
            # Log the command we're about to send
            cmd = f'& {{. "{self._command_script}"}}\n'
            logger.debug(f'Attempting to send command to PowerShell: {cmd!r}')
            
            # Ensure stdin is still open
            if self._process.stdin is None:
                raise RuntimeError('PowerShell stdin pipe is closed')
            
            # Send command to execute the script
            self._process.stdin.write(cmd)
            self._process.stdin.flush()
            time.sleep(0.1)  # Give PowerShell time to process the command
        except (OSError, IOError) as e:
            logger.error(f'Failed to send command to PowerShell: {e}')
            logger.error(f'Process state: poll={self._process.poll()}, stdin={self._process.stdin is not None}')
            raise RuntimeError(f'Failed to send command to PowerShell: {e}')

    def _get_process_output(self) -> str:
        """Get the current output from the PowerShell process."""
        if not self._process:
            raise RuntimeError('PowerShell session is not initialized')

        try:
            # Read all available output
            output = []
            while True:
                # Use a timeout to avoid blocking indefinitely
                try:
                    line = self._process.stdout.readline()
                    if not line:
                        break
                    output.append(line.rstrip())
                except Exception:
                    break
            
            return '\n'.join(output)
        except (OSError, IOError) as e:
            logger.error(f'Failed to read output from PowerShell: {e}')
            raise RuntimeError(f'Failed to read output from PowerShell: {e}')

    def close(self):
        """Clean up the PowerShell session."""
        if self._closed or not self._process:
            return
        
        try:
            # First try to terminate gracefully
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # If terminate doesn't work, try to kill the process
                self._process.kill()
        except Exception as e:
            logger.error(f'Error while closing PowerShell session: {e}')
        finally:
            # Clean up temporary files
            try:
                if hasattr(self, '_temp_dir') and self._temp_dir.exists():
                    import shutil
                    shutil.rmtree(self._temp_dir)
            except Exception as e:
                logger.error(f'Error while cleaning up temporary files: {e}')
            
            self._process = None
            self._closed = True

    @property
    def cwd(self):
        return self._cwd

    def _is_special_key(self, command: str) -> bool:
        """Check if the command is a special key."""
        # Special keys are of the form C-<key>
        _command = command.strip()
        return _command.startswith('C-') and len(_command) == 3

    def _clear_screen(self):
        """Clear the PowerShell screen."""
        self._send_command('Clear-Host')
        time.sleep(0.1)

    def _get_command_output(
        self,
        command: str,
        raw_command_output: str,
        metadata: CmdOutputMetadata,
        continue_prefix: str = '',
    ) -> str:
        """Get the command output with the previous command output removed."""
        if self.prev_output:
            command_output = raw_command_output.removeprefix(self.prev_output)
            metadata.prefix = continue_prefix
        else:
            command_output = raw_command_output
        self.prev_output = raw_command_output
        command_output = _remove_command_prefix(command_output, command)
        return command_output.rstrip()

    def _handle_completed_command(
        self, command: str, pane_content: str, ps1_matches: list[re.Match]
    ) -> CmdOutputObservation:
        is_special_key = self._is_special_key(command)
        assert len(ps1_matches) >= 1, (
            f'Expected at least one PS1 metadata block, but got {len(ps1_matches)}.\n'
            f'---FULL OUTPUT---\n{pane_content!r}\n---END OF OUTPUT---'
        )
        metadata = CmdOutputMetadata.from_ps1_match(ps1_matches[-1])

        # Special case where the previous command output is truncated due to history limit
        get_content_before_last_match = bool(len(ps1_matches) == 1)

        # Update the current working directory if it has changed
        if metadata.working_dir != self._cwd and metadata.working_dir:
            self._cwd = metadata.working_dir

        logger.debug(f'COMMAND OUTPUT: {pane_content}')
        # Extract the command output between the two PS1 prompts
        raw_command_output = self._combine_outputs_between_matches(
            pane_content,
            ps1_matches,
            get_content_before_last_match=get_content_before_last_match,
        )

        if get_content_before_last_match:
            # Count the number of lines in the truncated output
            num_lines = len(raw_command_output.splitlines())
            metadata.prefix = f'[Previous command outputs are truncated. Showing the last {num_lines} lines of the output below.]\n'

        metadata.suffix = (
            f'\n[The command completed with exit code {metadata.exit_code}.]'
            if not is_special_key
            else f'\n[The command completed with exit code {metadata.exit_code}. CTRL+{command[-1].upper()} was sent.]'
        )
        command_output = self._get_command_output(
            command,
            raw_command_output,
            metadata,
        )
        self.prev_status = BashCommandStatus.COMPLETED
        self.prev_output = ''  # Reset previous command output
        self._ready_for_next_command()
        return CmdOutputObservation(
            content=command_output,
            command=command,
            metadata=metadata,
        )

    def _handle_nochange_timeout_command(
        self,
        command: str,
        pane_content: str,
        ps1_matches: list[re.Match],
    ) -> CmdOutputObservation:
        self.prev_status = BashCommandStatus.NO_CHANGE_TIMEOUT
        if len(ps1_matches) != 1:
            logger.warning(
                'Expected exactly one PS1 metadata block BEFORE the execution of a command, '
                f'but got {len(ps1_matches)} PS1 metadata blocks:\n---\n{pane_content!r}\n---'
            )
        raw_command_output = self._combine_outputs_between_matches(
            pane_content, ps1_matches
        )
        metadata = CmdOutputMetadata()  # No metadata available
        metadata.suffix = (
            f'\n[The command has no new output after {self.NO_CHANGE_TIMEOUT_SECONDS} seconds. '
            "You may wait longer to see additional output by sending empty command '', "
            'send other commands to interact with the current process, '
            'or send keys to interrupt/kill the command.]'
        )
        command_output = self._get_command_output(
            command,
            raw_command_output,
            metadata,
            continue_prefix='[Below is the output of the previous command.]\n',
        )
        return CmdOutputObservation(
            content=command_output,
            command=command,
            metadata=metadata,
        )

    def _handle_hard_timeout_command(
        self,
        command: str,
        pane_content: str,
        ps1_matches: list[re.Match],
        timeout: float,
    ) -> CmdOutputObservation:
        self.prev_status = BashCommandStatus.HARD_TIMEOUT
        if len(ps1_matches) != 1:
            logger.warning(
                'Expected exactly one PS1 metadata block BEFORE the execution of a command, '
                f'but got {len(ps1_matches)} PS1 metadata blocks:\n---\n{pane_content!r}\n---'
            )
        raw_command_output = self._combine_outputs_between_matches(
            pane_content, ps1_matches
        )
        metadata = CmdOutputMetadata()  # No metadata available
        metadata.suffix = (
            f'\n[The command timed out after {timeout} seconds. '
            "You may wait longer to see additional output by sending empty command '', "
            'send other commands to interact with the current process, '
            'or send keys to interrupt/kill the command.]'
        )
        command_output = self._get_command_output(
            command,
            raw_command_output,
            metadata,
            continue_prefix='[Below is the output of the previous command.]\n',
        )

        return CmdOutputObservation(
            command=command,
            content=command_output,
            metadata=metadata,
        )

    def _ready_for_next_command(self):
        """Reset the content buffer for a new command."""
        self._clear_screen()

    def _combine_outputs_between_matches(
        self,
        pane_content: str,
        ps1_matches: list[re.Match],
        get_content_before_last_match: bool = False,
    ) -> str:
        """Combine all outputs between PS1 matches."""
        if len(ps1_matches) == 1:
            if get_content_before_last_match:
                # The command output is the content before the last PS1 prompt
                return pane_content[: ps1_matches[0].start()]
            else:
                # The command output is the content after the last PS1 prompt
                return pane_content[ps1_matches[0].end() + 1 :]
        elif len(ps1_matches) == 0:
            return pane_content
        combined_output = ''
        for i in range(len(ps1_matches) - 1):
            # Extract content between current and next PS1 prompt
            output_segment = pane_content[
                ps1_matches[i].end() + 1 : ps1_matches[i + 1].start()
            ]
            combined_output += output_segment + '\n'
        logger.debug(f'COMBINED OUTPUT: {combined_output}')
        return combined_output

    def execute(self, action: CmdRunAction) -> CmdOutputObservation | ErrorObservation:
        """Execute a command in the PowerShell session."""
        if not self._initialized:
            raise RuntimeError('PowerShell session is not initialized')

        # Strip the command of any leading/trailing whitespace
        logger.debug(f'RECEIVED ACTION: {action}')
        command = action.command.strip()
        is_input: bool = action.is_input

        # If the previous command is not completed, we need to check if the command is empty
        if self.prev_status not in {
            BashCommandStatus.CONTINUE,
            BashCommandStatus.NO_CHANGE_TIMEOUT,
            BashCommandStatus.HARD_TIMEOUT,
        }:
            if command == '':
                return CmdOutputObservation(
                    content='ERROR: No previous running command to retrieve logs from.',
                    command='',
                    metadata=CmdOutputMetadata(),
                )
            if is_input:
                return CmdOutputObservation(
                    content='ERROR: No previous running command to interact with.',
                    command='',
                    metadata=CmdOutputMetadata(),
                )

        # Check if the command is a single command or multiple commands
        splited_commands = split_bash_commands(command)
        if len(splited_commands) > 1:
            return ErrorObservation(
                content=(
                    f'ERROR: Cannot execute multiple commands at once.\n'
                    f'Please run each command separately OR chain them into a single command via && or ;\n'
                    f'Provided commands:\n{"\n".join(f"({i+1}) {cmd}" for i, cmd in enumerate(splited_commands))}'
                )
            )

        start_time = time.time()
        last_change_time = start_time
        last_pane_output = self._get_process_output()

        # When prev command is still running, and we are trying to send a new command
        if (
            self.prev_status
            in {
                BashCommandStatus.HARD_TIMEOUT,
                BashCommandStatus.NO_CHANGE_TIMEOUT,
            }
            and not last_pane_output.endswith(
                CMD_OUTPUT_PS1_END
            )  # prev command is not completed
            and not is_input
            and command != ''  # not input and not empty command
        ):
            _ps1_matches = CmdOutputMetadata.matches_ps1_metadata(last_pane_output)
            raw_command_output = self._combine_outputs_between_matches(
                last_pane_output, _ps1_matches
            )
            metadata = CmdOutputMetadata()  # No metadata available
            metadata.suffix = (
                f'\n[Your command "{command}" is NOT executed. '
                f'The previous command is still running - You CANNOT send new commands until the previous command is completed. '
                'By setting `is_input` to `true`, you can interact with the current process: '
                "You may wait longer to see additional output of the previous command by sending empty command '', "
                'send other commands to interact with the current process, '
                'or send keys ("C-c", "C-z", "C-d") to interrupt/kill the previous command before sending your new command.]'
            )
            logger.debug(f'PREVIOUS COMMAND OUTPUT: {raw_command_output}')
            command_output = self._get_command_output(
                command,
                raw_command_output,
                metadata,
                continue_prefix='[Below is the output of the previous command.]\n',
            )
            return CmdOutputObservation(
                command=command,
                content=command_output,
                metadata=metadata,
            )

        # Send actual command/inputs to the process
        if command != '':
            is_special_key = self._is_special_key(command)
            if is_input:
                logger.debug(f'SENDING INPUT TO RUNNING PROCESS: {command!r}')
                self._send_command(command)
            else:
                # convert command to raw string
                command = escape_powershell_special_chars(command)
                logger.debug(f'SENDING COMMAND: {command!r}')
                self._send_command(command)

        # Loop until the command completes or times out
        while should_continue():
            _start_time = time.time()
            logger.debug(f'GETTING PROCESS OUTPUT at {_start_time}')
            cur_pane_output = self._get_process_output()
            logger.debug(
                f'PROCESS OUTPUT GOT after {time.time() - _start_time:.2f} seconds'
            )
            logger.debug(f'BEGIN OF PROCESS OUTPUT: {cur_pane_output.split("\n")[:10]}')
            logger.debug(f'END OF PROCESS OUTPUT: {cur_pane_output.split("\n")[-10:]}')
            ps1_matches = CmdOutputMetadata.matches_ps1_metadata(cur_pane_output)
            if cur_pane_output != last_pane_output:
                last_pane_output = cur_pane_output
                last_change_time = time.time()
                logger.debug(f'CONTENT UPDATED DETECTED at {last_change_time}')

            # 1) Execution completed
            # if the last command output contains the end marker
            if cur_pane_output.rstrip().endswith(CMD_OUTPUT_PS1_END.rstrip()):
                return self._handle_completed_command(
                    command,
                    pane_content=cur_pane_output,
                    ps1_matches=ps1_matches,
                )

            # 2) Execution timed out since there's no change in output
            # for a while (self.NO_CHANGE_TIMEOUT_SECONDS)
            # We ignore this if the command is *blocking
            time_since_last_change = time.time() - last_change_time
            logger.debug(
                f'CHECKING NO CHANGE TIMEOUT ({self.NO_CHANGE_TIMEOUT_SECONDS}s): elapsed {time_since_last_change}. Action blocking: {action.blocking}'
            )
            if (
                not action.blocking
                and time_since_last_change >= self.NO_CHANGE_TIMEOUT_SECONDS
            ):
                return self._handle_nochange_timeout_command(
                    command,
                    pane_content=cur_pane_output,
                    ps1_matches=ps1_matches,
                )

            # 3) Execution timed out due to hard timeout
            logger.debug(
                f'CHECKING HARD TIMEOUT ({action.timeout}s): elapsed {time.time() - start_time}'
            )
            if action.timeout and time.time() - start_time >= action.timeout:
                return self._handle_hard_timeout_command(
                    command,
                    pane_content=cur_pane_output,
                    ps1_matches=ps1_matches,
                    timeout=action.timeout,
                )

            logger.debug(f'SLEEPING for {self.POLL_INTERVAL} seconds for next poll')
            time.sleep(self.POLL_INTERVAL)
        raise RuntimeError('PowerShell session was likely interrupted...')
