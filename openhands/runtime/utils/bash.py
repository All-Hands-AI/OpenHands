"""Bash session management."""

import contextlib
import os
import pty
import select
import signal
import subprocess
import threading
import time
from typing import TYPE_CHECKING, Optional, Set

if TYPE_CHECKING:
    from openhands.events.action import CmdRunAction

from openhands.events.observation import CmdOutputMetadata, CmdOutputObservation
from openhands.runtime.utils.process import get_process_info


class BashSession:
    """A class to manage a bash session."""

    def __init__(
        self,
        work_dir: str,
        no_change_timeout_seconds: float = 30.0,
        max_output_lines: int = 1000,
    ) -> None:
        """Initialize the bash session.

        Args:
            work_dir: The working directory for the bash session.
            no_change_timeout_seconds: The timeout in seconds for no output change.
            max_output_lines: The maximum number of output lines to keep.
        """
        self.work_dir = work_dir
        self.no_change_timeout_seconds = no_change_timeout_seconds
        self.max_output_lines = max_output_lines
        self.master_fd: Optional[int] = None
        self.slave_fd: Optional[int] = None
        self.process: Optional[subprocess.Popen] = None
        self.current_command: Optional[str] = None
        self.current_pid: Optional[int] = None
        self.is_foreground_running = False
        self.lock = threading.Lock()

    def initialize(self) -> None:
        """Initialize the bash session."""
        if not os.path.exists(self.work_dir):
            os.makedirs(self.work_dir)

        self.master_fd, self.slave_fd = pty.openpty()
        self.process = subprocess.Popen(
            ['bash'],
            stdin=self.slave_fd,
            stdout=self.slave_fd,
            stderr=self.slave_fd,
            cwd=self.work_dir,
            preexec_fn=os.setsid,
        )

    def close(self) -> None:
        """Close the bash session."""
        if self.process:
            try:
                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                # Give it a chance to terminate gracefully
                for _ in range(10):
                    if self.process.poll() is not None:
                        break
                    time.sleep(0.1)
                # If still running, force kill
                if self.process.poll() is None:
                    os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
            except ProcessLookupError:
                pass
            self.process.wait()
            self.process = None

        if self.master_fd is not None:
            with contextlib.suppress(OSError):
                os.close(self.master_fd)
            self.master_fd = None

        if self.slave_fd is not None:
            with contextlib.suppress(OSError):
                os.close(self.slave_fd)
            self.slave_fd = None

    def _read_output(self, timeout: float = 0.1) -> str:
        """Read output from the bash session.

        Args:
            timeout: The timeout in seconds.

        Returns:
            The output from the bash session.
        """
        output = []
        start_time = time.time()
        last_output_time = start_time

        while True:
            if self.master_fd is None:
                break

            try:
                r, _, _ = select.select([self.master_fd], [], [], timeout)
                if not r:
                    current_time = time.time()
                    if (
                        current_time - last_output_time
                        >= self.no_change_timeout_seconds
                    ):
                        break
                    continue

                chunk = os.read(self.master_fd, 1024).decode('utf-8', errors='replace')
                if not chunk:
                    break

                output.append(chunk)
                last_output_time = time.time()

            except OSError:
                break

        return ''.join(output)

    def _get_command_output(
        self,
        command: str,
        raw_output: str,
        metadata: CmdOutputMetadata,
    ) -> str:
        """Process and format command output.

        Args:
            command: The command that was executed.
            raw_output: The raw output from the command.
            metadata: The command output metadata.

        Returns:
            The processed command output.
        """
        lines = raw_output.splitlines()
        if len(lines) > self.max_output_lines:
            lines = lines[-self.max_output_lines :]
            raw_output = '\n'.join(lines)

        return raw_output

    def _get_process_group_pids(self) -> Set[int]:
        """Get the set of PIDs in the current process group.

        Returns:
            A set of PIDs.
        """
        with contextlib.suppress(subprocess.CalledProcessError, ProcessLookupError):
            if self.process:
                pgid = os.getpgid(self.process.pid)
                ps_output = subprocess.check_output(
                    ['ps', '-o', 'pid', '--no-headers', '-g', str(pgid)]
                ).decode()
                return {
                    int(pid.strip()) for pid in ps_output.splitlines() if pid.strip()
                }
        return set()

    def execute(self, action: 'CmdRunAction') -> CmdOutputObservation:
        """Execute a command in the bash session.

        Args:
            action: The command action to execute.

        Returns:
            The command output observation.
        """
        with self.lock:
            command = action.command
            is_input = action.is_input

            if not is_input and self.is_foreground_running:
                metadata = CmdOutputMetadata(
                    exit_code=-1,
                    pid=-1,
                    prefix='',
                    suffix=(
                        '\n[Your command is NOT executed. The previous command is '
                        'still running - You CANNOT send new commands until the '
                        'previous command is completed. By setting `is_input` to '
                        '`true`, you can interact with the current process: You may '
                        'wait longer to see additional output of the previous command '
                        'by sending empty command "", send other commands to '
                        'interact with the current process, or send keys ("C-c", '
                        '"C-z", "C-d") to interrupt/kill the previous command '
                        'before sending your new command.]'
                    ),
                )
                return CmdOutputObservation(
                    content='',
                    command=command,
                    observation='run',
                    metadata=metadata,
                )

            is_special_key = is_input and command.startswith('C-')

            if is_special_key:
                if command == 'C-c':
                    # Send SIGINT to the process group
                    if self.process:
                        try:
                            os.killpg(os.getpgid(self.process.pid), signal.SIGINT)
                            # Wait for the process to terminate
                            for _ in range(10):
                                if self.process.poll() is not None:
                                    break
                                time.sleep(0.1)
                        except ProcessLookupError:
                            pass
                    self.is_foreground_running = False
                    # Return immediately with exit code 130
                    metadata = CmdOutputMetadata(
                        exit_code=130,
                        pid=get_process_info().pid,
                        username=get_process_info().username,
                        hostname=get_process_info().hostname,
                        working_dir=get_process_info().working_dir,
                        py_interpreter_path=get_process_info().py_interpreter_path,
                        suffix=(
                            '\n[The command was interrupted by CTRL+C '
                            '(exit code 130)]'
                        ),
                    )
                    return CmdOutputObservation(
                        content='',
                        command=command,
                        observation='run',
                        metadata=metadata,
                    )
                elif command == 'C-z':
                    # Send SIGTSTP to the process group
                    if self.process:
                        try:
                            os.killpg(os.getpgid(self.process.pid), signal.SIGTSTP)
                            # Wait for the process to stop
                            for _ in range(10):
                                if self.process.poll() is not None:
                                    break
                                time.sleep(0.1)
                        except ProcessLookupError:
                            pass
                    self.is_foreground_running = False
                    # Return immediately with exit code 146 (SIGTSTP + 128)
                    metadata = CmdOutputMetadata(
                        exit_code=146,
                        pid=get_process_info().pid,
                        username=get_process_info().username,
                        hostname=get_process_info().hostname,
                        working_dir=get_process_info().working_dir,
                        py_interpreter_path=get_process_info().py_interpreter_path,
                        suffix=(
                            '\n[The command was stopped by CTRL+Z ' '(exit code 146)]'
                        ),
                    )
                    return CmdOutputObservation(
                        content='',
                        command=command,
                        observation='run',
                        metadata=metadata,
                    )
                elif command == 'C-d':
                    # Send EOF
                    if self.master_fd is not None:
                        os.write(self.master_fd, b'\x04')
                        # Wait for the process to terminate
                        for _ in range(10):
                            if self.process and self.process.poll() is not None:
                                break
                            time.sleep(0.1)
                    self.is_foreground_running = False
                    # Return immediately with exit code 0
                    metadata = CmdOutputMetadata(
                        exit_code=0,
                        pid=get_process_info().pid,
                        username=get_process_info().username,
                        hostname=get_process_info().hostname,
                        working_dir=get_process_info().working_dir,
                        py_interpreter_path=get_process_info().py_interpreter_path,
                        suffix=(
                            '\n[The command was terminated by CTRL+D ' '(exit code 0)]'
                        ),
                    )
                    return CmdOutputObservation(
                        content='',
                        command=command,
                        observation='run',
                        metadata=metadata,
                    )

            # Write the command to the terminal
            if self.master_fd is not None:
                os.write(self.master_fd, (command + '\n').encode())
                # Read initial output
                raw_command_output = self._read_output(timeout=0.5)

                # For non-background commands, check if the command is still running
                if not is_special_key and not is_input:
                    is_background = command.strip().endswith('&')
                    if not is_background:
                        # Try to read more output with a very short timeout
                        try:
                            r, _, _ = select.select([self.master_fd], [], [], 0.1)
                            if r:
                                # If we can read more, the process is still running
                                self.is_foreground_running = True
                                return CmdOutputObservation(
                                    content=raw_command_output,
                                    command=command,
                                    observation='run',
                                    metadata=CmdOutputMetadata(
                                        exit_code=-1,
                                        pid=get_process_info().pid,
                                        username=get_process_info().username,
                                        hostname=get_process_info().hostname,
                                        working_dir=get_process_info().working_dir,
                                        py_interpreter_path=(
                                            get_process_info().py_interpreter_path
                                        ),
                                        suffix='\n[The command is still running]',
                                    ),
                                )
                        except OSError:
                            pass

                        # If we didn't get a prompt back, process is still running
                        if '###PS1END###' not in raw_command_output:
                            self.is_foreground_running = True
                            return CmdOutputObservation(
                                content=raw_command_output,
                                command=command,
                                observation='run',
                                metadata=CmdOutputMetadata(
                                    exit_code=-1,
                                    pid=get_process_info().pid,
                                    username=get_process_info().username,
                                    hostname=get_process_info().hostname,
                                    working_dir=get_process_info().working_dir,
                                    py_interpreter_path=(
                                        get_process_info().py_interpreter_path
                                    ),
                                    suffix='\n[The command is still running]',
                                ),
                            )
                        self.is_foreground_running = False
            else:
                raw_command_output = ''

            # Get process info
            process_info = get_process_info()

            # Determine exit code
            if is_special_key and command == 'C-c':
                exit_code = 130  # Standard Unix exit code for SIGINT
            elif 'command not found' in raw_command_output:
                exit_code = 127
            elif self.is_foreground_running:
                exit_code = -1
            else:
                exit_code = 0

            metadata = CmdOutputMetadata(
                exit_code=exit_code,
                pid=process_info.pid,
                username=process_info.username,
                hostname=process_info.hostname,
                working_dir=process_info.working_dir,
                py_interpreter_path=process_info.py_interpreter_path,
            )

            if self.max_output_lines and raw_command_output:
                num_lines = len(raw_command_output.splitlines())
                metadata.prefix = (
                    '[Previous command outputs are truncated. '
                    f'Showing the last {num_lines} lines of the output below.]\n'
                )

            if is_special_key:
                if command == 'C-c':
                    metadata.suffix = (
                        f'\n[The command was interrupted by CTRL+C '
                        f'(exit code {exit_code})]'
                    )
                else:
                    metadata.suffix = (
                        f'\n[The command completed with exit code {exit_code}. '
                        f'CTRL+{command[-1].upper()} was sent.]'
                    )
            else:
                metadata.suffix = (
                    f'\n[The command completed with exit code {exit_code}.]'
                )

            command_output = self._get_command_output(
                command,
                raw_command_output,
                metadata,
            )

            return CmdOutputObservation(
                content=command_output,
                command=command,
                observation='run',
                metadata=metadata,
            )
