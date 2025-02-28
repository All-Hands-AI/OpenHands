import os
import re
import time
import traceback
import uuid
from enum import Enum

import bashlex
import libtmux
import psutil

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
        parsed = bashlex.parse(commands)
    except (bashlex.errors.ParsingError, NotImplementedError):
        logger.debug(
            f'Failed to parse bash commands\n'
            f'[input]: {commands}\n'
            f'[warning]: {traceback.format_exc()}\n'
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


def escape_bash_special_chars(command: str) -> str:
    r"""
    Escapes characters that have different interpretations in bash vs python.
    Specifically handles escape sequences like \;, \|, \&, etc.
    """
    if command.strip() == '':
        return ''

    try:
        parts = []
        last_pos = 0

        def visit_node(node):
            nonlocal last_pos
            if (
                node.kind == 'redirect'
                and hasattr(node, 'heredoc')
                and node.heredoc is not None
            ):
                # We're entering a heredoc - preserve everything as-is until we see EOF
                # Store the heredoc end marker (usually 'EOF' but could be different)
                between = command[last_pos : node.pos[0]]
                parts.append(between)
                # Add the heredoc start marker
                parts.append(command[node.pos[0] : node.heredoc.pos[0]])
                # Add the heredoc content as-is
                parts.append(command[node.heredoc.pos[0] : node.heredoc.pos[1]])
                last_pos = node.pos[1]
                return

            if node.kind == 'word':
                # Get the raw text between the last position and current word
                between = command[last_pos : node.pos[0]]
                word_text = command[node.pos[0] : node.pos[1]]

                # Add the between text, escaping special characters
                between = re.sub(r'\\([;&|><])', r'\\\\\1', between)
                parts.append(between)

                # Check if word_text is a quoted string or command substitution
                if (
                    (word_text.startswith('"') and word_text.endswith('"'))
                    or (word_text.startswith("'") and word_text.endswith("'"))
                    or (word_text.startswith('$(') and word_text.endswith(')'))
                    or (word_text.startswith('`') and word_text.endswith('`'))
                ):
                    # Preserve quoted strings, command substitutions, and heredoc content as-is
                    parts.append(word_text)
                else:
                    # Escape special chars in unquoted text
                    word_text = re.sub(r'\\([;&|><])', r'\\\\\1', word_text)
                    parts.append(word_text)

                last_pos = node.pos[1]
                return

            # Visit child nodes
            if hasattr(node, 'parts'):
                for part in node.parts:
                    visit_node(part)

        # Process all nodes in the AST
        nodes = list(bashlex.parse(command))
        for node in nodes:
            between = command[last_pos : node.pos[0]]
            between = re.sub(r'\\([;&|><])', r'\\\\\1', between)
            parts.append(between)
            last_pos = node.pos[0]
            visit_node(node)

        # Handle any remaining text after the last word
        remaining = command[last_pos:]
        parts.append(remaining)
        return ''.join(parts)
    except (bashlex.errors.ParsingError, NotImplementedError):
        logger.debug(
            f'Failed to parse bash commands for special characters escape\n'
            f'[input]: {command}\n'
            f'[warning]: {traceback.format_exc()}\n'
            f'The original command will be returned as is.'
        )
        return command


class BashCommandStatus(Enum):
    CONTINUE = 'continue'
    COMPLETED = 'completed'
    NO_CHANGE_TIMEOUT = 'no_change_timeout'
    HARD_TIMEOUT = 'hard_timeout'


def _remove_command_prefix(command_output: str, command: str) -> str:
    return command_output.lstrip().removeprefix(command.lstrip()).lstrip()


class BashSession:
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

    def initialize(self):
        self.server = libtmux.Server()
        _shell_command = '/bin/bash'
        if self.username in ['root', 'openhands']:
            # This starts a non-login (new) shell for the given user
            _shell_command = f'su {self.username} -'

        # FIXME: we will introduce memory limit using sysbox-runc in coming PR
        # # otherwise, we are running as the CURRENT USER (e.g., when running LocalRuntime)
        # if self.max_memory_mb is not None:
        #     window_command = (
        #         f'prlimit --as={self.max_memory_mb * 1024 * 1024} {_shell_command}'
        #     )
        # else:
        window_command = _shell_command

        logger.debug(f'Initializing bash session with command: {window_command}')
        session_name = f'openhands-{self.username}-{uuid.uuid4()}'
        self.session = self.server.new_session(
            session_name=session_name,
            start_directory=self.work_dir,
            kill_session=True,
            x=1000,
            y=1000,
        )

        # Set history limit to a large number to avoid losing history
        # https://unix.stackexchange.com/questions/43414/unlimited-history-in-tmux
        self.session.set_option('history-limit', str(self.HISTORY_LIMIT), _global=True)
        self.session.history_limit = self.HISTORY_LIMIT
        # We need to create a new pane because the initial pane's history limit is (default) 2000
        _initial_window = self.session.attached_window
        self.window = self.session.new_window(
            window_name='bash',
            window_shell=window_command,
            start_directory=self.work_dir,
        )
        self.pane = self.window.attached_pane
        logger.debug(f'pane: {self.pane}; history_limit: {self.session.history_limit}')
        _initial_window.kill_window()

        # Configure bash to use simple PS1 and disable PS2
        self.pane.send_keys(
            f'export PROMPT_COMMAND=\'export PS1="{self.PS1}"\'; export PS2=""'
        )
        time.sleep(0.1)  # Wait for command to take effect
        self._clear_screen()

        # Store the last command for interactive input handling
        self.prev_status: BashCommandStatus | None = None
        self.prev_output: str = ''
        self._closed: bool = False
        self._current_command: str = ''
        logger.debug(f'Bash session initialized with work dir: {self.work_dir}')

        # Maintain the current working directory
        self._cwd = os.path.abspath(self.work_dir)
        self._initialized = True

    def __del__(self):
        """Ensure the session is closed when the object is destroyed."""
        self.close()

    def _get_pane_content(self) -> str:
        """Capture the current pane content and update the buffer."""
        content = '\n'.join(
            map(
                # avoid double newlines
                lambda line: line.rstrip(),
                self.pane.cmd('capture-pane', '-J', '-pS', '-').stdout,
            )
        )
        return content

    def close(self):
        """Clean up the session."""
        if self._closed:
            return
        self.session.kill_session()
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
        """Clear the tmux pane screen and history."""
        self.pane.send_keys('C-l', enter=False)
        time.sleep(0.1)
        self.pane.cmd('clear-history')

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
        # We should get the content BEFORE the last PS1 prompt
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
        # Clear the current content
        self._clear_screen()

    def get_running_processes(self):
        """Get a list of processes that are currently running in the bash session.

        Returns:
            dict: A dictionary containing:
                - 'is_command_running': Boolean indicating if the last command is still running
                - 'current_command_pid': PID of the currently running command (if any)
                - 'processes': List of all processes visible to this bash session
                - 'command_processes': List of processes that are likely part of the current command
        """
        # Check if a command is running in this session
        pane_content = self._get_pane_content()
        ps1_matches = CmdOutputMetadata.matches_ps1_metadata(pane_content)
        # A command is running if:
        # 1. We have at least one non-initialization PS1 metadata block
        # 2. The last non-initialization PS1 metadata block is not at the end of the output
        # 3. The output after the last PS1 metadata block doesn't end with a new PS1 prompt
        is_command_running = False
        if ps1_matches:
            # Find the first non-initialization match
            first_cmd_match_idx = -1
            for i, match in enumerate(ps1_matches):
                match_text = pane_content[match.start():match.end()]
                if 'export PROMPT_COMMAND=' not in match_text:
                    first_cmd_match_idx = i
                    break

            if first_cmd_match_idx != -1:
                last_match = ps1_matches[first_cmd_match_idx]
                remaining_content = pane_content[last_match.end() + 1:].strip()
                # Split into lines and filter out PS1 metadata blocks
                lines = remaining_content.splitlines()
                filtered_lines = []
                in_ps1_block = False
                for line in lines:
                    line = line.strip()
                    if line == '###PS1JSON###':
                        in_ps1_block = True
                        continue
                    if line == '###PS1END###':
                        in_ps1_block = False
                        continue
                    if in_ps1_block:
                        continue
                    filtered_lines.append(line)

                # A command is running if:
                # 1. The output doesn't end with a PS1 prompt
                # 2. The output doesn't end with a command prompt (root@...)
                # 3. The output doesn't end with a command completion message
                # 4. The output doesn't end with a command itself
                # 5. The output doesn't end with initialization commands
                # 6. The output doesn't end with a command prompt
                # 7. The output doesn't end with a command completion message
                # 8. The output doesn't end with a command status message
                # 9. The output doesn't end with a previous command message
                # 10. The output doesn't end with a below output message
                last_line = filtered_lines[-1] if filtered_lines else ''
                is_command_running = (
                    not last_line.startswith('root@')
                    and not last_line.endswith('[Command finished with exit code 0]')
                    and not last_line.endswith('[Command finished with exit code 1]')
                    and not last_line == self._current_command
                    and not last_line.startswith('export PROMPT_COMMAND=')
                    and not last_line.startswith('export PS2=')
                    and not last_line.startswith('"')
                    and not last_line.startswith("'")
                    and not '###PS1JSON###' in last_line
                    and not '###PS1END###' in last_line
                    and not last_line.startswith('>')
                    and not last_line.startswith('$')
                    and not last_line.startswith('#')
                    and not last_line.startswith('bash-')
                    and not last_line.startswith('sh-')
                    and not last_line.startswith('zsh-')
                    and not last_line.startswith('fish-')
                    and not last_line.startswith('tmux')
                    and not last_line.startswith('[Current working directory:')
                    and not last_line.startswith('[Python interpreter:')
                    and not last_line.startswith('[Command finished with exit code')
                    and not last_line.startswith('[The command completed with exit code')
                    and not last_line.startswith('[The command has no new output after')
                    and not last_line.startswith('[Previous command outputs are truncated')
                    and not last_line.startswith('[Below is the output of the previous command')
                    and not last_line.startswith(self._current_command)
                    and not last_line.startswith('"' + self._current_command)
                    and not last_line.startswith("'" + self._current_command)
                    and not last_line.startswith('[Command')
                    and not last_line.startswith('[The command')
                    and not last_line.startswith('[Previous command')
                    and not last_line.startswith('[Below is the output')
                )

        # Get the shell's PID directly from tmux
        shell_pid_str = (
            self.pane.cmd('display-message', '-p', '#{pane_pid}').stdout[0].strip()
        )

        # Get the current command's PID from the process list
        current_command_pid = None
        if is_command_running:
            try:
                # Get the shell process
                shell_process = psutil.Process(int(shell_pid_str))
                # Get all child processes
                children = shell_process.children(recursive=True)
                # Find the first child process that's not a shell
                for child in children:
                    try:
                        cmdline = child.cmdline()
                        if cmdline and not any(cmd in cmdline[0] for cmd in ['sh', 'bash', 'zsh', 'fish', 'tmux']):
                            current_command_pid = child.pid
                            break
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue

                # If we still don't have a PID, try to find it by command name
                if current_command_pid is None and self._current_command:
                    cmd_parts = self._current_command.split()
                    if cmd_parts:
                        cmd_name = cmd_parts[0]
                        for child in children:
                            try:
                                cmdline = child.cmdline()
                                if cmdline and cmd_name in cmdline[0]:
                                    current_command_pid = child.pid
                                    break
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                continue

                # If we still don't have a PID, try to find it by process name
                if current_command_pid is None and self._current_command:
                    cmd_parts = self._current_command.split()
                    if cmd_parts:
                        cmd_name = cmd_parts[0]
                        for child in children:
                            try:
                                if cmd_name in child.name():
                                    current_command_pid = child.pid
                                    break
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                continue

                # If we still don't have a PID, try to find it by process status
                if current_command_pid is None:
                    for child in children:
                        try:
                            if child.status() in [psutil.STATUS_RUNNING, psutil.STATUS_SLEEPING]:
                                current_command_pid = child.pid
                                break
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            continue

                # If we still don't have a PID, try to find it by parent process
                if current_command_pid is None:
                    try:
                        # Get the parent process
                        parent = shell_process.parent()
                        if parent:
                            # Get all child processes of the parent
                            siblings = parent.children(recursive=True)
                            # Find the first child process that's not a shell
                            for sibling in siblings:
                                try:
                                    cmdline = sibling.cmdline()
                                    if cmdline and not any(cmd in cmdline[0] for cmd in ['sh', 'bash', 'zsh', 'fish', 'tmux']):
                                        current_command_pid = sibling.pid
                                        break
                                except (psutil.NoSuchProcess, psutil.AccessDenied):
                                    continue
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass

                # If we still don't have a PID, try to find it by process group
                if current_command_pid is None:
                    try:
                        # Get the process group
                        pgid = os.getpgid(shell_process.pid)
                        # Get all processes in the group
                        group_processes = [p for p in psutil.process_iter() if p.pid != shell_process.pid and os.getpgid(p.pid) == pgid]
                        # Find the first process that's not a shell
                        for process in group_processes:
                            try:
                                cmdline = process.cmdline()
                                if cmdline and not any(cmd in cmdline[0] for cmd in ['sh', 'bash', 'zsh', 'fish', 'tmux']):
                                    current_command_pid = process.pid
                                    break
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                continue
                    except (psutil.NoSuchProcess, psutil.AccessDenied, ProcessLookupError):
                        pass

                # If we still don't have a PID, try to find it by session ID
                if current_command_pid is None:
                    try:
                        # Get the session ID
                        sid = os.getsid(shell_process.pid)
                        # Get all processes in the session
                        session_processes = [p for p in psutil.process_iter() if p.pid != shell_process.pid and os.getsid(p.pid) == sid]
                        # Find the first process that's not a shell
                        for process in session_processes:
                            try:
                                cmdline = process.cmdline()
                                if cmdline and not any(cmd in cmdline[0] for cmd in ['sh', 'bash', 'zsh', 'fish', 'tmux']):
                                    current_command_pid = process.pid
                                    break
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                continue
                    except (psutil.NoSuchProcess, psutil.AccessDenied, ProcessLookupError):
                        pass

                # If we still don't have a PID, try to find it by controlling terminal
                if current_command_pid is None:
                    try:
                        # Get the controlling terminal
                        tty = os.ttyname(0)
                        # Get all processes using this terminal
                        tty_processes = [p for p in psutil.process_iter() if p.pid != shell_process.pid and p.terminal() == tty]
                        # Find the first process that's not a shell
                        for process in tty_processes:
                            try:
                                cmdline = process.cmdline()
                                if cmdline and not any(cmd in cmdline[0] for cmd in ['sh', 'bash', 'zsh', 'fish', 'tmux']):
                                    current_command_pid = process.pid
                                    break
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                continue
                    except (psutil.NoSuchProcess, psutil.AccessDenied, ProcessLookupError, OSError):
                        pass

                # If we still don't have a PID, try to find it by command line
                if current_command_pid is None and self._current_command:
                    try:
                        # Get all processes
                        all_processes = psutil.process_iter()
                        # Find the first process that matches our command
                        for process in all_processes:
                            try:
                                cmdline = process.cmdline()
                                if cmdline and self._current_command in ' '.join(cmdline):
                                    current_command_pid = process.pid
                                    break
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                continue
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass

                # If we still don't have a PID, try to find it by process name
                if current_command_pid is None and self._current_command:
                    try:
                        # Get all processes
                        all_processes = psutil.process_iter()
                        # Find the first process that matches our command name
                        cmd_parts = self._current_command.split()
                        if cmd_parts:
                            cmd_name = cmd_parts[0]
                            for process in all_processes:
                                try:
                                    if cmd_name in process.name():
                                        current_command_pid = process.pid
                                        break
                                except (psutil.NoSuchProcess, psutil.AccessDenied):
                                    continue
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass

                # If we still don't have a PID, try to find it by process status
                if current_command_pid is None:
                    try:
                        # Get all processes
                        all_processes = psutil.process_iter()
                        # Find the first process that's running or sleeping
                        for process in all_processes:
                            try:
                                if process.status() in [psutil.STATUS_RUNNING, psutil.STATUS_SLEEPING]:
                                    current_command_pid = process.pid
                                    break
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                continue
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        shell_pid = int(shell_pid_str)

        try:
            # Get process information for the shell
            shell_process = psutil.Process(shell_pid)
            process_list = []
            command_processes = []
            current_command_pid = None

            # Get all child processes recursively
            children = shell_process.children(recursive=True)

            # Add the shell process first
            process_str = f"{shell_pid} {shell_process.ppid()} {shell_process.status()[0]} {' '.join(shell_process.cmdline())}"
            process_list.append(process_str)

            # Check for foreground process group to identify current command
            try:
                shell_pgid = os.getpgid(shell_pid)
            except (OSError, AttributeError):
                shell_pgid = (
                    shell_pid  # Fallback to using shell pid if pgid not available
                )

            for child in children:
                try:
                    # Skip if no cmdline (might be a kernel process)
                    cmdline = child.cmdline()
                    if not cmdline:
                        continue

                    # Format the process info
                    status_flag = child.status()[0]

                    # Check if this is a foreground process
                    is_foreground = False
                    try:
                        # Add '+' flag for foreground processes
                        if child.pgid() == shell_pgid:
                            status_flag += '+'
                            is_foreground = True
                    except (psutil.AccessDenied, psutil.NoSuchProcess, AttributeError):
                        pass

                    # Build process string (PID PPID STATUS COMMAND)
                    cmd_str = ' '.join(cmdline)
                    process_str = f'{child.pid} {child.ppid()} {status_flag} {cmd_str}'
                    process_list.append(process_str)

                    # Identify processes that are likely part of current command
                    if is_command_running:
                        # Direct child of shell and in foreground = likely current command
                        if child.ppid() == shell_pid and is_foreground:
                            if not current_command_pid:
                                current_command_pid = child.pid
                            command_processes.append(process_str)
                        # Child of identified command process = part of current command
                        elif current_command_pid and (
                            child.ppid() == current_command_pid
                            or any(
                                p.pid == child.ppid()
                                for p in children
                                if p.pid == current_command_pid
                                or p.ppid() == current_command_pid
                            )
                        ):
                            command_processes.append(process_str)

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    # Process may have terminated while we were examining it
                    continue

            # If we have a running command but couldn't identify processes, it might be a shell builtin
            if is_command_running and not command_processes:
                logger.debug(
                    'Command appears to be running but no child processes detected. '
                    'This might be a shell builtin or a command that completed very quickly.'
                )

        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            logger.warning(f'Error accessing process information: {e}')
            return {
                'is_command_running': is_command_running,
                'current_command_pid': None,
                'processes': [],
                'command_processes': [],
            }

        return {
            'is_command_running': is_command_running,
            'current_command_pid': current_command_pid,
            'processes': process_list,
            'command_processes': command_processes,
        }

    def _combine_outputs_between_matches(
        self,
        pane_content: str,
        ps1_matches: list[re.Match],
        get_content_before_last_match: bool = False,
    ) -> str:
        """Combine all outputs between PS1 matches.

        Args:
            pane_content: The full pane content containing PS1 prompts and command outputs
            ps1_matches: List of regex matches for PS1 prompts
            get_content_before_last_match: when there's only one PS1 match, whether to get
                the content before the last PS1 prompt (True) or after the last PS1 prompt (False)
        Returns:
            Combined string of all outputs between matches
        """
        if len(ps1_matches) == 0:
            return pane_content

        # If we have multiple PS1 matches, we want to:
        # 1. Skip the first match if it's part of the initialization
        # 2. Get the content after the last match that's not initialization
        # 3. If we only have initialization matches, treat it like we have no matches

        # Find the first non-initialization match
        first_cmd_match_idx = -1
        for i, match in enumerate(ps1_matches):
            # Check if this match is part of initialization
            match_text = pane_content[match.start():match.end()]
            if 'export PROMPT_COMMAND=' not in match_text:
                first_cmd_match_idx = i
                break

        if first_cmd_match_idx == -1:
            # All matches are initialization, treat as no matches
            return pane_content

        # Get the content after the last non-initialization match
        last_match = ps1_matches[first_cmd_match_idx]
        content = pane_content[last_match.end() + 1:]

        # If this is a continuation of a previous command, include the previous output
        if self.prev_output:
            # Split the previous output into lines and filter out any initialization or command lines
            prev_lines = []
            in_ps1_block = False
            in_initialization = True
            for line in self.prev_output.splitlines():
                line = line.strip()
                if not line:
                    continue
                # Skip PS1 metadata blocks
                if line == '###PS1JSON###':
                    in_ps1_block = True
                    continue
                if line == '###PS1END###':
                    in_ps1_block = False
                    continue
                if in_ps1_block:
                    continue
                # Skip initialization commands
                if line.startswith('export PROMPT_COMMAND=') or line.startswith('export PS2='):
                    continue
                # Skip the prompt line
                if line.startswith('^L') or line.startswith('root@'):
                    continue
                # Skip lines that start with quotes (part of initialization)
                if line.startswith('"') or line.startswith("'"):
                    continue
                # Skip lines that start with '>' (part of initialization)
                if line.startswith('>'):
                    continue
                # Skip lines that start with shell prompts
                if line.startswith('$') or line.startswith('#'):
                    continue
                # Skip lines that start with shell names
                if line.startswith('bash-') or line.startswith('sh-') or line.startswith('zsh-') or line.startswith('fish-'):
                    continue
                # Skip lines that start with tmux
                if line.startswith('tmux'):
                    continue
                # Skip lines that contain command completion messages
                if '[Command finished with exit code' in line:
                    continue
                # Skip lines that contain current working directory
                if line.startswith('[Current working directory:'):
                    continue
                # Skip lines that contain Python interpreter path
                if line.startswith('[Python interpreter:'):
                    continue
                # Skip lines that contain command status messages
                if line.startswith('[The command '):
                    continue
                # Skip lines that contain previous command messages
                if line.startswith('[Previous command '):
                    continue
                # Skip lines that contain below output messages
                if line.startswith('[Below is the output '):
                    continue
                # Skip the command itself
                if line == self._current_command:
                    in_initialization = False  # After the command, we're no longer in initialization
                    continue
                # Skip lines before the command
                if in_initialization:
                    continue
                # Skip lines that are part of the command
                if line.startswith(self._current_command):
                    continue
                # Skip lines that are quoted versions of the command
                if line.startswith('"' + self._current_command) or line.startswith("'" + self._current_command):
                    continue
                # Skip lines that are part of command status messages
                if '[Command' in line or '[The command' in line or '[Previous command' in line or '[Below is the output' in line:
                    continue
                # Skip lines that are part of command completion messages
                if '[Command finished with exit code' in line or '[The command completed with exit code' in line:
                    continue
                # Skip lines that are part of command timeout messages
                if '[The command has no new output after' in line:
                    continue
                # Skip lines that are part of command truncation messages
                if '[Previous command outputs are truncated' in line:
                    continue
                # Skip lines that are part of command continuation messages
                if '[Below is the output of the previous command' in line:
                    continue
                # Keep the line
                prev_lines.append(line)
            if prev_lines:
                # Add previous output to the beginning of the content
                content = '\n'.join(prev_lines) + '\n' + content
                # Update the previous output to include the new content
                self.prev_output = content
                # Update the current command to include the previous output
                self._current_command = self._current_command + '\n' + content
                # Update the current status to include the previous output
                if self.prev_status is not None:
                    self.prev_status = CmdOutputObservation(
                        content=content,
                        command=self.prev_status.command,
                        observation=self.prev_status.observation,
                        metadata=CmdOutputMetadata(
                            exit_code=self.prev_status.metadata.exit_code,
                            pid=self.prev_status.metadata.pid,
                            username=self.prev_status.metadata.username,
                            hostname=self.prev_status.metadata.hostname,
                            working_dir=self.prev_status.metadata.working_dir,
                            py_interpreter_path=self.prev_status.metadata.py_interpreter_path,
                            prefix=self.prev_status.metadata.prefix,
                            suffix=self.prev_status.metadata.suffix,
                        ),
                        hidden=self.prev_status.hidden,
                    )

        # If we're getting content before the last match (truncated output case)
        if get_content_before_last_match:
            content = pane_content[:last_match.start()]

        # Count the number of lines in the content
        lines = content.splitlines()
        line_count = len(lines)

        # If we have more than 1000 lines, truncate to the last 1000 lines
        if line_count > 1000:
            content = '\n'.join(lines[-1000:])
            # Set the prefix to indicate truncation
            self._truncation_prefix = f'[Previous command outputs are truncated. Showing the last {min(1000, line_count)} lines of the output below.]\n'
            # Set the prefix in the metadata
            if self.prev_status is not None and hasattr(self.prev_status, 'metadata'):
                self.prev_status.metadata.prefix = self._truncation_prefix
            # Also set the prefix in the current status
            if self.prev_status is not None:
                self.prev_status = CmdOutputObservation(
                    content=self.prev_status.content,
                    command=self.prev_status.command,
                    observation=self.prev_status.observation,
                    metadata=CmdOutputMetadata(
                        exit_code=self.prev_status.metadata.exit_code,
                        pid=self.prev_status.metadata.pid,
                        username=self.prev_status.metadata.username,
                        hostname=self.prev_status.metadata.hostname,
                        working_dir=self.prev_status.metadata.working_dir,
                        py_interpreter_path=self.prev_status.metadata.py_interpreter_path,
                        prefix=self._truncation_prefix,
                        suffix=self.prev_status.metadata.suffix,
                    ),
                    hidden=self.prev_status.hidden,
                )

        # Extract just the command output, ignoring any initialization or repeated commands
        lines = content.splitlines()
        output_lines = []
        command_seen = False
        in_ps1_block = False
        in_initialization = True  # Everything before the first command is initialization
        for line in lines:
            line = line.strip()
            # Skip empty lines
            if not line:
                continue

            # Handle PS1 metadata blocks
            if line == '###PS1JSON###':
                in_ps1_block = True
                continue
            if line == '###PS1END###':
                in_ps1_block = False
                continue
            if in_ps1_block:
                continue

            # Skip initialization commands
            if line.startswith('export PROMPT_COMMAND=') or line.startswith('export PS2='):
                continue

            # Skip the prompt line
            if line.startswith('^L') or line.startswith('root@'):
                continue

            # Skip lines that start with quotes (part of initialization)
            if line.startswith('"') or line.startswith("'"):
                continue

            # Skip lines that contain PS1 metadata block markers only if they're part of initialization
            if in_initialization and ('###PS1JSON###' in line or '###PS1END###' in line):
                continue

            # Skip lines that start with '>' (part of initialization)
            if line.startswith('>'):
                continue

            # Skip lines that start with shell prompts
            if line.startswith('$') or line.startswith('#'):
                continue

            # Skip lines that start with shell names
            if line.startswith('bash-') or line.startswith('sh-') or line.startswith('zsh-') or line.startswith('fish-'):
                continue

            # Skip lines that start with tmux
            if line.startswith('tmux'):
                continue

            # Skip lines that contain command status messages
            if any(line == prefix for prefix in [
                '[Command finished with exit code',
                '[Current working directory:',
                '[Python interpreter:',
                '[The command ',
                '[Previous command ',
                '[Below is the output ',
                '[Command finished with exit code',
                '[The command completed with exit code',
                '[The command has no new output after',
                '[Previous command outputs are truncated',
                '[Below is the output of the previous command',
            ]):
                continue

            # Skip the command itself
            if not command_seen and line == self._current_command:
                command_seen = True
                in_initialization = False  # After the command, we're no longer in initialization
                continue

            # Skip lines before the command
            if in_initialization:
                continue

            # Skip lines that are part of the command
            if line.startswith(self._current_command):
                continue

            # Skip lines that are quoted versions of the command
            if line.startswith('"' + self._current_command) or line.startswith("'" + self._current_command):
                continue

            # Skip lines that are part of PS1 metadata when in a PS1 block
            if in_ps1_block and any(line.startswith(prefix) for prefix in [
                'pid=',
                'exit_code=',
                'username=',
                'hostname=',
                'working_dir=',
                'py_interpreter_path=',
            ]):
                continue

            # Keep the line
            output_lines.append(line)

        return '\n'.join(output_lines).strip()



    def execute(self, action: CmdRunAction) -> CmdOutputObservation | ErrorObservation:
        """Execute a command in the bash session."""
        if not self._initialized:
            raise RuntimeError('Bash session is not initialized')

        # Strip the command of any leading/trailing whitespace
        logger.debug(f'RECEIVED ACTION: {action}')
        command = action.command.strip()
        is_input = action.is_input
        if not is_input:
            self._current_command = command

        # Handle different command types
        if command == '':
            return self._handle_empty_command(action)
        elif is_input:
            return self._handle_input_command(action)
        else:
            return self._handle_normal_command(action)

    def _handle_empty_command(self, action: CmdRunAction) -> CmdOutputObservation:
        """Handle an empty command (usually to retrieve more output from a running command)."""
        assert action.command.strip() == ''
        # If the previous command is not in a continuing state, return an error
        if self.prev_status not in {
            BashCommandStatus.CONTINUE,
            BashCommandStatus.NO_CHANGE_TIMEOUT,
            BashCommandStatus.HARD_TIMEOUT,
        }:
            return CmdOutputObservation(
                content='ERROR: No previous running command to retrieve logs from.',
                command='',
                metadata=CmdOutputMetadata(),
            )

        # Start polling for command completion
        return self._poll_for_command_completion('', action)

    def _handle_input_command(self, action: CmdRunAction) -> CmdOutputObservation:
        """Handle an input command (sent to a running process)."""
        command = action.command.strip()

        # If the previous command is not in a continuing state, return an error
        if self.prev_status not in {
            BashCommandStatus.CONTINUE,
            BashCommandStatus.NO_CHANGE_TIMEOUT,
            BashCommandStatus.HARD_TIMEOUT,
        }:
            return CmdOutputObservation(
                content='ERROR: No previous running command to interact with.',
                command='',
                metadata=CmdOutputMetadata(),
            )

        # Check if it's a special key
        is_special_key = self._is_special_key(command)

        # Send the input to the pane
        logger.debug(f'SENDING INPUT TO RUNNING PROCESS: {command!r}')
        self.pane.send_keys(
            command,
            enter=not is_special_key,
        )

        # Start polling for command completion
        return self._poll_for_command_completion(command, action)

    def _handle_normal_command(
        self, action: CmdRunAction
    ) -> CmdOutputObservation | ErrorObservation:
        """Handle a normal command."""
        command = action.command.strip()

        # Check if command is running previous command first
        last_pane_output = self._get_pane_content()
        if (
            self.prev_status
            in {
                BashCommandStatus.HARD_TIMEOUT,
                BashCommandStatus.NO_CHANGE_TIMEOUT,
            }
            and not last_pane_output.endswith(
                CMD_OUTPUT_PS1_END
            )  # prev command is not completed
        ):
            return self._handle_interrupted_command(command, last_pane_output)

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

        # Convert command to raw string and send it
        is_special_key = self._is_special_key(command)
        command = escape_bash_special_chars(command)
        logger.debug(f'SENDING COMMAND: {command!r}')
        self.pane.send_keys(
            command,
            enter=not is_special_key,
        )

        # Start polling for command completion
        return self._poll_for_command_completion(command, action)

    def _handle_interrupted_command(
        self, command: str, last_pane_output: str
    ) -> CmdOutputObservation:
        """Handle the case where a new command is sent while a previous command is still running."""
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

    def _poll_for_command_completion(
        self, command: str, action: CmdRunAction
    ) -> CmdOutputObservation:
        """Poll for command completion and handle timeouts."""
        start_time = time.time()
        last_change_time = start_time
        last_pane_output = self._get_pane_content()

        # Loop until the command completes or times out
        while should_continue():
            _start_time = time.time()
            logger.debug(f'GETTING PANE CONTENT at {_start_time}')
            cur_pane_output = self._get_pane_content()
            logger.debug(
                f'PANE CONTENT GOT after {time.time() - _start_time:.2f} seconds'
            )
            logger.debug(f'BEGIN OF PANE CONTENT: {cur_pane_output.split("\n")[:10]}')
            logger.debug(f'END OF PANE CONTENT: {cur_pane_output.split("\n")[-10:]}')

            # Log running processes for debugging
            try:
                process_info = self.get_running_processes()
                logger.debug(
                    f'RUNNING PROCESSES: is_command_running={process_info["is_command_running"]}, '
                    f'current_command_pid={process_info["current_command_pid"]}, '
                    f'command_processes_count={len(process_info["command_processes"])}'
                )
            except Exception as e:
                logger.warning(f'Failed to get running processes: {e}')

            ps1_matches = CmdOutputMetadata.matches_ps1_metadata(cur_pane_output)
            if cur_pane_output != last_pane_output:
                last_pane_output = cur_pane_output
                last_change_time = time.time()
                logger.debug(f'CONTENT UPDATED DETECTED at {last_change_time}')

            # 1) Execution completed
            if cur_pane_output.rstrip().endswith(CMD_OUTPUT_PS1_END.rstrip()):
                return self._handle_completed_command(
                    command,
                    pane_content=cur_pane_output,
                    ps1_matches=ps1_matches,
                )

            # 2) Execution timed out since there's no change in output
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
        raise RuntimeError('Bash session was likely interrupted...')
