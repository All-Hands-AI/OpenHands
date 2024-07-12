import asyncio
import atexit
import json
import os
import re
import socket
import sys
import tarfile
import tempfile
import time
import uuid
from glob import glob
from typing import Tuple, Union  # type: ignore[unused-import]

import docker
from pexpect import exceptions, pxssh
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    wait_fixed,
)

from opendevin.core.config import config
from opendevin.core.const.guide_url import TROUBLESHOOTING_URL
from opendevin.core.logger import opendevin_logger as logger
from opendevin.core.schema import CancellableStream
from opendevin.runtime.plugins import AgentSkillsRequirement, JupyterRequirement
from opendevin.runtime.sandbox import Sandbox
from opendevin.runtime.utils import find_available_tcp_port
from opendevin.runtime.utils.async_utils import async_to_sync
from opendevin.runtime.utils.image_agnostic import get_od_sandbox_image


class SSHExecCancellableStream(CancellableStream):
    def __init__(self, ssh, cmd, timeout):
        super().__init__(self.read_output())
        self.ssh = ssh
        self.cmd = cmd
        self.timeout = timeout

    def close(self):
        self.closed = True

    def exit_code(self):
        marker = f'EXIT_CODE_MARKER_{uuid.uuid4().hex}'
        self.ssh.sendline(f'echo "{marker}$?{marker}"')

        if not self.ssh.prompt(timeout=self.timeout):
            return None  # Timeout occurred

        output = self.ssh.before
        match = re.search(f'{marker}(\\d+){marker}', output)

        if match:
            try:
                return int(match.group(1))
            except ValueError:
                # Log the unexpected format
                logger.error(f'Unexpected exit code format: {match.group(1)}')
                return None
        else:
            # If we can't find our marked exit code, log the output and return None
            logger.error(f'Could not find exit code in output: {output}')
            return None

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
    _instance = None
    _initialization_lock = asyncio.Lock()

    instance_id: str
    container_image: str
    container_name_prefix = 'opendevin-sandbox-'
    container_name: str
    container: docker.models.containers.Container
    docker_client: docker.DockerClient

    _ssh_password: str
    _ssh_port: int
    ssh: pxssh.pxssh

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        container_image: str | None = None,
        timeout: int = config.sandbox.timeout,
        sid: str | None = None,
    ):
        if not hasattr(self, 'initialized'):
            super().__init__()
            self.sid = sid
            self.initialized = False
            self.ssh = None
            self._sshbox_init_complete = asyncio.Event()
            self.initialize_plugins: bool = config.initialize_plugins

            self.timeout = timeout
            if config.persist_sandbox:
                if not self.run_as_devin:
                    raise RuntimeError(
                        'Persistent sandbox is currently designed for opendevin user only. Please set run_as_devin=True in your config.toml'
                    )
                self.instance_id = 'persisted'
            else:
                self.instance_id = (sid or '') + str(uuid.uuid4())

            if config.persist_sandbox:
                if not config.ssh_password:
                    raise RuntimeError(
                        'Please add ssh_password to your config.toml or add -e SSH_PASSWORD to your docker run command'
                    )
                self._ssh_password = config.ssh_password
                self._ssh_port = config.ssh_port
            else:
                self._ssh_password = str(uuid.uuid4())
                self._ssh_port = find_available_tcp_port()

            self.is_initial_session = True

            self.container_image = container_image or config.sandbox.container_image
            self.container_name = self.container_name_prefix + self.instance_id

            # Initialize _env with SANDBOX_ENV_ prefixed variables
            self._env = {
                k[12:]: v for k, v in os.environ.items() if k.startswith('SANDBOX_ENV_')
            }
            if isinstance(config.sandbox.env, dict):
                self._env.update(config.sandbox.env)

            self._cleanup_done = False
            atexit.register(self.sync_cleanup)

    @async_to_sync
    def initialize(self):
        return self.initialize_async()

    async def initialize_async(self):
        if not self._sshbox_init_complete.is_set():
            async with self._initialization_lock:
                if not self._sshbox_init_complete.is_set():
                    logger.info(
                        'SSHBox is running as opendevin user with USER_ID=1000 in the sandbox'
                    )
                    try:
                        # await super().initialize()
                        await self._setup_docker()
                        await self._setup_container()
                        await self._setup_user()
                        await self._setup_ssh()
                        self.initialized = True
                        logger.info('SSHBox initialization complete')
                    finally:
                        self._sshbox_init_complete.set()
        else:
            await self._sshbox_init_complete.wait()

    @classmethod
    async def reset_instance(cls):
        if cls._instance is not None:
            await cls._instance.aclose()
            cls._instance = None
        cls._initialization_lock = asyncio.Lock()

    async def _setup_docker(self):
        # Initialize Docker client
        try:
            self.docker_client = await asyncio.to_thread(docker.from_env)
        except RuntimeError as ex:
            logger.exception(
                f'Error creating Docker client. Please check Docker is running and visit `{TROUBLESHOOTING_URL}` for more debugging information.',
                exc_info=False,
            )
            raise ex

        self.container_image = await asyncio.to_thread(
            get_od_sandbox_image, self.container_image, self.docker_client
        )

    async def _setup_container(self):
        # Set up the Docker container
        try:
            self.container = await asyncio.to_thread(
                self.docker_client.containers.get, self.container_name
            )
            self.is_initial_session = False
        except docker.errors.NotFound:
            self.is_initial_session = True

        if not config.persist_sandbox or self.is_initial_session:
            await self._create_new_container()
        else:
            await self._use_existing_container()

    async def _create_new_container(self):
        logger.info('Creating new Docker container')
        try:
            await self.restart_docker_container()
        except docker.errors.APIError as ex:
            if ex.status_code == 409 and 'is already in use by container' in str(ex):
                # Extract the conflicting container ID from the error message
                conflicting_container_id = ex.explanation.split('"')[1]
                logger.warning(
                    f'Removing conflicting container: {conflicting_container_id}'
                )
                self.docker_client.containers.get(conflicting_container_id).remove(
                    force=True
                )
                # Retry creating the container
                await self.restart_docker_container()
            else:
                raise

    async def _use_existing_container(self):
        self.container = await asyncio.to_thread(
            self.docker_client.containers.get, self.container_name
        )
        logger.info('Using existing Docker container')
        await self.start_docker_container()

    async def _setup_environment(self):
        try:
            await self.execute_async('mkdir -p /tmp')
            await self.execute_async('git config --global user.name "OpenDevin"')
            await self.execute_async(
                'git config --global user.email "opendevin@all-hands.dev"'
            )
        except Exception as e:
            logger.exception(f'Error during initialization: {e}')
            raise

    @async_to_sync
    def add_to_env(self, key: str, value: str):
        return self.add_to_env_async(key, value)

    async def add_to_env_async(self, key: str, value: str):
        exit_code, _ = await self.execute_async(f'export {key}={json.dumps(value)}')
        if exit_code == 0:
            self._env[key] = value
        else:
            raise RuntimeError(f'Failed to set environment variable {key}')

    async def container_exec_run(self, *args, **kwargs):
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, lambda: self.container.exec_run(*args, **kwargs)
        )
        return result  # Returns a tuple (exit_code, output)

    async def _setup_user(self):
        # Make users sudoers passwordless
        # TODO(sandbox): add this line in the Dockerfile for next minor version of docker image
        result = await self.container_exec_run(
            ['/bin/bash', '-c', r"echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers"],
            workdir=self.sandbox_workspace_dir,
            environment=self._env,
        )
        exit_code, logs = result
        if exit_code != 0:
            raise RuntimeError(
                f'Failed to make all users passwordless sudoers in sandbox: {logs}'
            )

        # Check if the opendevin user exists
        exit_code, logs = await self.container_exec_run(
            ['/bin/bash', '-c', 'id -u opendevin'],
            workdir=self.sandbox_workspace_dir,
            environment=self._env,
        )
        if exit_code == 0:
            # User exists, delete it
            exit_code, logs = await self.container_exec_run(
                ['/bin/bash', '-c', 'userdel -r opendevin'],
                workdir=self.sandbox_workspace_dir,
                environment=self._env,
            )
            if exit_code != 0:
                raise Exception(f'Failed to remove opendevin user in sandbox: {logs}')

        if self.run_as_devin:
            # Create the opendevin user
            exit_code, logs = await self.container_exec_run(
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
            exit_code, logs = await self.container_exec_run(
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
            exit_code, logs = await self.container_exec_run(
                ['/bin/bash', '-c', 'chown opendevin:root /home/opendevin'],
                workdir=self.sandbox_workspace_dir,
                environment=self._env,
            )
            if exit_code != 0:
                raise RuntimeError(
                    f'Failed to chown home directory for opendevin in sandbox: {logs}'
                )
            # check the miniforge3 directory exist
            exit_code, logs = await self.container_exec_run(
                [
                    '/bin/bash',
                    '-c',
                    '[ -d "/opendevin/miniforge3" ] && exit 0 || exit 1',
                ],
                workdir=self.sandbox_workspace_dir,
                environment=self._env,
            )
            if exit_code != 0:
                if exit_code == 1:
                    raise RuntimeError(
                        'OPENDEVIN_PYTHON_INTERPRETER is not usable. Please pull the latest Docker image: docker pull ghcr.io/opendevin/sandbox:main'
                    )
                else:
                    raise RuntimeError(
                        f'An error occurred while checking if miniforge3 directory exists: {logs}'
                    )
            exit_code, logs = await self.container_exec_run(
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
            exit_code, logs = await self.container_exec_run(
                # change password for root
                ['/bin/bash', '-c', f"echo 'root:{self._ssh_password}' | chpasswd"],
                workdir=self.sandbox_workspace_dir,
                environment=self._env,
            )
            if exit_code != 0:
                raise RuntimeError(
                    f'Failed to set password for root in sandbox: {logs}'
                )
        exit_code, logs = await self.container_exec_run(
            ['/bin/bash', '-c', "echo 'opendevin-sandbox' > /etc/hostname"],
            workdir=self.sandbox_workspace_dir,
            environment=self._env,
        )

        # Add a check to ensure the user was created successfully
        exit_code, logs = await self.container_exec_run(
            ['/bin/bash', '-c', 'id opendevin'],
            workdir=self.sandbox_workspace_dir,
            environment=self._env,
        )
        if exit_code != 0:
            raise RuntimeError(f'Failed to create or verify opendevin user: {logs}')

        logger.info('User setup in sandbox completed')

    # Use the retry decorator, with a maximum of 5 attempts and a fixed wait time of 5 seconds between attempts
    @retry(
        stop=stop_after_attempt(2),
        wait=wait_fixed(5),
        retry=retry_if_exception_type(pxssh.ExceptionPxssh),
    )
    async def _setup_ssh(self):
        try:
            await self.wait_for_ssh_ready()
            await self.start_ssh_session()
        except pxssh.ExceptionPxssh as e:
            logger.error(
                f'SSH session failed, attempting to restart container.\nError: {e}'
            )
            if not config.persist_sandbox:
                await self.restart_container()
            raise e

    async def wait_for_ssh_ready(self):
        max_attempts = 10
        for attempt in range(max_attempts):
            try:
                exit_code, output = await self.container_exec_run(
                    ['sh', '-c', "service ssh status | grep 'is running'"]
                )
                if exit_code == 0:
                    logger.info('SSH service is running')
                    # Add a small delay after confirming SSH is running
                    await asyncio.sleep(2)
                    return
            except Exception as e:
                logger.warning(f'Error checking SSH status: {e}')

            logger.info(
                f'Waiting for SSH service to start (attempt {attempt + 1}/{max_attempts})'
            )
            await asyncio.sleep(2)

        raise RuntimeError('SSH service failed to start in time')

    def send_line(self, cmd: str):
        if self.ssh is not None:
            self.ssh.sendline(cmd)

    async def start_ssh_session(self):
        logger.info('Starting SSH session')
        await self.__ssh_login()
        await asyncio.sleep(1)

        # Fix: https://github.com/pexpect/pexpect/issues/669
        self.send_line("bind 'set enable-bracketed-paste off'")
        self.ssh.prompt()
        # cd to workspace
        self.send_line(f'cd {self.sandbox_workspace_dir}')
        self.ssh.prompt()

    async def restart_container(self):
        logger.info('Restarting container...')
        await self.aclose()
        await self._setup_docker()
        await self._setup_container()
        await asyncio.sleep(2)
        await self._setup_user()
        await self._setup_ssh()
        await asyncio.sleep(3)
        logger.info('Container restarted successfully.')

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(
            (exceptions.TIMEOUT, exceptions.EOF, pxssh.ExceptionPxssh)
        ),
        reraise=True,
    )
    async def __ssh_login(self):
        try:
            if not hasattr(self, '_ssh_debug_logged'):
                hostname = self.ssh_hostname
                username = 'opendevin' if self.run_as_devin else 'root'
                if config.persist_sandbox:
                    password_msg = 'using your SSH password'
                else:
                    password_msg = f"using the password '{self._ssh_password}'"
                ssh_cmd = f'`ssh -v -p {self._ssh_port} {username}@{hostname}`'
                logger.info(
                    f'You can debug the SSH connection by running: {ssh_cmd} {password_msg}'
                )
                self._ssh_debug_logged = True

            logger.debug(
                f"Attempting SSH login to {self.ssh_hostname}:{self._ssh_port} as {'opendevin' if self.run_as_devin else 'root'}"
            )

            self.ssh = pxssh.pxssh(
                echo=False,
                timeout=self.timeout,
                encoding='utf-8',
                codec_errors='replace',
            )
            await asyncio.sleep(1)

            # Wrap the blocking login call in asyncio.to_thread
            await asyncio.to_thread(
                self.ssh.login,
                self.ssh_hostname,
                'opendevin' if self.run_as_devin else 'root',
                self._ssh_password,
                port=self._ssh_port,
                login_timeout=20,
            )

            # Verify the connection
            if not await self.__verify_ssh_connection():
                raise exceptions.EOF('Failed to verify SSH connection')

            logger.info('Connected to SSH session')
        except pxssh.ExceptionPxssh as e:
            logger.exception(f'Failed to login to SSH session: {e}')
            logger.debug(f'SSH debug output: {self.ssh.before}')
            if 'connection refused' in str(e).lower():
                logger.error('SSH connection refused')
            raise

    async def __verify_ssh_connection(self):
        try:
            exit_code, output = await self.execute_async(
                "echo 'SSH connection test'", timeout=5
            )
            return exit_code == 0 and 'SSH connection test' in output
        except Exception as e:
            logger.error(f'Failed to verify SSH connection: {e}')
            return False

    def get_exec_cmd(self, cmd: str) -> list[str]:
        if self.run_as_devin:
            return ['su', 'opendevin', '-c', cmd]
        else:
            return ['/bin/bash', '-c', cmd]

    def _send_interrupt(
        self,
        cmd: str,
        prev_output: str = '',
        ignore_last_output: bool = False,
    ) -> tuple[int, str | CancellableStream]:
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

    @async_to_sync
    def execute(
        self, cmd: str, stream: bool = False, timeout: int | None = None
    ) -> Union[Tuple[int, str], Tuple[int, CancellableStream]]:
        return self.execute_async(cmd, stream, timeout)  # type: ignore

    async def execute_async(
        self,
        cmd: str,
        stream: bool = False,
        timeout: int | None = None,
        # ) -> Union[Tuple[int, str], Tuple[int, CancellableStream]]:
    ) -> tuple[int, str | CancellableStream]:
        # Ensure initialization is complete
        if not self.initialized:
            await self.initialize_async()

        timeout = timeout or self.timeout
        commands = split_bash_commands(cmd)

        if len(commands) > 1:
            all_output = ''
            for command in commands:
                exit_code, output = await self.execute_async(command, stream, timeout)  # type: ignore
                if all_output:
                    all_output += '\r\n'
                all_output += str(output)
                if exit_code != 0:
                    return exit_code, all_output
            return 0, all_output

        # Prepare environment variables
        env_exports = ' '.join(
            [f'export {key}={json.dumps(value)}' for key, value in self._env.items()]
        )
        if env_exports:
            full_cmd = f'({env_exports}) && {cmd}'
        else:
            full_cmd = f'{cmd}'
        self.send_line(full_cmd)
        if stream:
            return 0, SSHExecCancellableStream(self.ssh, full_cmd, self.timeout)

        success = await asyncio.to_thread(self.ssh.prompt, timeout=timeout)
        if not success:
            return self._send_interrupt(full_cmd)  # type: ignore
        command_output = self.ssh.before

        # once out, make sure that we have *every* output, we while loop until we get an empty output
        while True:
            self.send_line('\n')
            timeout_not_reached = await asyncio.to_thread(self.ssh.prompt, timeout=1)
            if not timeout_not_reached:
                logger.debug('TIMEOUT REACHED')
                break
            output = self.ssh.before
            if isinstance(output, str) and output.strip() == '':
                break
            command_output += output
        command_output = command_output.removesuffix('\r\n')

        # get the exit code
        self.send_line('echo $?')
        await asyncio.to_thread(self.ssh.prompt)
        exit_code_str = self.ssh.before.strip()
        _start_time = time.time()
        while not exit_code_str:
            await asyncio.to_thread(self.ssh.prompt, timeout=1)
            exit_code_str = self.ssh.before.strip()
            if time.time() - _start_time > timeout:
                return self._send_interrupt(  # type: ignore
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

    @async_to_sync
    def copy_to(self, host_src: str, sandbox_dest: str, recursive: bool = False):
        return self.copy_to_async(host_src, sandbox_dest, recursive)

    async def copy_to_async(
        self, host_src: str, sandbox_dest: str, recursive: bool = False
    ):
        # mkdir -p sandbox_dest if it doesn't exist
        exit_code, logs = await self.container_exec_run(  # type: ignore
            ['/bin/bash', '-c', f'mkdir -p {sandbox_dest}'],
            workdir=self.sandbox_workspace_dir,
            environment=self._env,
        )
        if exit_code != 0:
            raise RuntimeError(
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

    async def start_docker_container(self):
        try:
            container = await asyncio.to_thread(
                self.docker_client.containers.get, self.container_name
            )
            if container.status != 'running':
                await asyncio.to_thread(container.start)
                logger.info('Container started')
            await self.wait_for_container_ready()
        except Exception:
            logger.exception('Failed to start container')

    def remove_docker_container(self):
        try:
            container = self.docker_client.containers.get(self.container_name)
            container.stop()
            logger.info('Container stopped')
            container.remove()
            logger.info('Container removed')
            elapsed = 0
            while container.status != 'exited':
                time.sleep(2)
                elapsed += 1
                if elapsed > self.timeout:
                    break
                container = self.docker_client.containers.get(self.container_name)
        except docker.errors.NotFound:
            pass

    async def get_working_directory(self):
        exit_code, result = await self.execute('pwd')
        if exit_code != 0:
            raise RuntimeError('Failed to get working directory')
        return str(result).strip()

    @property
    def user_id(self):
        return config.sandbox.user_id

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

    async def is_container_running(self):
        try:
            container = await self.docker_client.containers.get(self.container_name)
            if container.status == 'running':
                self.container = container
                return True
            return False
        except docker.errors.NotFound:
            return False

    @property
    def volumes(self):
        mount_dir = config.workspace_mount_path
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

    def find_free_port(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            return s.getsockname()[1]

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(2),
        retry=retry_if_exception_type(docker.errors.APIError),
    )
    async def restart_docker_container(self):
        try:
            await asyncio.to_thread(self.remove_docker_container)
        except docker.errors.DockerException as ex:
            logger.exception('Failed to remove container', exc_info=False)
            raise ex

        try:
            network_kwargs: dict[str, str | dict[str, int]] = {}
            if self.use_host_network:
                network_kwargs['network_mode'] = 'host'
            else:
                # Use dynamic port allocation
                self._ssh_port = self.find_free_port()
                network_kwargs['ports'] = {f'{self._ssh_port}/tcp': self._ssh_port}
                logger.warning(
                    'Using port forwarding with dynamic port allocation. '
                    f'SSH port: {self._ssh_port}'
                )
                # FIXME: This is a temporary workaround for Windows where host network mode has bugs.
                # FIXME: Docker Desktop for Mac OS has experimental support for host network mode
                # network_kwargs['ports'] = {f'{self._ssh_port}/tcp': self._ssh_port}
                # logger.warning(
                #     (
                #         'Using port forwarding till the enable host network mode of Docker is out of experimental mode.'
                #         'Check the 897th issue on https://github.com/OpenDevin/OpenDevin/issues/ for more information.'
                #     )
                # )

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
        except docker.errors.APIError as ex:
            if 'Ports are not available' in str(ex):
                logger.warning(
                    f'Port {self._ssh_port} is not available. Retrying with a new port.'
                )
                raise ex  # This will trigger a retry
            else:
                logger.exception(
                    'Failed to start container: ' + str(ex), exc_info=False
                )
                raise ex
        except Exception as ex:
            logger.exception('Failed to start container: ' + str(ex), exc_info=False)
            raise ex

        # wait for container to be ready
        await self.wait_for_container_ready()

    async def wait_for_container_ready(self):
        max_attempts = 30
        for attempt in range(max_attempts):
            try:
                container_info = self.docker_client.containers.get(self.container_name)
                if container_info.status == 'running':
                    logger.info('Container is running')
                    return
                if container_info.status == 'exited':
                    logger.error('Container exited unexpectedly')
                    logs = container_info.logs()
                    logger.error(f'Container logs: {logs.decode("utf-8")}')
                    raise RuntimeError('Container exited unexpectedly')
            except docker.errors.NotFound:
                logger.warning('Container not found, waiting...')

            await asyncio.sleep(1)
            logger.info(
                f'Waiting for container to start (attempt {attempt + 1}/{max_attempts})'
            )

        raise RuntimeError('Failed to start container within the timeout period')

    # clean up the container, cannot do it in __del__ because the python interpreter is already shutting down
    @async_to_sync
    def close(self):
        return self.aclose()

    async def aclose(self):
        if self._cleanup_done:
            return

        try:
            if hasattr(self, 'docker_client'):
                for container in self.docker_client.containers.list(all=True):
                    if container.name.startswith(self.container_name):
                        if config.persist_sandbox:
                            container.stop()
                        else:
                            container.remove(force=True)

                # Close the Docker client
                if hasattr(self.docker_client, 'close'):
                    self.docker_client.close()
        except Exception as e:
            logger.error(f'Error during cleanup: {e}')
        finally:
            self._cleanup_done = True

    def sync_cleanup(self):
        if self._cleanup_done:
            return

        try:
            if hasattr(self, 'docker_client'):
                for container in self.docker_client.containers.list(all=True):
                    if container.name.startswith(self.container_name):
                        try:
                            if config.persist_sandbox:
                                container.stop()
                            else:
                                container.remove(force=True)
                        except docker.errors.NotFound:
                            pass
                        except Exception as e:
                            logger.error(f'Error during container cleanup: {e}')

                # Close the Docker client
                if hasattr(self.docker_client, 'close'):
                    self.docker_client.close()
        except Exception as e:
            logger.error(f'Error during sync cleanup: {e}')
        finally:
            self._cleanup_done = True

    def __del__(self):
        if hasattr(self, '_cleanup_done') and not self._cleanup_done:
            self.sync_cleanup()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.aclose()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.sync_cleanup()


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
    plugins = [AgentSkillsRequirement(), JupyterRequirement()]
    ssh_box.init_plugins(plugins)
    logger.info(
        '--- AgentSkills COMMAND DOCUMENTATION ---\n'
        f'{AgentSkillsRequirement().documentation}\n'
        '---'
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
            exit_code, output = ssh_box.execute(user_input)
            logger.info('exit code: %d', exit_code)
            logger.info(output)
            sys.stdout.flush()
    except KeyboardInterrupt:
        logger.info('Exiting...')
    ssh_box.close()
