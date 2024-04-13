import atexit
import os
import platform
import sys
import time
import uuid
from collections import namedtuple
from typing import Dict, List, Tuple, Union

import docker
from pexpect import pxssh

from opendevin import config
from opendevin.logger import opendevin_logger as logger
from opendevin.sandbox.sandbox import Sandbox, BackgroundCommand
from opendevin.schema import ConfigType
from opendevin.utils import find_available_tcp_port

InputType = namedtuple('InputType', ['content'])
OutputType = namedtuple('OutputType', ['content'])

# helpful for docker-in-docker scenarios
DIRECTORY_REWRITE = config.get(ConfigType.DIRECTORY_REWRITE)
CONTAINER_IMAGE = config.get(ConfigType.SANDBOX_CONTAINER_IMAGE)

# FIXME: On some containers, the devin user doesn't have enough permission, e.g. to install packages
# How do we make this more flexible?
RUN_AS_DEVIN = config.get('RUN_AS_DEVIN').lower() != 'false'
USER_ID = 1000
if SANDBOX_USER_ID := config.get('SANDBOX_USER_ID'):
    USER_ID = int(SANDBOX_USER_ID)
elif hasattr(os, 'getuid'):
    USER_ID = os.getuid()


class DockerSSHBox(Sandbox):
    instance_id: str
    container_image: str
    container_name_prefix = 'opendevin-sandbox-'
    container_name: str
    container: docker.models.containers.Container
    docker_client: docker.DockerClient

    _ssh_password: str
    _ssh_port: int

    cur_background_id = 0
    background_commands: Dict[int, BackgroundCommand] = {}

    def __init__(
            self,
            workspace_dir: str | None = None,
            container_image: str | None = None,
            timeout: int = 120,
            sid: str | None = None,
    ):
        # Initialize docker client. Throws an exception if Docker is not reachable.
        try:
            self.docker_client = docker.from_env()
        except Exception as ex:
            logger.exception(
                'Please check Docker is running using `docker ps`.', exc_info=False)
            raise ex

        self.instance_id = sid if sid is not None else str(uuid.uuid4())
        if workspace_dir is not None:
            os.makedirs(workspace_dir, exist_ok=True)
            # expand to absolute path
            self.workspace_dir = os.path.abspath(workspace_dir)
        else:
            self.workspace_dir = os.getcwd()
            logger.info(
                'workspace unspecified, using current directory: %s', workspace_dir)
        if DIRECTORY_REWRITE != '':
            parts = DIRECTORY_REWRITE.split(':')
            self.workspace_dir = self.workspace_dir.replace(parts[0], parts[1])
            logger.info('Rewriting workspace directory to: %s',
                        self.workspace_dir)
        else:
            logger.info('Using workspace directory: %s', self.workspace_dir)

        # TODO: this timeout is actually essential - need a better way to set it
        # if it is too short, the container may still waiting for previous
        # command to finish (e.g. apt-get update)
        # if it is too long, the user may have to wait for a unnecessary long time
        self.timeout = timeout
        self.container_image = CONTAINER_IMAGE if container_image is None else container_image
        self.container_name = self.container_name_prefix + self.instance_id

        # set up random user password
        self._ssh_password = str(uuid.uuid4())
        self._ssh_port = find_available_tcp_port()

        # always restart the container, cuz the initial be regarded as a new session
        self.restart_docker_container()

        self.setup_user()
        self.start_ssh_session()
        atexit.register(self.close)

    def setup_user(self):

        # Make users sudoers passwordless
        # TODO(sandbox): add this line in the Dockerfile for next minor version of docker image
        exit_code, logs = self.container.exec_run(
            ['/bin/bash', '-c',
             r"echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers"],
            workdir='/workspace',
        )
        if exit_code != 0:
            raise Exception(
                f'Failed to make all users passwordless sudoers in sandbox: {logs}')

        # Check if the opendevin user exists
        exit_code, logs = self.container.exec_run(
            ['/bin/bash', '-c', 'id -u opendevin'],
            workdir='/workspace',
        )
        if exit_code == 0:
            # User exists, delete it
            exit_code, logs = self.container.exec_run(
                ['/bin/bash', '-c', 'userdel -r opendevin'],
                workdir='/workspace',
            )
            if exit_code != 0:
                raise Exception(
                    f'Failed to remove opendevin user in sandbox: {logs}')

        # Create the opendevin user
        exit_code, logs = self.container.exec_run(
            ['/bin/bash', '-c',
             f'useradd -rm -d /home/opendevin -s /bin/bash -g root -G sudo -u {USER_ID} opendevin'],
            workdir='/workspace',
        )
        if exit_code != 0:
            raise Exception(
                f'Failed to create opendevin user in sandbox: {logs}')
        exit_code, logs = self.container.exec_run(
            ['/bin/bash', '-c',
             f"echo 'opendevin:{self._ssh_password}' | chpasswd"],
            workdir='/workspace',
        )
        if exit_code != 0:
            raise Exception(f'Failed to set password in sandbox: {logs}')

        if not RUN_AS_DEVIN:
            exit_code, logs = self.container.exec_run(
                # change password for root
                ['/bin/bash', '-c',
                 f"echo 'root:{self._ssh_password}' | chpasswd"],
                workdir='/workspace',
            )
            if exit_code != 0:
                raise Exception(
                    f'Failed to set password for root in sandbox: {logs}')
        exit_code, logs = self.container.exec_run(
            ['/bin/bash', '-c', "echo 'opendevin-sandbox' > /etc/hostname"],
            workdir='/workspace',
        )

    def start_ssh_session(self):
        # start ssh session at the background
        self.ssh = pxssh.pxssh()
        hostname = 'localhost'
        if RUN_AS_DEVIN:
            username = 'opendevin'
        else:
            username = 'root'
        logger.info(
            # FIXME: mypy and autopep8 fight each other on this line
            # autopep8: off
            f"Connecting to {username}@{hostname} via ssh. If you encounter any issues, you can try `ssh -v -p {self._ssh_port} {username}@{hostname}` with the password '{self._ssh_password}' and report the issue on GitHub."
        )
        self.ssh.login(hostname, username, self._ssh_password, port=self._ssh_port)

        # Fix: https://github.com/pexpect/pexpect/issues/669
        self.ssh.sendline("bind 'set enable-bracketed-paste off'")
        self.ssh.prompt()
        # cd to workspace
        self.ssh.sendline('cd /workspace')
        self.ssh.prompt()

    def get_exec_cmd(self, cmd: str) -> List[str]:
        if RUN_AS_DEVIN:
            return ['su', 'opendevin', '-c', cmd]
        else:
            return ['/bin/bash', '-c', cmd]

    def read_logs(self, id) -> str:
        if id not in self.background_commands:
            raise ValueError('Invalid background command id')
        bg_cmd = self.background_commands[id]
        return bg_cmd.read_logs()

    def execute(self, cmd: str) -> Tuple[int, str]:
        # use self.ssh
        self.ssh.sendline(cmd)
        success = self.ssh.prompt(timeout=self.timeout)
        if not success:
            logger.exception(
                'Command timed out, killing process...', exc_info=False)
            # send a SIGINT to the process
            self.ssh.sendintr()
            self.ssh.prompt()
            command_output = self.ssh.before.decode(
                'utf-8').lstrip(cmd).strip()
            return -1, f'Command: "{cmd}" timed out. Sending SIGINT to the process: {command_output}'
        command_output = self.ssh.before.decode('utf-8').lstrip(cmd).strip()

        # get the exit code
        self.ssh.sendline('echo $?')
        self.ssh.prompt()
        exit_code = self.ssh.before.decode('utf-8')
        # remove the echo $? itself
        exit_code = int(exit_code.lstrip('echo $?').strip())
        return exit_code, command_output

    def execute_in_background(self, cmd: str) -> BackgroundCommand:
        result = self.container.exec_run(
            self.get_exec_cmd(cmd), socket=True, workdir='/workspace'
        )
        result.output._sock.setblocking(0)
        pid = self.get_pid(cmd)
        bg_cmd = BackgroundCommand(self.cur_background_id, cmd, result, pid)
        self.background_commands[bg_cmd.id] = bg_cmd
        self.cur_background_id += 1
        return bg_cmd

    def get_pid(self, cmd):
        exec_result = self.container.exec_run('ps aux')
        processes = exec_result.output.decode('utf-8').splitlines()
        cmd = ' '.join(self.get_exec_cmd(cmd))

        for process in processes:
            if cmd in process:
                pid = process.split()[1]  # second column is the pid
                return pid
        return None

    def kill_background(self, id: int) -> BackgroundCommand:
        if id not in self.background_commands:
            raise ValueError('Invalid background command id')
        bg_cmd = self.background_commands[id]
        if bg_cmd.pid is not None:
            self.container.exec_run(
                f'kill -9 {bg_cmd.pid}', workdir='/workspace')
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
                container = self.docker_client.containers.get(
                    self.container_name)
        except docker.errors.NotFound:
            pass

    def is_container_running(self):
        try:
            container = self.docker_client.containers.get(self.container_name)
            if container.status == 'running':
                self.container = container
                return True
            return False
        except docker.errors.NotFound:
            return False

    def restart_docker_container(self):
        try:
            self.stop_docker_container()
            logger.info('Container stopped')
        except docker.errors.DockerException as ex:
            logger.exception('Failed to stop container', exc_info=False)
            raise ex

        try:
            network_kwargs: Dict[str, Union[str, Dict[str, int]]] = {}
            if platform.system() == 'Linux':
                network_kwargs['network_mode'] = 'host'
            elif platform.system() == 'Darwin':
                # FIXME: This is a temporary workaround for Mac OS
                network_kwargs['ports'] = {'2222/tcp': self._ssh_port}
                logger.warning(
                    ('Using port forwarding for Mac OS. '
                     'Server started by OpenDevin will not be accessible from the host machine at the moment. '
                     'See https://github.com/OpenDevin/OpenDevin/issues/897 for more information.'
                     )
                )

            # start the container
            self.container = self.docker_client.containers.run(
                self.container_image,
                # allow root login
                command="/usr/sbin/sshd -D -p 2222 -o 'PermitRootLogin=yes'",
                **network_kwargs,
                working_dir='/workspace',
                name=self.container_name,
                hostname='opendevin_sandbox',
                detach=True,
                volumes={self.workspace_dir: {
                    'bind': '/workspace', 'mode': 'rw'}},
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
            self.container = self.docker_client.containers.get(
                self.container_name)
            logger.info(
                f'waiting for container to start: {elapsed}, container status: {self.container.status}')
            if elapsed > self.timeout:
                break
        if self.container.status != 'running':
            raise Exception('Failed to start container')

    # clean up the container, cannot do it in __del__ because the python interpreter is already shutting down
    def close(self):
        containers = self.docker_client.containers.list(all=True)
        for container in containers:
            try:
                if container.name.startswith(self.container_name_prefix):
                    container.remove(force=True)
            except docker.errors.NotFound:
                pass


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Interactive Docker container')
    parser.add_argument(
        '-d',
        '--directory',
        type=str,
        default=None,
        help='The directory to mount as the workspace in the Docker container.',
    )
    args = parser.parse_args()

    try:
        ssh_box = DockerSSHBox(
            workspace_dir=args.directory,
        )
    except Exception as e:
        logger.exception('Failed to start Docker container: %s', e)
        sys.exit(1)

    logger.info(
        "Interactive Docker container started. Type 'exit' or use Ctrl+C to exit.")

    bg_cmd = ssh_box.execute_in_background(
        "while true; do echo 'dot ' && sleep 1; done"
    )

    sys.stdout.flush()
    try:
        while True:
            try:
                user_input = input('>>> ')
            except EOFError:
                logger.info('Exiting...')
                break
            if user_input.lower() == 'exit':
                logger.info('Exiting...')
                break
            if user_input.lower() == 'kill':
                ssh_box.kill_background(bg_cmd.id)
                logger.info('Background process killed')
                continue
            exit_code, output = ssh_box.execute(user_input)
            logger.info('exit code: %d', exit_code)
            logger.info(output)
            if bg_cmd.id in ssh_box.background_commands:
                logs = ssh_box.read_logs(bg_cmd.id)
                logger.info('background logs: %s', logs)
            sys.stdout.flush()
    except KeyboardInterrupt:
        logger.info('Exiting...')
    ssh_box.close()
