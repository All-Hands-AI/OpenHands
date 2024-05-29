import atexit
import os
import re
import sys
import tarfile
import tempfile
import time
import uuid
from collections import namedtuple
from glob import glob

import docker
from pexpect import exceptions, pxssh
from tenacity import retry, stop_after_attempt, wait_fixed

from opendevin.core.config import config
from opendevin.core.const.guide_url import TROUBLESHOOTING_URL
from opendevin.core.exceptions import SandboxInvalidBackgroundCommandError
from opendevin.core.logger import opendevin_logger as logger
from opendevin.core.schema import CancellableStream
from opendevin.runtime.docker.process import DockerProcess, Process
from opendevin.runtime.plugins import AgentSkillsRequirement, JupyterRequirement
from opendevin.runtime.sandbox import Sandbox
from opendevin.runtime.utils import find_available_tcp_port

# FIXME: these are not used, can we remove them?
InputType = namedtuple('InputType', ['content'])
OutputType = namedtuple('OutputType', ['content'])


class SSHExecCancellableStream(CancellableStream):
    def __init__(self, ssh, cmd, timeout):
        super().__init__(self.read_output())
        self.ssh = ssh
        self.cmd = cmd
        self.timeout = timeout

    def close(self):
        self.closed = True

    def exit_code(self):
        self.ssh.sendline('echo $?')
        success = self.ssh.prompt(timeout=self.timeout)
        if not success:
            return -1

        _exit_code = self.ssh.before.strip()
        return int(_exit_code)

    def read_output(self):
        st = time.time()
        buf = ''
        crlf = '\r\n'
        lf = '\n'
        prompt_len = len(self.ssh.PROMPT)
        while True:
            try:
                if self.closed:
                    break
                _output = self.ssh.read_nonblocking(timeout=1)
                if not _output:
                    continue

                buf += _output

                if len(buf) < prompt_len:
                    continue

                match = re.search(self.ssh.PROMPT, buf)
                if match:
                    idx, _ = match.span()
                    yield buf[:idx].replace(crlf, lf)
                    buf = ''
                    break

                res = buf[:-prompt_len]
                if len(res) == 0 or res.find(crlf) == -1:
                    continue
                buf = buf[-prompt_len:]
                yield res.replace(crlf, lf)
            except exceptions.TIMEOUT:
                if time.time() - st < self.timeout:
                    match = re.search(self.ssh.PROMPT, buf)
                    if match:
                        idx, _ = match.span()
                        yield buf[:idx].replace(crlf, lf)
                        break
                    continue
                else:
                    yield buf.replace(crlf, lf)
                break
            except exceptions.EOF:
                break


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


