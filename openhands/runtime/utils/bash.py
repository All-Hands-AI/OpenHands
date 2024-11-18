import time
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
            window_command = f'su {username}'

        self.session = self.server.new_session(
            session_name=f'openhands-{username}',
            window_name='bash',
            window_command=window_command,
            start_directory=work_dir,
            kill_session=True,
        )
        self.pane = self.session.attached_window.attached_pane

        # Configure bash to use simple PS1 and disable PS2
        self.pane.send_keys(
            f'export PROMPT_COMMAND=\'export PS1="{self.PS1}"\'; export PS2=""'
        )
        time.sleep(0.2)  # Wait for command to take effect
        self._clear_screen()

        # Store the last command for interactive input handling
        self.prev_status: BashCommandStatus | None = None
        self.prev_output: str = ''
        logger.debug(f'Bash session initialized with work dir: {work_dir}')

    def close(self):
        self.session.kill_session()

    @property
    def pwd(self):
        self._pwd = self.pane.cmd(
            'display-message', '-p', '#{pane_current_path}'
        ).stdout[0]
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

    def _get_pane_content(self, full: bool = False) -> str:
        """Get the current content of the tmux pane.

        Args:
            full: If True, capture the entire history of the pane.
        """
        # https://man7.org/linux/man-pages/man1/tmux.1.html
        # -J preserves trailing spaces and joins any wrapped lines;
        # -p direct output to stdout
        # -S -: start from the start of history
        if full:
            # Capture the entire history of the pane
            return '\n'.join(self.pane.cmd('capture-pane', '-J', '-pS', '-').stdout)
        return '\n'.join(self.pane.cmd('capture-pane', '-J', '-p').stdout)

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

    def _handle_completed_command(self, command: str) -> CmdOutputObservation:
        full_output = self._get_pane_content(full=True)

        ps1_matches = CmdOutputMetadata.matches_ps1_metadata(full_output)
        assert len(ps1_matches) == 2, 'Expected exactly two PS1 metadata blocks'
        metadata = CmdOutputMetadata.from_ps1_match(ps1_matches[1])
        is_special_key = self._is_special_key(command)
        # Extract the command output between the two PS1 prompts
        raw_command_output = full_output[
            ps1_matches[0].end() + 1 : ps1_matches[1].start()
        ]
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

    def _handle_nochange_timeout_command(self, command: str) -> CmdOutputObservation:
        self.prev_status = BashCommandStatus.NO_CHANGE_TIMEOUT
        full_output = self._get_pane_content(full=True)

        ps1_matches = CmdOutputMetadata.matches_ps1_metadata(full_output)
        assert len(ps1_matches) == 1, 'Expected exactly one PS1 metadata block'

        raw_command_output = full_output[ps1_matches[0].end() + 1 :]
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
        self, command: str, timeout: float
    ) -> CmdOutputObservation:
        self.prev_status = BashCommandStatus.HARD_TIMEOUT
        full_output = self._get_pane_content(full=True)
        ps1_matches = CmdOutputMetadata.matches_ps1_metadata(full_output)
        assert len(ps1_matches) == 1, 'Expected exactly one PS1 metadata block'

        raw_command_output = full_output[ps1_matches[0].end() + 1 :]
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

    def execute(self, action: CmdRunAction) -> CmdOutputObservation | ErrorObservation:
        """Execute a command in the bash session."""
        logger.debug(f'Executing command: {action.command}')
        splited_commands = split_bash_commands(action.command)
        if len(splited_commands) > 1:
            return ErrorObservation(
                content=(
                    f'ERROR: Cannot execute multiple commands at once.\n'
                    f'Please run each command separately OR chain them into a single command via && or ;\n'
                    f'Provided commands:\n{"\n".join(f"({i+1}) {cmd}" for i, cmd in enumerate(splited_commands))}'
                )
            )

        if action.command.strip() == '' and self.prev_status not in {
            BashCommandStatus.CONTINUE,
            BashCommandStatus.COMPLETED,
            BashCommandStatus.NO_CHANGE_TIMEOUT,
            BashCommandStatus.HARD_TIMEOUT,
        }:
            return CmdOutputObservation(
                content='ERROR: No previous command to continue from. '
                + 'Previous command has to be timeout to be continued.',
                command='',
                metadata=CmdOutputMetadata(),
            )

        start_time = time.time()
        last_change_time = start_time
        last_pane_output = self._get_pane_content()

        assert (
            len(CmdOutputMetadata.matches_ps1_metadata(last_pane_output)) == 1
        ), 'Expected exactly one PS1 metadata block BEFORE the execution of a command'

        if action.command.strip() != '':
            self.pane.send_keys(
                action.command,
                # do not send enter for special keys
                enter=not self._is_special_key(action.command),
            )

        # Loop until the command completes or times out
        while True:
            cur_pane_output = self._get_pane_content()
            if cur_pane_output != last_pane_output:
                last_pane_output = cur_pane_output
                last_change_time = time.time()

            # 1) Execution completed
            # if the last command output contains the end marker
            if cur_pane_output.rstrip().endswith(CMD_OUTPUT_PS1_END.rstrip()):
                return self._handle_completed_command(action.command)

            # 2) Execution timed out since there's no change in output
            # for a while (self.NO_CHANGE_TIMEOUT_SECONDS)
            # We ignore this if the command is *blocking
            time_since_last_change = time.time() - last_change_time
            if (
                not action.blocking
                and time_since_last_change >= self.NO_CHANGE_TIMEOUT_SECONDS
            ):
                return self._handle_nochange_timeout_command(action.command)

            # 3) Execution timed out due to hard timeout
            if action.timeout and time.time() - start_time >= action.timeout:
                return self._handle_hard_timeout_command(action.command, action.timeout)

            time.sleep(self.POLL_INTERVAL)
