import atexit
import sys
import time

import pexpect
from tenacity import retry, stop_after_attempt, wait_fixed

from opendevin.core.config import config
from opendevin.core.exceptions import SandboxInvalidBackgroundCommandError
from opendevin.core.logger import opendevin_logger as logger
from opendevin.core.schema import CancellableStream
from opendevin.runtime.plugins import AgentSkillsRequirement, JupyterRequirement
from opendevin.runtime.process import Process
from opendevin.runtime.sandbox import Sandbox
from opendevin.runtime.sandbox.stream.ssh import SSHCancellableStream


class SSHProcess(Process):
    """
    Represents a background command execution
    """

    def __init__(self, id: int, command: str, pid: int):
        """
        Initialize a DockerProcess instance.

        Args:
            id (int): The identifier of the command.
            command (str): The command to be executed.
            result: The result of the command execution.
            pid (int): The process ID (PID) of the command.
        """
        self.id = id
        self._command = command
        self._pid = pid

    @property
    def pid(self) -> int:
        return self._pid

    @property
    def command(self) -> str:
        return self._command

    def read_logs(self) -> str:
        """
        Read the logs of the background command.

        Returns:
            str: The logs of the background command.
        """
        return ''


def split_bash_commands(commands):
    # States
    NORMAL = 0
    IN_SINGLE_QUOTE = 1
    IN_DOUBLE_QUOTE = 2
    IN_HEREDOC = 3

    state = NORMAL
    heredoc_trigger = None
    result = []
    current_command: list[str] = []

    i = 0
    while i < len(commands):
        char = commands[i]

        if state == NORMAL:
            if char == "'":
                state = IN_SINGLE_QUOTE
            elif char == '"':
                state = IN_DOUBLE_QUOTE
            elif char == '\\':
                # Check if this is escaping a newline
                if i + 1 < len(commands) and commands[i + 1] == '\n':
                    i += 1  # Skip the newline
                    # Continue with the next line as part of the same command
                    i += 1  # Move to the first character of the next line
                    continue
            elif char == '\n':
                if not heredoc_trigger and current_command:
                    result.append(''.join(current_command).strip())
                    current_command = []
            elif char == '<' and commands[i : i + 2] == '<<':
                # Detect heredoc
                state = IN_HEREDOC
                i += 2  # Skip '<<'
                while commands[i] == ' ':
                    i += 1
                start = i
                while commands[i] not in [' ', '\n']:
                    i += 1
                heredoc_trigger = commands[start:i]
                current_command.append(commands[start - 2 : i])  # Include '<<'
                continue  # Skip incrementing i at the end of the loop
            current_command.append(char)

        elif state == IN_SINGLE_QUOTE:
            current_command.append(char)
            if char == "'" and commands[i - 1] != '\\':
                state = NORMAL

        elif state == IN_DOUBLE_QUOTE:
            current_command.append(char)
            if char == '"' and commands[i - 1] != '\\':
                state = NORMAL

        elif state == IN_HEREDOC:
            current_command.append(char)
            if (
                char == '\n'
                and heredoc_trigger
                and commands[i + 1 : i + 1 + len(heredoc_trigger) + 1]
                == heredoc_trigger + '\n'
            ):
                # Check if the next line starts with the heredoc trigger followed by a newline
                i += (
                    len(heredoc_trigger) + 1
                )  # Move past the heredoc trigger and newline
                current_command.append(
                    heredoc_trigger + '\n'
                )  # Include the heredoc trigger and newline
                result.append(''.join(current_command).strip())
                current_command = []
                heredoc_trigger = None
                state = NORMAL
                continue

        i += 1

    # Add the last command if any
    if current_command:
        result.append(''.join(current_command).strip())

    # Remove any empty strings from the result
    result = [cmd for cmd in result if cmd]

    return result


