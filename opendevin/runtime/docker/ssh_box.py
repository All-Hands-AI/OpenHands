import atexit
import os
import re
import sys
import tarfile
import tempfile
import time
import uuid
from glob import glob

import docker
from pexpect import exceptions, pxssh
from tenacity import retry, stop_after_attempt, wait_fixed

from opendevin.core.config import SandboxConfig
from opendevin.core.const.guide_url import TROUBLESHOOTING_URL
from opendevin.core.logger import opendevin_logger as logger
from opendevin.core.schema import CancellableStream
from opendevin.runtime.plugins import AgentSkillsRequirement, JupyterRequirement
from opendevin.runtime.plugins.requirement import PluginRequirement
from opendevin.runtime.sandbox import Sandbox
from opendevin.runtime.utils import find_available_tcp_port, split_bash_commands
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


class DockerSSHBox(Sandbox):
    instance_id: str
    container_image: str
    container_name_prefix = 'opendevin-sandbox-'
    container_name: str
    container: docker.models.containers.Container
    docker_client: docker.DockerClient

    _ssh_password: str
    _ssh_port: int
    ssh: pxssh.pxssh | None = None

    def __init__(
        self,
        config: SandboxConfig,
        persist_sandbox: bool,
        workspace_mount_path: str,
        sandbox_workspace_dir: str,
        cache_dir: str,
        run_as_devin: bool,
        ssh_hostname: str = 'host.docker.internal',
        ssh_password: str | None = None,
        ssh_port: int = 22,
        sid: str | None = None,
    ):
        self.config = config
        self.workspace_mount_path = workspace_mount_path
        self.sandbox_workspace_dir = sandbox_workspace_dir
        self.cache_dir = cache_dir
        self.use_host_network = config.use_host_network
        self.run_as_devin = run_as_devin
        logger.info(
            f'SSHBox is running as {"opendevin" if self.run_as_devin else "root"} user with USER_ID={config.user_id} in the sandbox'
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

        if persist_sandbox:
            if not self.run_as_devin:
                raise Exception(
                    'Persistent sandbox is currently designed for opendevin user only. Please set run_as_devin=True in your config.toml'
                )
            self.instance_id = 'persisted'
        else:
            self.instance_id = (sid or '') + str(uuid.uuid4())

        self.container_image = get_od_sandbox_image(
            config.container_image, self.docker_client
        )
        self.container_name = self.container_name_prefix + self.instance_id

        # set up random user password
        self.persist_sandbox = persist_sandbox
        self.ssh_hostname = ssh_hostname
        if persist_sandbox:
            if not ssh_password:
                raise ValueError('ssh_password is required for persistent sandbox')
            self._ssh_password = ssh_password
            self._ssh_port = ssh_port
        else:
            self._ssh_password = str(uuid.uuid4())
            self._ssh_port = find_available_tcp_port()
        try:
            docker.DockerClient().containers.get(self.container_name)
            self.is_initial_session = False
        except docker.errors.NotFound:
            self.is_initial_session = True
            logger.info('Detected initial session.')
        if not persist_sandbox or self.is_initial_session:
            logger.info('Creating new Docker container')
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
        else:
            self.container = self.docker_client.containers.get(self.container_name)
            logger.info('Using existing Docker container')
            self.start_docker_container()
        try:
            self.start_ssh_session()
        except Exception as e:
            self.close()
            raise e
        time.sleep(1)

        # make sure /tmp always exists
        self.execute('mkdir -p /tmp')
        # set git config
        self.execute('git config --global user.name "OpenDevin"')
        self.execute('git config --global user.email "opendevin@all-hands.dev"')
        atexit.register(self.close)
        super().__init__(config)

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
                    f'useradd -rm -d /home/opendevin -s /bin/bash -g root -G sudo -u {self.config.user_id} opendevin',
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
            # check the miniforge3 directory exist
            exit_code, logs = self.container.exec_run(
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
                    raise Exception(
                        'OPENDEVIN_PYTHON_INTERPRETER is not usable. Please pull the latest Docker image: docker pull ghcr.io/opendevin/sandbox:main'
                    )
                else:
                    raise Exception(
                        f'An error occurred while checking if miniforge3 directory exists: {logs}'
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
                timeout=self.config.timeout,
                encoding='utf-8',
                codec_errors='replace',
            )
            hostname = self.ssh_hostname
            username = 'opendevin' if self.run_as_devin else 'root'
            if self.persist_sandbox:
                password_msg = 'using your SSH password'
            else:
                password_msg = f"using the password '{self._ssh_password}'"
            logger.info('Connecting to SSH session...')
            hostname_to_log = hostname.replace('host.docker.internal', 'localhost')
            ssh_cmd = f'`ssh -v -p {self._ssh_port} {username}@{hostname_to_log}`'
            logger.info(
                f'You can debug the SSH connection by running: {ssh_cmd} {password_msg}'
            )
            self.ssh.login(hostname, username, self._ssh_password, port=self._ssh_port)
            logger.info('Connected to SSH session')
        except pxssh.ExceptionPxssh as e:
            logger.exception(
                'Failed to login to SSH session, retrying...', exc_info=False
            )
            raise e

    def start_ssh_session(self):
        time.sleep(1)
        self.__ssh_login()
        assert self.ssh is not None

        # Fix: https://github.com/pexpect/pexpect/issues/669
        self.ssh.sendline("bind 'set enable-bracketed-paste off'")
        self.ssh.prompt()
        time.sleep(1)

        # cd to workspace
        self.ssh.sendline(f'cd {self.sandbox_workspace_dir}')
        self.ssh.prompt()

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
    ) -> tuple[int, str]:
        assert self.ssh is not None
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
        assert self.ssh is not None
        timeout = timeout or self.config.timeout
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
            return 0, SSHExecCancellableStream(self.ssh, cmd, self.config.timeout)
        success = self.ssh.prompt(timeout=timeout)
        if not success:
            return self._send_interrupt(cmd)
        command_output = self.ssh.before

        # once out, make sure that we have *every* output, we while loop until we get an empty output
        while True:
            self.ssh.sendline('\n')
            timeout_not_reached = self.ssh.prompt(timeout=1)
            if not timeout_not_reached:
                logger.debug('TIMEOUT REACHED')
                break
            output = self.ssh.before
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
            if time.time() - _start_time > timeout:
                return self._send_interrupt(
                    cmd, command_output, ignore_last_output=True
                )
        cleaned_exit_code_str = exit_code_str.replace('echo $?', '').strip().split()[0]

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

    def start_docker_container(self):
        try:
            container = self.docker_client.containers.get(self.container_name)
            logger.info('Container status: %s', container.status)
            if container.status != 'running':
                container.start()
                logger.info('Container started')
            elapsed = 0
            while container.status != 'running':
                time.sleep(1)
                elapsed += 1
                if elapsed > self.config.timeout:
                    break
                container = self.docker_client.containers.get(self.container_name)
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
                time.sleep(1)
                elapsed += 1
                if elapsed > self.config.timeout:
                    break
                container = self.docker_client.containers.get(self.container_name)
        except docker.errors.NotFound:
            pass

    def get_working_directory(self):
        exit_code, result = self.execute('pwd')
        if exit_code != 0:
            raise Exception('Failed to get working directory')
        return str(result).strip()

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
        mount_dir = self.workspace_mount_path
        return {
            mount_dir: {'bind': self.sandbox_workspace_dir, 'mode': 'rw'},
            # mount cache directory to /home/opendevin/.cache for pip cache reuse
            self.cache_dir: {
                'bind': (
                    '/home/opendevin/.cache' if self.run_as_devin else '/root/.cache'
                ),
                'mode': 'rw',
            },
        }

    def restart_docker_container(self):
        try:
            self.remove_docker_container()
        except docker.errors.DockerException as ex:
            logger.exception('Failed to remove container', exc_info=False)
            raise ex

        try:
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
            logger.exception('Failed to start container: ' + str(ex), exc_info=False)
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
            if elapsed > self.config.timeout:
                break
        if self.container.status != 'running':
            raise Exception('Failed to start container')

    # clean up the container, cannot do it in __del__ because the python interpreter is already shutting down
    def close(self):
        containers = self.docker_client.containers.list(all=True)
        for container in containers:
            try:
                if container.name.startswith(self.container_name):
                    if self.persist_sandbox:
                        container.stop()
                    else:
                        # only remove the container we created
                        # otherwise all other containers with the same prefix will be removed
                        # which will mess up with parallel evaluation
                        container.remove(force=True)
            except docker.errors.NotFound:
                pass
        self.docker_client.close()


if __name__ == '__main__':
    try:
        ssh_box = DockerSSHBox(
            config=SandboxConfig(),
            run_as_devin=False,
            workspace_mount_path='/path/to/workspace',
            cache_dir='/path/to/cache',
            sandbox_workspace_dir='/sandbox',
            persist_sandbox=False,
        )
    except Exception as e:
        logger.exception('Failed to start Docker container: %s', e)
        sys.exit(1)

    logger.info(
        "Interactive Docker container started. Type 'exit' or use Ctrl+C to exit."
    )

    # Initialize required plugins
    plugins: list[PluginRequirement] = [AgentSkillsRequirement(), JupyterRequirement()]
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
