import asyncio
import atexit
import json
import os
import re
import shlex
import sys
import tarfile
import tempfile
import time
import uuid
from glob import glob
from typing import Tuple, Union  # type: ignore[unused-import]

import aiodocker
from aiodocker.containers import Exec
from aiodocker.exceptions import DockerError
from pexpect import exceptions, pxssh
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
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
        assert self.ssh is not None
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
    container: aiodocker.containers.DockerContainer
    docker_client: aiodocker.Docker

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
        return self.ainit()

    async def ainit(self):
        if not self._sshbox_init_complete.is_set():
            async with self._initialization_lock:
                if not self._sshbox_init_complete.is_set():
                    logger.info(
                        'SSHBox is running as opendevin user with USER_ID=1000 in the sandbox'
                    )
                    try:
                        await self._setup_docker_client()
                        await self._setup_container()
                        await asyncio.sleep(2)
                        await self._setup_user_and_ssh()

                        self.initialized = True
                        logger.info('SSHBox initialization complete')
                        self._sshbox_init_complete.set()
                    except Exception as e:
                        logger.error(f'SSHBox initialization failed: {e}')
                        # Optionally, you might want to clean up any partially initialized resources here
                        await self.aclose()
                        raise
        else:
            await self._sshbox_init_complete.wait()

        if not self.initialized:
            raise RuntimeError('SSHBox initialization failed')

    async def _setup_docker_client(self):
        try:
            self.docker_client = aiodocker.Docker()
        except RuntimeError as ex:
            logger.exception(
                f'Error creating aiodocker client. Please check that Docker is running and visit `{TROUBLESHOOTING_URL}` for more debugging information.',
                exc_info=False,
            )
            raise ex

        self.container_image = await asyncio.to_thread(
            get_od_sandbox_image, self.container_image, self.docker_client
        )

    def format_env_value(self, value):
        if isinstance(value, str):
            # Use shlex.quote for strings to handle all special characters
            return shlex.quote(value)
        elif isinstance(value, (int, float, bool)):
            # Convert to string directly
            return str(value).lower()
        # Use JSON for complex types, then quote the result
        return shlex.quote(json.dumps(value))

    @async_to_sync
    def add_to_env(self, key: str, value: str):
        return self.add_to_env_async(key, value)

    async def add_to_env_async(self, key: str, value: str):
        formatted_value = self.format_env_value(value)

        # Set the environment variable in the SSH session
        self.send_line(f'export {key}={formatted_value}')
        self.ssh.prompt()

        # Verify that the environment variable was set
        self.send_line(f'echo ${key}')
        self.ssh.prompt()
        output = self.ssh.before.strip()

        if output == value:
            self._env[key] = value
            os.environ[key] = value
        else:
            raise RuntimeError(f'Failed to set environment variable {key}: {output}')

    async def run_command(self, command: str, use_os: Union[bool, None] = False):
        if use_os and os.environ.items():
            environment = dict(os.environ)
        elif self._env:
            environment = dict(self._env)
        else:
            environment = None
        return await self.container_exec_run(
            ['/bin/bash', '-c', command],
            environment=environment,
        )

    async def container_exec_run(
        self,
        cmd: Union[str, list[str]],
        workdir: Union[str, None] = None,
        environment: Union[dict[str, str], None] = None,
    ) -> Tuple[int, str]:
        """Executes a command in the container and returns the exit code and output.

        This method uses the aiodocker library's Exec class to execute a command
        within the Docker container. It waits for the command to complete and
        returns a tuple containing the exit code and the command's output.

        Args:
            cmd (Union[str, list[str]]): The command to execute. Can be a string
                or a list of strings.
            workdir (Union[str, None], optional): The working directory for the
                command. Defaults to None.
            environment (Union[dict[str, str], None], optional): Environment
                variables to set for the command. Defaults to None.

        Returns:
            Tuple[int, str]: A tuple containing the exit code and the command's
                output.
        """

        # Ensure the command is a list
        if isinstance(cmd, str):
            cmd = ['/bin/sh', '-c', cmd]

        # Create the exec instance
        exec_instance: Exec = await self.container.exec(
            cmd=cmd,
            stdout=True,
            stderr=True,
            workdir=workdir or self.sandbox_workspace_dir,
            environment=environment or dict(self._env) if self._env else None,
        )

        # Start the exec instance and collect the output
        output = b''
        async with exec_instance.start() as stream:
            while True:
                chunk = await stream.read_out()
                if chunk:
                    output += chunk.data
                    logger.debug(f'>>> {chunk.data!r}')  # Print the raw data
                else:
                    break

        # Get the exit code
        inspect_data = await exec_instance.inspect()
        exit_code = inspect_data.get('ExitCode')

        # Decode output, handling potential encoding errors
        try:
            decoded_output = output.decode('utf-8')
        except UnicodeDecodeError:
            # If UTF-8 decoding fails, try decoding with 'latin-1'
            decoded_output = output.decode('latin-1')

        return exit_code, decoded_output

    async def _setup_container(self):
        # Set up the Docker container
        try:
            self.container = await self.docker_client.containers.get(
                self.container_name
            )
            self.is_initial_session = False
        except DockerError:
            self.is_initial_session = True

        if not config.persist_sandbox or self.is_initial_session:
            await self._create_new_container()
        else:
            await self._use_existing_container()

    async def _create_new_container(self):
        logger.info('Creating new Docker container')
        try:
            await self.restart_docker_container()
        except DockerError as ex:
            if ex.status == 409 and 'is already in use by container' in str(ex):
                # Extract the conflicting container ID from the error message
                conflicting_container_id = ex.explanation.split('"')[1]
                logger.warning(
                    f'Removing conflicting container: {conflicting_container_id}'
                )
                await self.docker_client.containers.delete(
                    conflicting_container_id, force=True
                )
                await self.restart_docker_container()
            else:
                raise

    async def _use_existing_container(self):
        self.container = await self.docker_client.containers.get(self.container_name)
        logger.info('Using existing Docker container')
        await self.start_docker_container()

    async def _setup_environment(self):
        try:
            logger.info('Setting up sandbox vars')
            for key, value in self._env.items():
                if key.startswith('SANDBOX_ENV_'):
                    sandbox_key = key.removeprefix('SANDBOX_ENV_')
                    await self.add_to_env_async(sandbox_key, value)
                else:
                    await self.add_to_env_async(key, value)

            logger.info('Setting up tmp folder')
            self.send_line('mkdir -p /tmp')
            self.ssh.prompt()
            logger.info('Setting up git user')
            self.send_line('git config --global user.name "OpenDevin"')
            self.ssh.prompt()
            logger.info('Setting up git email')
            self.send_line('git config --global user.email "opendevin@all-hands.dev"')
            self.ssh.prompt()
        except Exception as e:
            logger.exception(f'Error during initialization: {e}')
            raise e
        logger.info('Environment setup complete')

    async def _setup_user(self):
        logger.info('Setting up user')
        # Make users sudoers passwordless
        # TODO(sandbox): add this line in the Dockerfile for next minor version of docker image
        result = await self.container_exec_run(
            ['/bin/bash', '-c', r"echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers"],
        )
        exit_code, logs = result
        if exit_code != 0:
            raise RuntimeError(
                f'Failed to make all users passwordless sudoers in sandbox: {logs}'
            )

        # Check if the opendevin user exists
        exit_code, logs = await self.container_exec_run(
            ['/bin/bash', '-c', 'id -u opendevin'],
        )
        if exit_code == 0 and 'no such user' not in logs:
            # User exists, delete it
            logger.info('Deleting existing opendevin user...')
            exit_code, logs = await self.container_exec_run(
                ['/bin/bash', '-c', 'userdel -r opendevin'],
            )
            if exit_code != 0:
                logger.error(f'Failed to remove opendevin user in sandbox: {logs}')
            else:
                logger.info('Successfully deleted existing opendevin user.')

        if self.run_as_devin:
            # The opendevin home folder is already part of the sandbox.
            # Just try to clear the logs folder here.
            exit_code, logs = await self.container_exec_run(
                ['/bin/bash', '-c', 'test -d /home/opendevin/logs'],
            )
            if exit_code == 0:
                logger.info('Deleting existing logs directory...')
                exit_code, logs = await self.container_exec_run(
                    ['/bin/bash', '-c', 'rm -rf /home/opendevin/logs'],  # 2>/dev/null
                )
                if exit_code != 0:
                    # This is not a fatal error, just a warning
                    logger.warning(
                        f'Failed to remove existing opendevin logs directory in sandbox: {logs}'
                    )

            # Create the opendevin user
            exit_code, logs = await self.container_exec_run(
                [
                    '/bin/bash',
                    '-c',
                    f'useradd -rm -d /home/opendevin -s /bin/bash -g root -G sudo -u {self.user_id} opendevin 2>/dev/null && id opendevin',
                ],
            )
            if exit_code != 0:
                raise RuntimeError(
                    f'Failed to create opendevin user in sandbox: {logs}'
                )

            exit_code, logs = await self.container_exec_run(
                [
                    '/bin/bash',
                    '-c',
                    f"echo 'opendevin:{self._ssh_password}' | chpasswd",
                ],
            )
            if exit_code != 0:
                raise RuntimeError(f'Failed to set password in sandbox: {logs}')

            # chown the home directory
            exit_code, logs = await self.container_exec_run(
                ['/bin/bash', '-c', 'chown opendevin:root /home/opendevin'],
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
            )
            if exit_code != 0:
                raise RuntimeError(
                    f'Failed to set password for root in sandbox: {logs}'
                )
        exit_code, logs = await self.container_exec_run(
            ['/bin/bash', '-c', "echo 'opendevin-sandbox' > /etc/hostname"],
        )

        # Add a check to ensure the user was created successfully
        exit_code, logs = await self.container_exec_run(
            ['/bin/bash', '-c', 'id opendevin'],
        )
        if exit_code != 0:
            raise RuntimeError(f'Failed to create or verify opendevin user: {logs}')

        logger.info('User setup in sandbox completed')
        await self._check_user_setup()

    async def _check_user_setup(self):
        """Checks if the user setup was successful by verifying user existence and permissions."""
        if self.run_as_devin:
            try:
                # Check if the user exists
                exit_code, logs = await self.container_exec_run(['id', 'opendevin'])
                if exit_code != 0:
                    raise RuntimeError(f'User "opendevin" does not exist: {logs}')

                # Check if the user is in the correct groups (sudo in this case)
                exit_code, logs = await self.container_exec_run(
                    ['/bin/bash', '-c', 'groups opendevin | grep sudo']
                )
                if exit_code != 0:
                    raise RuntimeError(
                        f'User "opendevin" is not in the sudo group: {logs}'
                    )

                logger.info('User setup verification successful.')

            except RuntimeError as e:
                logger.error(f'User setup verification failed: {e}')
                raise

    # Use the retry decorator, with a maximum of 5 attempts and a fixed wait time of 5 seconds between attempts
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(5),
        retry=retry_if_exception_type(pxssh.ExceptionPxssh),
    )
    async def _setup_ssh(self):
        try:
            await self.wait_for_ssh_ready()
            await asyncio.sleep(2)
            await self._ssh_login()
            await asyncio.sleep(2)
            await self.start_ssh_session()
            await asyncio.sleep(2)
            await self._setup_environment()
        except pxssh.ExceptionPxssh as e:
            logger.error(
                f'SSH session failed, attempting to restart container.\nError: {e}'
            )
            if not config.persist_sandbox:
                await self.remove_docker_container()
                await self.restart_container()
            raise

    async def _setup_user_and_ssh(self):
        await self._setup_user()
        await self._check_user_setup()
        retry_count = 0
        max_retries = 3
        while retry_count < max_retries:
            try:
                await self._setup_ssh()
                break
            except pxssh.ExceptionPxssh as e:
                retry_count += 1
                logger.warning(
                    f'SSH setup failed (attempt {retry_count}/{max_retries}): {e}'
                )
                if retry_count == max_retries:
                    raise RuntimeError('Failed to set up SSH after multiple attempts')
                await asyncio.sleep(5)

    async def wait_for_ssh_ready(self):
        max_attempts = 10
        for attempt in range(max_attempts):
            try:
                exit_code, _ = await self.container_exec_run(
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

    async def start_ssh_session(self):
        logger.info('Starting SSH session')
        # Fix: https://github.com/pexpect/pexpect/issues/669
        self.send_line("bind 'set enable-bracketed-paste off'")
        self.ssh.prompt()
        # cd to workspace
        self.send_line(f'cd {self.sandbox_workspace_dir}')
        self.ssh.prompt()
        logger.info('SSH session started')

    async def restart_container(self):
        logger.info('Restarting container...')
        await asyncio.sleep(1)
        await self._setup_container()
        await asyncio.sleep(1)
        await self._setup_user()
        await asyncio.sleep(1)
        logger.info('Container restarted successfully.')

    async def _ssh_login(self):
        try:
            if not hasattr(self, '_ssh_debug_logged'):
                hostname = self.ssh_hostname
                username = 'opendevin' if self.run_as_devin else 'root'
                if config.persist_sandbox:
                    password_msg = 'using your SSH password'
                else:
                    password_msg = f"using the password '{self._ssh_password}'"
                logger.info('Connecting to SSH session...')
                hostname_to_log = hostname.replace('host.docker.internal', 'localhost')
                ssh_cmd = f'`ssh -v -p {self._ssh_port} {username}@{hostname_to_log}`'
                logger.info(
                    f'You can debug the SSH connection by running: {ssh_cmd} {password_msg}'
                )
                self._ssh_debug_logged = True

            logger.info(
                f"Attempting SSH login to {self.ssh_hostname}:{self._ssh_port} as {'opendevin' if self.run_as_devin else 'root'}"
            )

            login_timeout = max(self.timeout, 20) if hasattr(self, 'timeout') else 60

            logger.info(' -> Creating pxssh instance')
            self.ssh = pxssh.pxssh(
                echo=False,
                timeout=login_timeout,
                encoding='utf-8',
                codec_errors='replace',
            )
            assert self.ssh is not None

            # Add this block before creating the container
            # try:
            #     await self.docker_client.images.get(self.container_image)
            # except DockerError as img_error:
            #     if img_error.status == 404:
            #         logger.warning(
            #             f'Image {self.container_image} not found. Attempting to pull...'
            #         )
            #         try:
            #             await self.docker_client.images.pull(self.container_image)
            #             logger.info(f'Successfully pulled image {self.container_image}')
            #         except DockerError as pull_error:
            #             logger.error(
            #                 f'Failed to pull image {self.container_image}: {pull_error}'
            #             )
            #             raise
            #     else:
            #         raise

            logger.info(f' -> Logging in to {self.ssh_hostname}...')
            self.ssh.login(
                self.ssh_hostname,
                'opendevin' if self.run_as_devin else 'root',
                self._ssh_password,
                port=self._ssh_port,
                login_timeout=login_timeout,
                quiet=False,
            )

            logger.info('Connected to SSH session')
        except pxssh.ExceptionPxssh as e:
            logger.exception(f'Login failed: {e}', exc_info=False)
            if 'connection refused' in str(e).lower():
                logger.error('SSH connection refused')
            raise e

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

    def send_line(self, cmd: str):
        if self.ssh is not None:
            self.ssh.sendline(cmd)

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
            await self.ainit()

        timeout = timeout or self.timeout
        timeout = 60 if timeout is None or int(timeout) < 60 else int(timeout)

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
            f'export {key}={self.format_env_value(value)}'
            for key, value in self._env.items()
        )
        if env_exports.strip():
            full_cmd = f'({env_exports}) && {cmd}'
        else:
            full_cmd = f'{cmd}'
        self.send_line(full_cmd)
        if stream:
            return 0, SSHExecCancellableStream(self.ssh, full_cmd, self.timeout)

        success = self.ssh.prompt(timeout=600)
        if not success:
            return self._send_interrupt(full_cmd)  # type: ignore
        command_output = self.ssh.before

        # once out, make sure that we have *every* output, we while loop until we get an empty output
        while True:
            self.send_line('\n')
            self.ssh.prompt(timeout=timeout)
            output = self.ssh.before
            if isinstance(output, str) and output.strip() == '':
                break
            command_output += output
        command_output = command_output.removesuffix('\r\n')

        # get the exit code
        self.send_line('echo $?')
        self.ssh.prompt()
        exit_code_str = self.ssh.before.strip()
        _start_time = time.time()
        while not exit_code_str:
            self.ssh.prompt(timeout=timeout)
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
            await self.container.put_archive(os.path.dirname(sandbox_dest), data)

    async def start_docker_container(self):
        try:
            container = await self.docker_client.containers.get(self.container_name)
            # if container['State']['Status'] != 'running':
            if container._container['State']['Status'] != 'running':
                await container.start()
                logger.info('Container started')
            await self.wait_for_container_ready()
        except Exception:
            logger.exception('Failed to start container')

    async def remove_docker_container(self):
        try:
            container = await self.docker_client.containers.get(self.container_name)
            if not container:
                return
            if await self.is_container_running():
                await container.stop()
                logger.info('Container stopped')
            try:
                await container.delete()
            except DockerError as e:
                if e.status == 404:
                    # If gone we don't care here
                    pass
                else:
                    raise

            # Wait for the container to be fully removed
            elapsed = 0
            while elapsed < self.timeout:
                try:
                    container_info = await container.show()
                    if container_info['State']['Status'] == 'exited':
                        break
                except DockerError:
                    # Container no longer exists
                    break
                await asyncio.sleep(2)
                elapsed += 2

            if elapsed >= self.timeout:
                logger.warning('Timeout waiting for container to be removed')
            else:
                logger.info('Container removed')
        except DockerError:
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
            if container._container['State']['Status'] == 'running':
                self.container = container
                return True
            return False
        except DockerError:
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

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(2),
        retry=retry_if_exception_type(DockerError),
    )
    async def restart_docker_container(self):
        try:
            # Attempt to find an existing container with the same name
            existing_container = await self.docker_client.containers.get(
                self.container_name
            )
        except DockerError as e:
            if e.status == 404:
                # Container not found, proceed with creation
                existing_container = None
            else:
                raise  # Re-raise other Docker errors

        try:
            if existing_container:
                logger.warning(f'Replacing existing container: {self.container_name}')
                await existing_container.delete(force=True)

            logger.info('Finding available port')
            self._ssh_port = find_available_tcp_port()
            logger.info(f'Using port {self._ssh_port}')
            network_kwargs: dict[str, str | dict[str, int]] = {}
            if self.use_host_network:
                network_kwargs['network_mode'] = 'host'
            else:
                # FIXME: This is a temporary workaround for Windows where host network mode has bugs.
                # FIXME: Docker Desktop for Mac OS has experimental support for host network mode
                network_kwargs['ports'] = {f'{self._ssh_port}/tcp': self._ssh_port}
                logger.warning(
                    (
                        'Using port forwarding till the enable host network mode of Docker is out of experimental mode.'
                        'Check the 897th issue on https://github.com/OpenDevin/OpenDevin/issues/ for more information.'
                    )
                )

            # start the container
            logger.info(f'Mounting volumes: {self.volumes}')
            container_config = {
                'Image': self.container_image,
                'Cmd': [
                    '/usr/sbin/sshd',
                    '-D',
                    '-p',
                    str(self._ssh_port),
                    '-o',
                    'PermitRootLogin=yes',
                ],
                'WorkingDir': self.sandbox_workspace_dir,
                'HostConfig': {
                    'NetworkMode': network_kwargs.get('network_mode'),
                    'PortBindings': {
                        str(self._ssh_port) + '/tcp': [
                            {'HostPort': str(self._ssh_port)}
                        ]
                    }
                    if 'ports' in network_kwargs
                    else {},
                    'Binds': [
                        f"{host}:{container['bind']}:rw"
                        for host, container in self.volumes.items()
                    ],
                },
            }

            # Use create_or_replace for idempotent container management
            logger.info('Waiting for container...')
            self.container = await self.docker_client.containers.create_or_replace(
                config=container_config,
                name=self.container_name,
            )
            assert self.container is not None
            self.container_id = self.container.id

            await asyncio.sleep(2)
            await self.container.start()
            logger.info('Container started')
        except DockerError as ex:
            if ex.status == 404:
                # If not found, it's a hard error!
                logger.error(f'{ex}')
                sys.exit(1)
            elif 'Ports are not available' in str(ex):
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

    async def wait_for_container_ready(self):
        max_attempts = 30
        for attempt in range(max_attempts):
            try:
                container_info = await self.docker_client.containers.get(
                    self.container_name
                )
                logger.info(
                    f"Container info: {container_info['State']}"
                )  # New debug line
                if container_info['State']['Status'] == 'running':
                    logger.info('Container is running')
                    return
                if container_info['State']['Status'] == 'exited':
                    logger.error('Container exited unexpectedly')
                    logs = await container_info.log(stdout=True, stderr=True)
                    logger.error(f'Container logs: {logs}')
                    raise RuntimeError('Container exited unexpectedly')
            except DockerError as e:
                logger.warning(f'Container not found, waiting...: {e}')

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
        await self._cleanup()

    def sync_cleanup(self):
        if self._cleanup_done:
            return
        asyncio.run(self._cleanup())

    async def _cleanup(self):
        try:
            if hasattr(self, 'docker_client'):
                containers = await self.docker_client.containers.list(all=True)
                for container in containers:
                    container_info = await container.show()
                    if container_info['Name'].startswith(f'/{self.container_name}'):
                        if config.persist_sandbox:
                            await container.stop()
                        else:
                            await container.delete(force=True)

                # Close the Docker client
                if hasattr(self.docker_client, 'close'):
                    await self.docker_client.close()
        except Exception as e:
            logger.error(f'Error during cleanup: {e}')
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