class SSHBox(Sandbox):
    _hostname: str
    _port: int
    _username: str
    _password: str
    ssh: pexpect.pxssh.pxssh

    cur_background_id = 0
    background_commands: dict[int, Process] = {}

    def __init__(
        self,
        hostname: str = config.ssh_hostname,
        port: int = config.ssh_port,
        username: str = config.ssh_username,
        password: str = config.ssh_password or '',
        timeout: int = config.sandbox_timeout,
        sid: str | None = None,
    ):
        logger.info(
            f'SSHBox is running as {"opendevin" if config.run_as_devin else "root"} user with USER_ID={config.sandbox_user_id} in the sandbox'
        )
        self.timeout = timeout
        self._hostname = hostname
        self._port = port
        self._user = username
        self._password = password

        try:
            self.start_session()
        except pexpect.pxssh.ExceptionPxssh as e:
            self.close()
            raise e

        # make sure /tmp always exists
        self.execute('mkdir -p /tmp')
        # set git config
        self.execute('git config --global user.name "OpenDevin"')
        self.execute('git config --global user.email "opendevin@opendevin.ai"')
        atexit.register(self.close)
        super().__init__()

    # Use the retry decorator, with a maximum of 5 attempts and a fixed wait time of 5 seconds between attempts
    @retry(stop=stop_after_attempt(5), wait=wait_fixed(5))
    def _login(self):
        print('Connecting to SSH session...')
        try:
            self.ssh = pexpect.pxssh.pxssh(
                echo=False,
                timeout=self.timeout,
                encoding='utf-8',
                codec_errors='replace',
            )
            logger.info('Connecting to SSH session...')
            ssh_cmd = f'`ssh -v -p {self._port} {self._username}@{self._hostname}`'
            logger.info(f'You can debug the SSH connection by running: {ssh_cmd}')
            self.ssh.login(
                self._hostname, self._username, self._password, port=self._port
            )
            logger.info('Connected to SSH session')
        except pexpect.pxssh.ExceptionPxssh as e:
            print('exception', e)
            logger.exception(
                'Failed to login to SSH session, retrying...', exc_info=False
            )
            raise e
        except Exception as e:
            print('exception', e)
            logger.exception(
                'Failed to login to SSH session, retrying...', exc_info=False
            )
            raise e

    def start_session(self):
        self._login()

        # Fix: https://github.com/pexpect/pexpect/issues/669
        self.ssh.sendline("bind 'set enable-bracketed-paste off'")
        self.ssh.prompt()
        # cd to workspace
        self.ssh.sendline(f'cd {config.workspace_mount_path_in_sandbox}')
        self.ssh.prompt()

    def get_exec_cmd(self, cmd: str) -> list[str]:
        if config.run_as_devin:
            return ['su', 'opendevin', '-c', cmd]
        else:
            return ['/bin/bash', '-c', cmd]

    def read_logs(self, id) -> str:
        if id not in self.background_commands:
            raise SandboxInvalidBackgroundCommandError()
        bg_cmd = self.background_commands[id]
        return bg_cmd.read_logs()

    def _send_interrupt(
        self,
        cmd: str,
        prev_output: str = '',
        ignore_last_output: bool = False,
    ) -> tuple[int, str]:
        logger.exception(
            f'Command "{cmd}" timed out, killing process...', exc_info=False
        )
        # send a SIGINT to the process
        self.ssh.sendintr()
        self.ssh.prompt()
        command_output = prev_output
        if not ignore_last_output:
            command_output += '\n' + self.ssh.before
        return (
            -1,
            f'Command: "{cmd}" timed out. Sent SIGINT to the process: {command_output}',
        )

    def execute(
        self, cmd: str, stream: bool = False, timeout: int | None = None
    ) -> tuple[int, str | CancellableStream]:
        timeout = timeout or self.timeout
        commands = split_bash_commands(cmd)
        if len(commands) > 1:
            all_output = ''
            for command in commands:
                exit_code, output = self.execute(command)
                if all_output:
                    all_output += '\r\n'
                all_output += str(output)
                if exit_code != 0:
                    return exit_code, all_output
            return 0, all_output

        self.ssh.sendline(cmd)
        if stream:
            return 0, SSHCancellableStream(self.ssh, cmd, self.timeout)
        success = self.ssh.prompt(timeout=timeout)
        if not success:
            return self._send_interrupt(cmd)
        command_output = self.ssh.before

        # once out, make sure that we have *every* output, we while loop until we get an empty output
        while True:
            logger.debug('WAITING FOR .prompt()')
            self.ssh.sendline('\n')
            timeout_not_reached = self.ssh.prompt(timeout=1)
            if not timeout_not_reached:
                logger.debug('TIMEOUT REACHED')
                break
            logger.debug('WAITING FOR .before')
            output = self.ssh.before
            logger.debug(
                f'WAITING FOR END OF command output ({bool(output)}): {output}'
            )
            if isinstance(output, str) and output.strip() == '':
                break
            command_output += output
        command_output = command_output.removesuffix('\r\n')

        # get the exit code
        self.ssh.sendline('echo $?')
        self.ssh.prompt()
        exit_code_str = self.ssh.before.strip()
        _start_time = time.time()
        while not exit_code_str:
            self.ssh.prompt(timeout=1)
            exit_code_str = self.ssh.before.strip()
            logger.debug(f'WAITING FOR exit code: {exit_code_str}')
            if time.time() - _start_time > timeout:
                return self._send_interrupt(
                    cmd, command_output, ignore_last_output=True
                )
        cleaned_exit_code_str = exit_code_str.replace('echo $?', '').strip()

        try:
            exit_code = int(cleaned_exit_code_str)
        except ValueError:
            logger.error(f'Invalid exit code: {cleaned_exit_code_str}')
            # Handle the invalid exit code appropriately (e.g., raise an exception or set a default value)
            exit_code = -1  # or some other appropriate default value

        return exit_code, command_output

    def copy_to(self, host_src: str, sandbox_dest: str, recursive: bool = False):
        pexpect.run(
            f'scp {host_src} {self._user}:{sandbox_dest}',
            events={'(?i)password': self._password},
        )

    def execute_in_background(self, cmd: str) -> Process:
        # TODO: we need the logs here, need to add to background_commands
        self.ssh.sendline(f'nohup {cmd} > /dev/null 2>&1 &')
        self.ssh.prompt()
        pid = self.get_pid(cmd)
        proc = SSHProcess(self.cur_background_id, cmd, pid)
        self.background_commands[self.cur_background_id] = proc
        self.cur_background_id += 1
        return proc

    def get_pid(self, cmd):
        code, logs = self.execute('ps aux')
        processes = logs.splitlines()  # type: ignore [union-attr]
        cmd = ' '.join(self.get_exec_cmd(cmd))

        for process in processes:
            if cmd in process:
                pid = process.split()[1]  # second column is the pid
                return pid
        return None

    def kill_background(self, id: int) -> Process:
        if id not in self.background_commands:
            raise SandboxInvalidBackgroundCommandError()
        bg_cmd = self.background_commands[id]
        if bg_cmd.pid is not None:
            self.execute(
                f'kill -9 {bg_cmd.pid}',
            )
        assert isinstance(bg_cmd, SSHProcess)
        self.background_commands.pop(id)
        return bg_cmd

    def get_working_directory(self):
        exit_code, result = self.execute('pwd')
        if exit_code != 0:
            raise Exception('Failed to get working directory')
        return str(result).strip()

    def close(self):
        if self.ssh:
            self.ssh.logout()
            self.ssh = None


