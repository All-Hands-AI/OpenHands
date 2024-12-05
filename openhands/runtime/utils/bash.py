import os
import re
import tempfile
import threading
import time
import uuid
from enum import Enum

import bashlex
import libtmux

from openhands.core.logger import openhands_logger as logger
from openhands.events.action import CmdRunAction
from openhands.events.observation import ErrorObservation
from openhands.events.observation.commands import (
    CMD_OUTPUT_PS1_END,
    CmdOutputMetadata,
    CmdOutputObservation,
)


def split_bash_commands(commands):
    if not commands.strip():
        return ['']
    try:
        parsed = bashlex.parse(commands)
    except bashlex.errors.ParsingError as e:
        logger.debug(
            f'Failed to parse bash commands\n'
            f'[input]: {commands}\n'
            f'[warning]: {e}\n'
            f'The original command will be returned as is.'
        )
        # If parsing fails, return the original commands
        return [commands]

    result: list[str] = []
    last_end = 0

    for node in parsed:
        start, end = node.pos

        # Include any text between the last command and this one
        if start > last_end:
            between = commands[last_end:start]
            logger.debug(f'BASH PARSING between: {between}')
            if result:
                result[-1] += between.rstrip()
            elif between.strip():
                # THIS SHOULD NOT HAPPEN
                result.append(between.rstrip())

        # Extract the command, preserving original formatting
        command = commands[start:end].rstrip()
        logger.debug(f'BASH PARSING command: {command}')
        result.append(command)

        last_end = end

    # Add any remaining text after the last command to the last command
    remaining = commands[last_end:].rstrip()
    logger.debug(f'BASH PARSING remaining: {remaining}')
    if last_end < len(commands) and result:
        result[-1] += remaining
        logger.debug(f'BASH PARSING result[-1] += remaining: {result[-1]}')
    elif last_end < len(commands):
        if remaining:
            result.append(remaining)
            logger.debug(f'BASH PARSING result.append(remaining): {result[-1]}')
    return result


class BashCommandStatus(Enum):
    CONTINUE = 'continue'
    COMPLETED = 'completed'
    NO_CHANGE_TIMEOUT = 'no_change_timeout'
    HARD_TIMEOUT = 'hard_timeout'


def _remove_command_prefix(command_output: str, command: str) -> str:
    return command_output.lstrip().removeprefix(command.lstrip()).lstrip()