class DockerSSHBox(Sandbox):
    instance_id: str
    container_image: str
    container_name_prefix = 'opendevin-sandbox-'
    container_name: str
    container: docker.models.containers.Container
    docker_client: docker.DockerClient

    _ssh_password: str
    _ssh_port: int
    ssh: pxssh.pxssh

    cur_background_id = 0
    background_commands: dict[int, Process] = {}

    def __init__(
        self,
        container_image: str | None = None,
        timeout: int = config.sandbox_timeout,
        sid: str | None = None,
    ):
        logger.info(
            f'SSHBox is running as {"opendevin" if self.run_as_devin else "root"} user with USER_ID={self.user_id} in the sandbox'
        )
        # Initialize docker client. Throws an exception if Docker is not reachable.
        try:
            self.docker_client = docker.from_env()
        except Exception as ex:
            logger.exception(
                f'Error creating controller. Please check Docker is running and visit `{TROUBLESHOOTING_URL}` for more debugging information.',
                exc_info=False,
            )
            raise ex

        self.instance_id = (
            sid + str(uuid.uuid4()) if sid is not None else str(uuid.uuid4())
        )

        self.timeout = timeout
        self.container_image = (
            config.sandbox_container_image
            if container_image is None
            else container_image
        )
        self.container_name = self.container_name_prefix + self.instance_id

        # set up random user password
        self._ssh_password = str(uuid.uuid4())
        self._ssh_port = find_available_tcp_port()

        # always restart the container, cuz the initial be regarded as a new session
        n_tries = 5
        while n_tries > 0:
            try:
                self.restart_docker_container()
                break
            except Exception as e:
                logger.exception(
                    'Failed to start Docker container, retrying...', exc_info=False
                )
                n_tries -= 1
                if n_tries == 0:
                    raise e
                time.sleep(5)
        self.setup_user()

        try:
            self.start_ssh_session()
        except pxssh.ExceptionPxssh as e:
            self.close()
            raise e

        # make sure /tmp always exists
        self.execute('mkdir -p /tmp')
        # set git config
        self.execute('git config --global user.name "OpenDevin"')
        self.execute('git config --global user.email "opendevin@opendevin.ai"')
        atexit.register(self.close)
        super().__init__()

    def add_to_env(self, key: str, value: str):
        super().add_to_env(key, value)

    def setup_user(self):
        # Make users sudoers passwordless
        # TODO(sandbox): add this line in the Dockerfile for next minor version of docker image
        exit_code, logs = self.container.exec_run(
            ['/bin/bash', '-c', r"echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers"],
            workdir=self.sandbox_workspace_dir,
            environment=self._env,
        )
        if exit_code != 0:
            raise Exception(
                f'Failed to make all users passwordless sudoers in sandbox: {logs}'
            )

        # Check if the opendevin user exists
        exit_code, logs = self.container.exec_run(
            ['/bin/bash', '-c', 'id -u opendevin'],
            workdir=self.sandbox_workspace_dir,
            environment=self._env,
        )
        if exit_code == 0:
            # User exists, delete it
            exit_code, logs = self.container.exec_run(
                ['/bin/bash', '-c', 'userdel -r opendevin'],
                workdir=self.sandbox_workspace_dir,
                environment=self._env,
            )
            if exit_code != 0:
                raise Exception(f'Failed to remove opendevin user in sandbox: {logs}')

        if self.run_as_devin:
            # Create the opendevin user
            exit_code, logs = self.container.exec_run(
                [
                    '/bin/bash',
                    '-c',
                    f'useradd -rm -d /home/opendevin -s /bin/bash -g root -G sudo -u {self.user_id} opendevin',
                ],
                workdir=self.sandbox_workspace_dir,
                environment=self._env,
            )
            if exit_code != 0:
                raise Exception(f'Failed to create opendevin user in sandbox: {logs}')
            exit_code, logs = self.container.exec_run(
                [
                    '/bin/bash',
                    '-c',
                    f"echo 'opendevin:{self._ssh_password}' | chpasswd",
                ],
                workdir=self.sandbox_workspace_dir,
                environment=self._env,
            )
            if exit_code != 0:
                raise Exception(f'Failed to set password in sandbox: {logs}')

            # chown the home directory
            exit_code, logs = self.container.exec_run(
                ['/bin/bash', '-c', 'chown opendevin:root /home/opendevin'],
                workdir=self.sandbox_workspace_dir,
                environment=self._env,
            )
            if exit_code != 0:
                raise Exception(
                    f'Failed to chown home directory for opendevin in sandbox: {logs}'
                )
            exit_code, logs = self.container.exec_run(
                [
                    '/bin/bash',
                    '-c',
                    f'chown opendevin:root {self.sandbox_workspace_dir}',
                ],
                workdir=self.sandbox_workspace_dir,
                environment=self._env,
            )
            if exit_code != 0:
                # This is not a fatal error, just a warning
                logger.warning(
                    f'Failed to chown workspace directory for opendevin in sandbox: {logs}. But this should be fine if the {self.sandbox_workspace_dir=} is mounted by the app docker container.'
                )
        else:
            exit_code, logs = self.container.exec_run(
                # change password for root
                ['/bin/bash', '-c', f"echo 'root:{self._ssh_password}' | chpasswd"],
                workdir=self.sandbox_workspace_dir,
                environment=self._env,
            )
            if exit_code != 0:
                raise Exception(f'Failed to set password for root in sandbox: {logs}')
        exit_code, logs = self.container.exec_run(
            ['/bin/bash', '-c', "echo 'opendevin-sandbox' > /etc/hostname"],
            workdir=self.sandbox_workspace_dir,
            environment=self._env,
        )

    # Use the retry decorator, with a maximum of 5 attempts and a fixed wait time of 5 seconds between attempts
    @retry(stop=stop_after_attempt(5), wait=wait_fixed(5))
    def __ssh_login(self):
        try:
            self.ssh = pxssh.pxssh(
                echo=False,
                timeout=self.timeout,
                encoding='utf-8',
                codec_errors='replace',
            )
            hostname = self.ssh_hostname
            username = 'opendevin' if self.run_as_devin else 'root'
            logger.info(
                f'Connecting to {username}@{hostname} via ssh. '
                f"If you encounter any issues, you can try `ssh -v -p {self._ssh_port} {username}@{hostname}` with the password '{self._ssh_password}' and report the issue on GitHub. "
                f"If you started OpenDevin with `docker run`, you should try `ssh -v -p {self._ssh_port} {username}@localhost` with the password '{self._ssh_password} on the host machine (where you started the container)."
            )
            self.ssh.login(hostname, username, self._ssh_password, port=self._ssh_port)
        except pxssh.ExceptionPxssh as e:
            logger.exception(
                'Failed to login to SSH session, retrying...', exc_info=False
            )
            raise e

    def start_ssh_session(self):
        self.__ssh_login()

        # Fix: https://github.com/pexpect/pexpect/issues/669
        self.ssh.sendline("bind 'set enable-bracketed-paste off'")
        self.ssh.prompt()
        # cd to workspace
        self.ssh.sendline(f'cd {self.sandbox_workspace_dir}')
        self.ssh.prompt()

    def get_exec_cmd(self, cmd: str) -> list[str]:
        if self.run_as_devin:
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
        logger.exception('Command timed out, killing process...', exc_info=False)
        # send a SIGINT to the process
        self.ssh.sendintr()
        self.ssh.prompt()
        command_output = prev_output
        if not ignore_last_output:
            command_output += '\n' + self.ssh.before
        return (
            -1,
            f'Command: "{cmd}" timed out. Sending SIGINT to the process: {command_output}',
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
            return 0, SSHExecCancellableStream(self.ssh, cmd, self.timeout)
        success = self.ssh.prompt(timeout=timeout)
        if not success:
            logger.exception('Command timed out, killing process...', exc_info=False)
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
        # mkdir -p sandbox_dest if it doesn't exist
        exit_code, logs = self.container.exec_run(
            ['/bin/bash', '-c', f'mkdir -p {sandbox_dest}'],
            workdir=self.sandbox_workspace_dir,
            environment=self._env,
        )
        if exit_code != 0:
            raise Exception(
                f'Failed to create directory {sandbox_dest} in sandbox: {logs}'
            )

        # use temp directory to store the tar file to avoid
        # conflict of filename when running multi-processes
        with tempfile.TemporaryDirectory() as tmp_dir:
            if recursive:
                assert os.path.isdir(
                    host_src
                ), 'Source must be a directory when recursive is True'
                files = glob(host_src + '/**/*', recursive=True)
                srcname = os.path.basename(host_src)
                tar_filename = os.path.join(tmp_dir, srcname + '.tar')
                with tarfile.open(tar_filename, mode='w') as tar:
                    for file in files:
                        tar.add(
                            file,
                            arcname=os.path.relpath(file, os.path.dirname(host_src)),
                        )
            else:
                assert os.path.isfile(
                    host_src
                ), 'Source must be a file when recursive is False'
                srcname = os.path.basename(host_src)
                tar_filename = os.path.join(tmp_dir, srcname + '.tar')
                with tarfile.open(tar_filename, mode='w') as tar:
                    tar.add(host_src, arcname=srcname)

            with open(tar_filename, 'rb') as f:
                data = f.read()
            self.container.put_archive(os.path.dirname(sandbox_dest), data)

    def execute_in_background(self, cmd: str) -> Process:
        result = self.container.exec_run(
            self.get_exec_cmd(cmd),
            socket=True,
            workdir=self.sandbox_workspace_dir,
            environment=self._env,
        )
        result.output._sock.setblocking(0)
        pid = self.get_pid(cmd)
        bg_cmd = DockerProcess(self.cur_background_id, cmd, result, pid)
        self.background_commands[bg_cmd.pid] = bg_cmd
        self.cur_background_id += 1
        return bg_cmd

    def get_pid(self, cmd):
        exec_result = self.container.exec_run('ps aux', environment=self._env)
        processes = exec_result.output.decode('utf-8').splitlines()
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
            self.container.exec_run(
                f'kill -9 {bg_cmd.pid}',
                workdir=self.sandbox_workspace_dir,
                environment=self._env,
            )
        assert isinstance(bg_cmd, DockerProcess)
        bg_cmd.result.output.close()
        self.background_commands.pop(id)
        return bg_cmd

    def stop_docker_container(self):
        try:
            container = self.docker_client.containers.get(self.container_name)
            container.stop()
            container.remove()
            elapsed = 0
            while container.status != 'exited':
                time.sleep(1)
                elapsed += 1
                if elapsed > self.timeout:
                    break
                container = self.docker_client.containers.get(self.container_name)
        except docker.errors.NotFound:
            pass

    def get_working_directory(self):
        exit_code, result = self.execute('pwd')
        if exit_code != 0:
            raise Exception('Failed to get working directory')
        return str(result).strip()

    @property
    def user_id(self):
        return config.sandbox_user_id

    @property
    def sandbox_user_id(self):
        return config.sandbox_user_id

    @property
    def run_as_devin(self):
        return config.run_as_devin

    @property
    def sandbox_workspace_dir(self):
        return config.workspace_mount_path_in_sandbox

    @property
    def ssh_hostname(self):
        return config.ssh_hostname

    @property
    def use_host_network(self):
        return config.use_host_network

    def is_container_running(self):
        try:
            container = self.docker_client.containers.get(self.container_name)
            if container.status == 'running':
                self.container = container
                return True
            return False
        except docker.errors.NotFound:
            return False

    @property
    def volumes(self):
        mount_dir = config.workspace_mount_path
        logger.info(f'Mounting workspace directory: {mount_dir}')
        return {
            mount_dir: {'bind': self.sandbox_workspace_dir, 'mode': 'rw'},
            # mount cache directory to /home/opendevin/.cache for pip cache reuse
            config.cache_dir: {
                'bind': (
                    '/home/opendevin/.cache' if self.run_as_devin else '/root/.cache'
                ),
                'mode': 'rw',
            },
        }

    def restart_docker_container(self):
        try:
            self.stop_docker_container()
            logger.info('Container stopped')
        except docker.errors.DockerException as ex:
            logger.exception('Failed to stop container', exc_info=False)
            raise ex

        try:
            network_kwargs: dict[str, str | dict[str, int]] = {}
            if self.use_host_network:
                network_kwargs['network_mode'] = 'host'
            else:
                # FIXME: This is a temporary workaround for Mac OS
                network_kwargs['ports'] = {f'{self._ssh_port}/tcp': self._ssh_port}
                logger.warning(
                    (
                        'Using port forwarding for Mac OS. '
                        'Server started by OpenDevin will not be accessible from the host machine at the moment. '
                        'See https://github.com/OpenDevin/OpenDevin/issues/897 for more information.'
                    )
                )

            # start the container
            logger.info(f'Mounting volumes: {self.volumes}')
            self.container = self.docker_client.containers.run(
                self.container_image,
                # allow root login
                command=f"/usr/sbin/sshd -D -p {self._ssh_port} -o 'PermitRootLogin=yes'",
                **network_kwargs,
                working_dir=self.sandbox_workspace_dir,
                name=self.container_name,
                detach=True,
                volumes=self.volumes,
            )
            logger.info('Container started')
        except Exception as ex:
            logger.exception('Failed to start container', exc_info=False)
            raise ex

        # wait for container to be ready
        elapsed = 0
        while self.container.status != 'running':
            if self.container.status == 'exited':
                logger.info('container exited')
                logger.info('container logs:')
                logger.info(self.container.logs())
                break
            time.sleep(1)
            elapsed += 1
            self.container = self.docker_client.containers.get(self.container_name)
            logger.info(
                f'waiting for container to start: {elapsed}, container status: {self.container.status}'
            )
            if elapsed > self.timeout:
                break
        if self.container.status != 'running':
            raise Exception('Failed to start container')

    # clean up the container, cannot do it in __del__ because the python interpreter is already shutting down
    def close(self):
        containers = self.docker_client.containers.list(all=True)
        for container in containers:
            try:
                if container.name.startswith(self.container_name):
                    # only remove the container we created
                    # otherwise all other containers with the same prefix will be removed
                    # which will mess up with parallel evaluation
                    container.remove(force=True)
            except docker.errors.NotFound:
                pass


if __name__ == '__main__':
    try:
        ssh_box = DockerSSHBox()
    except Exception as e:
        logger.exception('Failed to start Docker container: %s', e)
        sys.exit(1)

    logger.info(
        "Interactive Docker container started. Type 'exit' or use Ctrl+C to exit."
    )

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