if __name__ == '__main__':
    try:
        ssh_box = SSHBox()
    except Exception as e:
        logger.exception('Failed to connect to ssh: %s', e)
        sys.exit(1)

    logger.info("SSH box started. Type 'exit' or use Ctrl+C to exit.")

    # Initialize required plugins
    ssh_box.init_plugins([AgentSkillsRequirement(), JupyterRequirement()])
    logger.info(
        '--- AgentSkills COMMAND DOCUMENTATION ---\n'
        f'{AgentSkillsRequirement().documentation}\n'
        '---'
    )

    bg_cmd = ssh_box.execute_in_background(
        "while true; do echo -n '.' && sleep 10; done"
    )

    sys.stdout.flush()
    try:
        while True:
            try:
                user_input = input('$ ')
            except EOFError:
                logger.info('Exiting...')
                break
            if user_input.lower() == 'exit':
                logger.info('Exiting...')
                break
            if user_input.lower() == 'kill':
                ssh_box.kill_background(bg_cmd.pid)
                logger.info('Background process killed')
                continue
            exit_code, output = ssh_box.execute(user_input)
            logger.info('exit code: %d', exit_code)
            logger.info(output)
            if bg_cmd.pid in ssh_box.background_commands:
                logs = ssh_box.read_logs(bg_cmd.pid)
                logger.info('background logs: %s', logs)
            sys.stdout.flush()
    except KeyboardInterrupt:
        logger.info('Exiting...')
    ssh_box.close()