class BashSession:
    POLL_INTERVAL = 0.5
    PS1 = CmdOutputMetadata.to_ps1_prompt()

    def __init__(
        self,
        work_dir: str,
        username: str | None = None,
        no_change_timeout_seconds: float = 30.0,
    ):
        self.NO_CHANGE_TIMEOUT_SECONDS = no_change_timeout_seconds

        self.server = libtmux.Server()
        window_command = '/bin/bash'
        if username:
            # This starts a non-login (new) shell for the given user
            window_command = f'su {username} -'

        session_name = f'openhands-{username}-{uuid.uuid4()}'
        self.session = self.server.new_session(
            session_name=session_name,
            window_name='bash',
            window_command=window_command,
            start_directory=work_dir,
            kill_session=True,
            x=1000,
            y=1000,
        )
        self.pane = self.session.attached_pane
        # Configure bash to use simple PS1 and disable PS2
        self.pane.send_keys(
            f'export PROMPT_COMMAND=\'export PS1="{self.PS1}"\'; export PS2=""'
        )
        time.sleep(0.2)  # Wait for command to take effect
        self._clear_screen()

        # Store the last command for interactive input handling
        self.prev_status: BashCommandStatus | None = None
        self.prev_output: str = ''
        self._closed: bool = False
        logger.debug(f'Bash session initialized with work dir: {work_dir}')

        # Maintain the current working directory
        self._pwd = os.path.abspath(work_dir)

        # Create a single named pipe for the session
        self.output_pipe = os.path.join(tempfile.mkdtemp(), 'output.pipe')
        try:
            os.mkfifo(self.output_pipe)
        except FileExistsError as e:
            logger.warning(f'Failed to create named pipe: {e}. {self.output_pipe}')

        # Add lock and current content
        self._pane_content_lock = threading.Lock()
        self._current_pane_content = ''
        self._stop_reader = threading.Event()
        self._reader_thread: threading.Thread | None = None

        # Start the pipe and reader thread
        self._setup_pipe()

    def __del__(self):
        """Ensure the session is closed when the object is destroyed."""
        self.close()

    def _setup_pipe(self):
        """Set up pipe-pane to write to the named pipe."""
        # Stop existing pipe
        self.pane.cmd('pipe-pane')

        logger.debug(f'Setting up pipe-pane to {self.output_pipe}')
        # Set up new pipe-pane
        self.pane.cmd('pipe-pane', f'cat > {self.output_pipe} 2>&1')

        # Start the reader thread if not already running
        assert self._reader_thread is None, 'Expected reader thread not running'
        self._stop_reader.clear()
        self._reader_thread = threading.Thread(
            target=self._read_from_pipe,
            daemon=True,
        )
        self._reader_thread.start()

        # Hit enter to trigger the FIRST PS1
        self.pane.enter()
        time.sleep(1)

    def _read_from_pipe(self):
        """Read from the named pipe and append to current content."""
        try:
            with open(self.output_pipe, 'r', buffering=1) as pipe:
                while not self._stop_reader.is_set():
                    line = pipe.readline()
                    if not line:
                        break
                    with self._pane_content_lock:
                        self._current_pane_content += line
                    logger.debug(f'PIPE OUTPUT: {line.strip()}')
        except Exception as e:
            logger.error(f'Error reading from pipe: {e}')

    def close(self):
        """Clean up the session and all output files."""
        if self._closed:
            return

        # Stop the reader thread
        if self._reader_thread and self._reader_thread.is_alive():
            self._stop_reader.set()
            self._reader_thread.join(
                timeout=1.0
            )  # Wait up to 1 second for thread to finish

        # Stop piping output
        self.pane.cmd('pipe-pane')

        # Clean up all output files and directory
        if os.path.exists(self.output_pipe):
            os.remove(self.output_pipe)
            # also remove the directory if empty
            if not os.listdir(os.path.dirname(self.output_pipe)):
                os.rmdir(os.path.dirname(self.output_pipe))

        self.session.kill_session()
        self._closed = True

    @property
    def pwd(self):
        return self._pwd

    def _is_special_key(self, command: str) -> bool:
        """Check if the command is a special key."""
        # Special keys are of the form C-<key>
        _command = command.strip()
        return _command.startswith('C-') and len(_command) == 3

    def _clear_screen(self):
        """Clear the tmux pane screen and history."""
        self.pane.send_keys('C-l', enter=False)
        time.sleep(0.1)
        self.pane.cmd('clear-history')

    def _get_pane_content(self) -> str:
        """Get the current content."""
        with self._pane_content_lock:
            # Clean up the bracketed paste mode and terminal clear sequence
            cleaned = re.sub(
                r'\x1b\[\?2004[hl]|\x1b\[H|\x1b\[J', '', self._current_pane_content
            )
            return cleaned

    def _get_command_output(
        self,
        command: str,
        raw_command_output: str,
        metadata: CmdOutputMetadata,
        continue_prefix: str = '',
    ) -> str:
        """Get the command output with the previous command output removed.

        Args:
            command: The command that was executed.
            raw_command_output: The raw output from the command.
            metadata: The metadata object to store prefix/suffix in.
            continue_prefix: The prefix to add to the command output if it's a continuation of the previous command.
        """
        # remove the previous command output from the new output if any
        if self.prev_output:
            command_output = raw_command_output.removeprefix(self.prev_output)
            metadata.prefix = continue_prefix
        else:
            command_output = raw_command_output
        self.prev_output = raw_command_output  # update current command output anyway
        command_output = _remove_command_prefix(command_output, command)
        return command_output

    def _handle_completed_command(
        self, command: str, pane_content: str, ps1_matches: list[re.Match]
    ) -> CmdOutputObservation:
        is_special_key = self._is_special_key(command)
        assert len(ps1_matches) >= 2, (
            f'Expected at least two PS1 metadata blocks, but got {len(ps1_matches)}.\n'
            f'---FULL OUTPUT---\n{pane_content!r}\n---END OF OUTPUT---'
        )
        metadata = CmdOutputMetadata.from_ps1_match(ps1_matches[-1])
        # Update the current working directory if it has changed
        if metadata.working_dir != self._pwd and metadata.working_dir:
            self._pwd = metadata.working_dir
        # Extract the command output between the two PS1 prompts
        raw_command_output = self._combine_outputs_between_matches(
            pane_content, ps1_matches
        )
        metadata.suffix = (
            f'\n\n[The command completed with exit code {metadata.exit_code}.]'
            if not is_special_key
            else f'\n\n[The command completed with exit code {metadata.exit_code}. CTRL+{command[-1].upper()} was sent.]'
        )
        command_output = self._get_command_output(
            command,
            raw_command_output,
            metadata,
        )
        self.prev_status = BashCommandStatus.COMPLETED
        self.prev_output = ''  # Reset previous command output
        self._clear_screen()
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
            f'\n\n[The command has no new output after {self.NO_CHANGE_TIMEOUT_SECONDS} seconds. '
            "You may wait longer to see additional output by sending empty command '', "
            'send other commands to interact with the current process, '
            'or send keys to interrupt/kill the command.]'
        )
        command_output = self._get_command_output(
            command,
            raw_command_output,
            metadata,
            continue_prefix='[Command output continued from previous command]\n',
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
            f'\n\n[The command timed out after {timeout} seconds. '
            "You may wait longer to see additional output by sending empty command '', "
            'send other commands to interact with the current process, '
            'or send keys to interrupt/kill the command.]'
        )
        command_output = self._get_command_output(
            command,
            raw_command_output,
            metadata,
            continue_prefix='[Command output continued from previous command]\n',
        )

        return CmdOutputObservation(
            command=command,
            content=command_output,
            metadata=metadata,
        )

    def _ready_for_next_command(self):
        """Reset the content buffer for a new command."""
        # Clear the current content
        with self._pane_content_lock:
            self._current_pane_content = ''

        # Hit enter to ensure we get a fresh PS1 prompt
        self.pane.enter()
        time.sleep(0.1)  # Small delay to ensure prompt appears

    def _combine_outputs_between_matches(
        self, pane_content: str, ps1_matches: list[re.Match]
    ) -> str:
        """Combine all outputs between PS1 matches.

        Args:
            pane_content: The full pane content containing PS1 prompts and command outputs
            ps1_matches: List of regex matches for PS1 prompts

        Returns:
            Combined string of all outputs between matches
        """
        if len(ps1_matches) == 1:
            return pane_content[ps1_matches[0].end() + 1 :]
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
        """Execute a command in the bash session."""
        # Strip the command of any leading/trailing whitespace
        command = action.command.strip()

        if command == '' and self.prev_status not in {
            BashCommandStatus.CONTINUE,
            BashCommandStatus.NO_CHANGE_TIMEOUT,
            BashCommandStatus.HARD_TIMEOUT,
        }:
            return CmdOutputObservation(
                content='ERROR: No previous command to continue from. '
                + 'Previous command has to be timeout to be continued.',
                command='',
                metadata=CmdOutputMetadata(),
            )

        if self.prev_status == BashCommandStatus.COMPLETED:
            self._ready_for_next_command()

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
        last_pane_output = self._get_pane_content()

        _ps1_matches = CmdOutputMetadata.matches_ps1_metadata(last_pane_output)
        if len(_ps1_matches) < 1:
            self.pane.enter()
            time.sleep(0.1)
            last_pane_output = self._get_pane_content()
            _ps1_matches = CmdOutputMetadata.matches_ps1_metadata(last_pane_output)
            logger.warning(
                'No PS1 metadata block found before the execution of a command. '
                'Hitting enter to get a fresh PS1 prompt:\n---\n'
                f'{last_pane_output!r}\n---'
            )
        assert len(_ps1_matches) >= 1, (
            'Expected at least one PS1 metadata block BEFORE the execution of a command, '
            f'but got {len(_ps1_matches)} PS1 metadata blocks:\n---\n{last_pane_output!r}\n---'
        )
        if len(_ps1_matches) > 1:
            logger.warning(
                'Found multiple PS1 metadata blocks BEFORE the execution of a command. '
                'Only the last one will be used.'
            )
            _ps1_matches = [_ps1_matches[-1]]

        if command != '':
            logger.debug(f'SENDING COMMAND: {command}')
            self.pane.send_keys(
                command,
                enter=not self._is_special_key(command),
            )

        # Loop until the command completes or times out
        while True:
            cur_pane_output = self._get_pane_content()
            ps1_matches = CmdOutputMetadata.matches_ps1_metadata(cur_pane_output)
            if cur_pane_output != last_pane_output:
                last_pane_output = cur_pane_output
                last_change_time = time.time()

            # 1) Execution completed
            # if the last command output contains the end marker
            if (
                cur_pane_output.rstrip().endswith(CMD_OUTPUT_PS1_END.rstrip())
                and len(ps1_matches) == 2
            ):
                return self._handle_completed_command(
                    command,
                    pane_content=cur_pane_output,
                    ps1_matches=ps1_matches,
                )

            # 2) Execution timed out since there's no change in output
            # for a while (self.NO_CHANGE_TIMEOUT_SECONDS)
            # We ignore this if the command is *blocking
            time_since_last_change = time.time() - last_change_time
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
            if action.timeout and time.time() - start_time >= action.timeout:
                return self._handle_hard_timeout_command(
                    command,
                    pane_content=cur_pane_output,
                    ps1_matches=ps1_matches,
                    timeout=action.timeout,
                )

            time.sleep(self.POLL_INTERVAL)
