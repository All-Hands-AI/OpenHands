import time
from enum import Enum

import libtmux

from openhands.events.action import CmdRunAction
from openhands.events.observation.commands import (
    CMD_OUTPUT_PS1_END,
    CmdOutputMetadata,
    CmdOutputObservation,
)


class BashCommandStatus(Enum):
    CONTINUE = 'continue'
    COMPLETED = 'completed'
    NO_CHANGE_TIMEOUT = 'no_change_timeout'
    HARD_TIMEOUT = 'hard_timeout'


class BashSession:
    NO_CHANGE_TIMEOUT_SECONDS = 10.0
    POLL_INTERVAL = 0.5
    PS1 = CmdOutputMetadata.to_ps1_prompt()

    def __init__(self, work_dir: str, username: str | None = None):
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

    def close(self):
        self.session.kill_session()

    @property
    def pwd(self):
        self._pwd = self.pane.cmd(
            'display-message', '-p', '#{pane_current_path}'
        ).stdout[0]
        return self._pwd

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

    def _handle_completed_command(self, command: str) -> CmdOutputObservation:
        self.prev_status = BashCommandStatus.COMPLETED
        self.prev_output = ''  # Reset previous command output
        full_output = self._get_pane_content(full=True)

        ps1_matches = CmdOutputMetadata.matches_ps1_metadata(full_output)
        assert len(ps1_matches) == 2, 'Expected exactly two PS1 metadata blocks'
        metadata = CmdOutputMetadata.from_ps1_match(ps1_matches[1])

        # Extract the command output between the two PS1 prompts
        command_output = full_output[ps1_matches[0].end() + 1 : ps1_matches[1].start()]
        command_output = command_output.lstrip().removeprefix(command.lstrip()).lstrip()

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

        command_output = full_output[ps1_matches[0].end() + 1 :]
        # remove the previous command output from the new output if any
        if self.prev_output:
            _clean_command_output = command_output.removeprefix(self.prev_output)
            command_output = (
                '[Command output continued from previous command]\n'
                + _clean_command_output
            )
            self.prev_output = _clean_command_output

        command_output += (
            f'\n[The command has no new output after {self.NO_CHANGE_TIMEOUT_SECONDS} seconds. '
            "You may wait longer to see additional output by sending empty command '', "
            'send other commands to interact with the current process, '
            'or send keys to interrupt/kill the command.]'
        )
        return CmdOutputObservation(
            content=command_output,
            command=command,
            metadata=CmdOutputMetadata(),  # No metadata available
        )

    def _handle_hard_timeout_command(
        self, command: str, timeout: float
    ) -> CmdOutputObservation:
        self.prev_status = BashCommandStatus.HARD_TIMEOUT
        full_output = self._get_pane_content(full=True)
        ps1_matches = CmdOutputMetadata.matches_ps1_metadata(full_output)
        assert len(ps1_matches) == 1, 'Expected exactly one PS1 metadata block'

        command_output = full_output[ps1_matches[0].end() + 1 :]
        if self.prev_output:
            _clean_command_output = command_output.removeprefix(self.prev_output)
            command_output = (
                '[Command output continued from previous command]\n'
                + _clean_command_output
            )
            self.prev_output = _clean_command_output

        command_output = command_output.lstrip().removeprefix(command.lstrip()).lstrip()
        command_output += (
            f'\n[The command timed out after {timeout} seconds. '
            "You may wait longer to see additional output by sending empty command '', "
            'send other commands to interact with the current process, '
            'or send keys to interrupt/kill the command.]'
        )

        return CmdOutputObservation(
            command=command,
            content=command_output,
            metadata=CmdOutputMetadata(),  # No metadata available
        )

    def _handle_empty_command(self) -> CmdOutputObservation:
        if self.prev_status not in {
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

        self.prev_status = BashCommandStatus.CONTINUE
        full_output = self._get_pane_content(full=True)

        ps1_matches = CmdOutputMetadata.matches_ps1_metadata(full_output)
        assert len(ps1_matches) == 1, 'Expected exactly one PS1 metadata block'

        command_output = full_output[ps1_matches[0].end() + 1 :]
        # remove the previous command output from the new output if any
        if self.prev_output:
            _clean_command_output = command_output.removeprefix(self.prev_output)
            command_output = (
                '[Command output continued from previous command]\n'
                + _clean_command_output
            )
            self.prev_output = _clean_command_output

        return CmdOutputObservation(
            content=command_output,
            command='',
            metadata=CmdOutputMetadata(),
        )

    def execute(self, action: CmdRunAction) -> CmdOutputObservation:
        """Execute a command in the bash session."""
        if action.command.strip() == '':
            return self._handle_empty_command()

        # Clear screen before executing new command
        if self.prev_status not in {
            BashCommandStatus.NO_CHANGE_TIMEOUT,
            BashCommandStatus.HARD_TIMEOUT,
            BashCommandStatus.CONTINUE,
        }:
            self._clear_screen()

        start_time = time.time()
        last_change_time = start_time
        last_pane_output = self._get_pane_content()

        assert (
            len(CmdOutputMetadata.matches_ps1_metadata(last_pane_output)) == 1
        ), 'Expected exactly one PS1 metadata block BEFORE the execution of a command'
        self.pane.send_keys(action.command)

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
