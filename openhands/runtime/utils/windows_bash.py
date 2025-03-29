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
        # Execute the command and capture output
        $output = Invoke-Expression $command 2>&1
        $exitCode = $LASTEXITCODE
        
        # Output the result
        if ($output) {{ $output | Out-String }}
        
        # Output PS1 prompt with metadata
        Write-Host "{self.PS1}"
        
        # Return exit code
        return $exitCode
    }} catch {{
        Write-Error $_.Exception.Message
        Write-Host "{self.PS1}"
        return 1
    }}
}}

# Output initial PS1 prompt
Write-Host "{self.PS1}"

# Main command processing loop
while ($true) {{
    $input = Read-Host
    if ($input -eq "exit") {{ break }}
    $exitCode = Process-Command $input
    $LASTEXITCODE = $exitCode
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
        
        # Wait for the process to be ready and get initial PS1 prompt
        time.sleep(1)
        initial_output = self._get_process_output()
        if not initial_output or self.PS1 not in initial_output:
            raise RuntimeError('Failed to get initial PS1 prompt from PowerShell')
        
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
            
            # Log the command we're about to send
            logger.debug(f'Attempting to send command to PowerShell: {command!r}')
            
            # Ensure stdin is still open
            if self._process.stdin is None:
                raise RuntimeError('PowerShell stdin pipe is closed')
            
            # Log process state before sending
            logger.debug(f'Process state before send: poll={self._process.poll()}, stdin={self._process.stdin is not None}')
            
            # Send command directly to PowerShell
            self._process.stdin.write(f"{command}\n")
            self._process.stdin.flush()
            logger.debug('Command sent and flushed to stdin')
            
            time.sleep(0.1)  # Give PowerShell time to process the command
            logger.debug('After sleep, checking process state')
            
            # Check process state after sending
            if self._process.poll() is not None:
                logger.error(f'Process terminated after sending command. Exit code: {self._process.poll()}')
                if self._process.stderr:
                    error_output = self._process.stderr.read()
                    logger.error(f'Process stderr: {error_output}')
                raise RuntimeError('PowerShell process terminated after sending command')
                
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
            print('Starting to read process output')
            logger.debug('Starting to read process output')
            
            # Set a timeout for reading
            timeout = 1.0  # 1 second timeout for the overall operation
            start_time = time.time()
            
            while True:
                # Check if we've exceeded the timeout
                if time.time() - start_time > timeout:
                    print('Timeout reached while reading output')
                    logger.debug('Timeout reached while reading output')
                    break
                
                try:
                    print('Attempting to read line from stdout')
                    logger.debug('Attempting to read line from stdout')
                    
                    # Check if there's data available to read
                    if not self._process.stdout:
                        print('stdout is None')
                        break
                    
                    # Try to read a line with a longer timeout
                    try:
                        # Use a thread to read the line with a timeout
                        import threading
                        line = [None]
                        def read_line():
                            line[0] = self._process.stdout.readline()
                        
                        thread = threading.Thread(target=read_line)
                        thread.daemon = True
                        thread.start()
                        thread.join(timeout=0.1)  # Wait up to 100ms for the read
                        
                        if thread.is_alive():
                            # Read timed out, continue
                            continue
                            
                        if line[0] is None:
                            # No data available
                            continue
                            
                    except Exception as e:
                        print(f'Error during readline: {e}')
                        break
                        
                    if not line[0]:
                        print('No more output available')
                        logger.debug('No more output available')
                        break
                        
                    # Skip empty lines
                    if not line[0].strip():
                        continue
                        
                    print(f'Read line: {line[0].rstrip()}')
                    logger.debug(f'Read line: {line[0].rstrip()}')
                    output.append(line[0].rstrip())
                    
                    # If we've found a PS1 prompt, we can stop reading
                    if self.PS1 in line[0]:
                        # If we have some output before the PS1 prompt, we can stop
                        if len(output) > 1:  # > 1 because the last line is the PS1 prompt
                            break
                        
                except Exception as e:
                    print(f'Error reading line from stdout: {e}')
                    logger.error(f'Error reading line from stdout: {e}')
                    break
            
            result = '\n'.join(output)
            logger.debug(f'Final output: {result}')
            return result
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
        print(f'RECEIVED ACTION: {action}')
        command = action.command.strip()
        is_input: bool = action.is_input

        # If the previous command is not completed, we need to check if the command is empty
        if self.prev_status not in {
            BashCommandStatus.CONTINUE,
            BashCommandStatus.NO_CHANGE_TIMEOUT,
            BashCommandStatus.HARD_TIMEOUT,
        }:
            print(f'PREVIOUS STATUS: {self.prev_status}')
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

        print(f'COMMAND: {command}')
        # Check if the command is a single command or multiple commands
        splited_commands = split_bash_commands(command)
        print(f'SPLIT COMMANDS: {splited_commands}')
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
        print(f'START TIME: {start_time}')
        logger.debug('Getting initial process output')
        last_pane_output = self._get_process_output()
        print(f'LAST PANE OUTPUT: {last_pane_output}')
        logger.debug(f'Initial process output: {last_pane_output}')

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
            print('Previous command still running, handling timeout state')
            logger.debug('Previous command still running, handling timeout state')
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
            print(f'PREVIOUS COMMAND OUTPUT: {raw_command_output}')
            logger.debug(f'PREVIOUS COMMAND OUTPUT: {raw_command_output}')
            command_output = self._get_command_output(
                command,
                raw_command_output,
                metadata,
                continue_prefix='[Below is the output of the previous command.]\n',
            )
            print(f'COMMAND OUTPUT: {command_output}')
            return CmdOutputObservation(
                command=command,
                content=command_output,
                metadata=metadata,
            )

        # Send actual command/inputs to the process
        if command != '':
            print(f'SENDING COMMAND: {command!r}')
            is_special_key = self._is_special_key(command)
            if is_input:
                print(f'SENDING INPUT TO RUNNING PROCESS: {command!r}')
                logger.debug(f'SENDING INPUT TO RUNNING PROCESS: {command!r}')
                self._send_command(command)
            else:
                # convert command to raw string
                command = escape_powershell_special_chars(command)
                print(f'SENDING COMMAND: {command!r}')
                logger.debug(f'SENDING COMMAND: {command!r}')
                self._send_command(command)

        # Loop until the command completes or times out
        iteration = 0
        while should_continue():
            print(f'ITERATION: {iteration}')
            iteration += 1
            _start_time = time.time()
            logger.debug(f'Iteration {iteration}: Getting process output at {_start_time}')
            cur_pane_output = self._get_process_output()
            logger.debug(
                f'Iteration {iteration}: Process output received after {time.time() - _start_time:.2f} seconds'
            )
            logger.debug(f'Iteration {iteration}: BEGIN OF PROCESS OUTPUT: {cur_pane_output.split("\n")[:10]}')
            logger.debug(f'Iteration {iteration}: END OF PROCESS OUTPUT: {cur_pane_output.split("\n")[-10:]}')
            
            ps1_matches = CmdOutputMetadata.matches_ps1_metadata(cur_pane_output)
            logger.debug(f'Iteration {iteration}: Found {len(ps1_matches)} PS1 matches')
            
            if cur_pane_output != last_pane_output:
                last_pane_output = cur_pane_output
                last_change_time = time.time()
                logger.debug(f'Iteration {iteration}: Content updated detected at {last_change_time}')

            # 1) Execution completed
            # if the last command output contains the end marker
            if cur_pane_output.rstrip().endswith(CMD_OUTPUT_PS1_END.rstrip()):
                print(f'Iteration {iteration}: Command completed, handling completion')
                logger.debug(f'Iteration {iteration}: Command completed, handling completion')
                return self._handle_completed_command(
                    command,
                    pane_content=cur_pane_output,
                    ps1_matches=ps1_matches,
                )

            # 2) Execution timed out since there's no change in output
            # for a while (self.NO_CHANGE_TIMEOUT_SECONDS)
            # We ignore this if the command is *blocking
            time_since_last_change = time.time() - last_change_time
            print(f'Iteration {iteration}: Time since last change: {time_since_last_change}')
            logger.debug(
                f'Iteration {iteration}: Checking no-change timeout ({self.NO_CHANGE_TIMEOUT_SECONDS}s): elapsed {time_since_last_change}. Action blocking: {action.blocking}'
            )
            if (
                not action.blocking
                and time_since_last_change >= self.NO_CHANGE_TIMEOUT_SECONDS
            ):
                print(f'Iteration {iteration}: No change timeout reached, handling timeout')
                logger.debug(f'Iteration {iteration}: No change timeout reached, handling timeout')
                return self._handle_nochange_timeout_command(
                    command,
                    pane_content=cur_pane_output,
                    ps1_matches=ps1_matches,
                )

            # 3) Execution timed out due to hard timeout
            elapsed_time = time.time() - start_time
            print(f'Iteration {iteration}: Elapsed time: {elapsed_time}')
            logger.debug(
                f'Iteration {iteration}: Checking hard timeout ({action.timeout}s): elapsed {elapsed_time}'
            )
            if action.timeout and elapsed_time >= action.timeout:
                print(f'Iteration {iteration}: Hard timeout reached, handling timeout')
                logger.debug(f'Iteration {iteration}: Hard timeout reached, handling timeout')
                return self._handle_hard_timeout_command(
                    command,
                    pane_content=cur_pane_output,
                    ps1_matches=ps1_matches,
                    timeout=action.timeout,
                )

            print(f'Iteration {iteration}: Sleeping for {self.POLL_INTERVAL} seconds')
            logger.debug(f'Iteration {iteration}: Sleeping for {self.POLL_INTERVAL} seconds')
            time.sleep(self.POLL_INTERVAL)
            
        logger.error('PowerShell session was interrupted')
        raise RuntimeError('PowerShell session was likely interrupted...')
