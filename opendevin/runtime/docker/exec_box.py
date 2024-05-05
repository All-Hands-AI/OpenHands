import atexit
import concurrent.futures
import os
import sys
import tarfile
import time
import uuid
from collections import namedtuple
from glob import glob
from typing import Dict, List, Tuple

import docker

from opendevin.const.guide_url import TROUBLESHOOTING_URL
from opendevin.core import config
from opendevin.core.exceptions import SandboxInvalidBackgroundCommandError
from opendevin.core.logger import opendevin_logger as logger
from opendevin.core.schema import ConfigType
from opendevin.runtime.docker.process import DockerProcess, Process
from opendevin.runtime.sandbox import Sandbox

InputType = namedtuple('InputType', ['content'])
OutputType = namedtuple('OutputType', ['content'])

CONTAINER_IMAGE = config.get(ConfigType.SANDBOX_CONTAINER_IMAGE)
SANDBOX_WORKSPACE_DIR = config.get(ConfigType.WORKSPACE_MOUNT_PATH_IN_SANDBOX)

# FIXME: On some containers, the devin user doesn't have enough permission, e.g. to install packages
# How do we make this more flexible?
RUN_AS_DEVIN = config.get(ConfigType.RUN_AS_DEVIN).lower() != 'false'
USER_ID = 1000
if SANDBOX_USER_ID := config.get(ConfigType.SANDBOX_USER_ID):
    USER_ID = int(SANDBOX_USER_ID)
elif hasattr(os, 'getuid'):
    USER_ID = os.getuid()


class DockerExecBox(Sandbox):
    instance_id: str
    container_image: str
    container_name_prefix = 'opendevin-sandbox-'
    container_name: str
    container: docker.models.containers.Container
    docker_client: docker.DockerClient

    cur_background_id = 0
    background_commands: Dict[int, Process] = {}

    def __init__(
        self,
        container_image: str | None = None,
        timeout: int = 120,
        sid: str | None = None,
    ):
        # Initialize docker client. Throws an exception if Docker is not reachable.
        try:
            self.docker_client = docker.from_env()
        except Exception as ex:
            logger.exception(
                f'Error creating controller. Please check Docker is running and visit `{TROUBLESHOOTING_URL}` for more debugging information.',
                exc_info=False,
            )
            raise ex

        self.instance_id = sid + str(uuid.uuid4()) if sid is not None else str(uuid.uuid4())

        # TODO: this timeout is actually essential - need a better way to set it
        # if it is too short, the container may still waiting for previous
        # command to finish (e.g. apt-get update)
        # if it is too long, the user may have to wait for a unnecessary long time
        self.timeout = timeout
        self.container_image = (
            CONTAINER_IMAGE if container_image is None else container_image
        )
        self.container_name = self.container_name_prefix + self.instance_id

        # always restart the container, cuz the initial be regarded as a new session
        self.restart_docker_container()

        if RUN_AS_DEVIN:
            self.setup_devin_user()
        atexit.register(self.close)

    def setup_devin_user(self):
        cmds = [
            f'useradd --shell /bin/bash -u {USER_ID} -o -c "" -m devin',
            r"echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers",
            'sudo adduser devin sudo',
        ]
        for cmd in cmds:
            exit_code, logs = self.container.exec_run(
                ['/bin/bash', '-c', cmd], workdir=SANDBOX_WORKSPACE_DIR
            )
            if exit_code != 0:
                raise Exception(f'Failed to setup devin user: {logs}')

    def get_exec_cmd(self, cmd: str) -> List[str]:
        if RUN_AS_DEVIN:
            return ['su', 'devin', '-c', cmd]
        else:
            return ['/bin/bash', '-c', cmd]

    def read_logs(self, id) -> str:
        if id not in self.background_commands:
            raise SandboxInvalidBackgroundCommandError()
        bg_cmd = self.background_commands[id]
        return bg_cmd.read_logs()

    def execute(self, cmd: str) -> Tuple[int, str]:
        # TODO: each execute is not stateful! We need to keep track of the current working directory
        def run_command(container, command):
            return container.exec_run(command, workdir=SANDBOX_WORKSPACE_DIR)

        # Use ThreadPoolExecutor to control command and set timeout
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(
                run_command, self.container, self.get_exec_cmd(cmd)
            )
            try:
                exit_code, logs = future.result(timeout=self.timeout)
            except concurrent.futures.TimeoutError:
                logger.exception(
                    'Command timed out, killing process...', exc_info=False
                )
                pid = self.get_pid(cmd)
                if pid is not None:
                    self.container.exec_run(
                        f'kill -9 {pid}', workdir=SANDBOX_WORKSPACE_DIR
                    )
                return -1, f'Command: "{cmd}" timed out'
        logs_out = logs.decode('utf-8')
        if logs_out.endswith('\n'):
            logs_out = logs_out[:-1]
        return exit_code, logs_out

    def copy_to(self, host_src: str, sandbox_dest: str, recursive: bool = False):
        # mkdir -p sandbox_dest if it doesn't exist
        exit_code, logs = self.container.exec_run(
            ['/bin/bash', '-c', f'mkdir -p {sandbox_dest}'],
            workdir=SANDBOX_WORKSPACE_DIR,
        )
        if exit_code != 0:
            raise Exception(
                f'Failed to create directory {sandbox_dest} in sandbox: {logs}'
            )

        if recursive:
            assert os.path.isdir(
                host_src
            ), 'Source must be a directory when recursive is True'
            files = glob(host_src + '/**/*', recursive=True)
            srcname = os.path.basename(host_src)
            tar_filename = os.path.join(os.path.dirname(host_src), srcname + '.tar')
            with tarfile.open(tar_filename, mode='w') as tar:
                for file in files:
                    tar.add(
                        file, arcname=os.path.relpath(file, os.path.dirname(host_src))
                    )
        else:
            assert os.path.isfile(
                host_src
            ), 'Source must be a file when recursive is False'
            srcname = os.path.basename(host_src)
            tar_filename = os.path.join(os.path.dirname(host_src), srcname + '.tar')
            with tarfile.open(tar_filename, mode='w') as tar:
                tar.add(host_src, arcname=srcname)

        with open(tar_filename, 'rb') as f:
            data = f.read()

        self.container.put_archive(os.path.dirname(sandbox_dest), data)
        os.remove(tar_filename)

    def execute_in_background(self, cmd: str) -> Process:
        result = self.container.exec_run(
            self.get_exec_cmd(cmd), socket=True, workdir=SANDBOX_WORKSPACE_DIR
        )
        result.output._sock.setblocking(0)
        pid = self.get_pid(cmd)
        bg_cmd = DockerProcess(self.cur_background_id, cmd, result, pid)
        self.background_commands[bg_cmd.pid] = bg_cmd
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

    def kill_background(self, id: int) -> Process:
        if id not in self.background_commands:
            raise SandboxInvalidBackgroundCommandError()
        bg_cmd = self.background_commands[id]
        if bg_cmd.pid is not None:
            self.container.exec_run(
                f'kill -9 {bg_cmd.pid}', workdir=SANDBOX_WORKSPACE_DIR
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
        except docker.errors.DockerException as e:
            logger.exception('Failed to stop container', exc_info=False)
            raise e

        try:
            # start the container
            mount_dir = config.get(ConfigType.WORKSPACE_MOUNT_PATH)
            self.container = self.docker_client.containers.run(
                self.container_image,
                command='tail -f /dev/null',
                network_mode='host',
                working_dir=SANDBOX_WORKSPACE_DIR,
                name=self.container_name,
                detach=True,
                volumes={mount_dir: {'bind': SANDBOX_WORKSPACE_DIR, 'mode': 'rw'}},
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

    def get_working_directory(self):
        return SANDBOX_WORKSPACE_DIR


if __name__ == '__main__':
    try:
        exec_box = DockerExecBox()
    except Exception as e:
        logger.exception('Failed to start Docker container: %s', e)
        sys.exit(1)

    logger.info(
        "Interactive Docker container started. Type 'exit' or use Ctrl+C to exit."
    )

    bg_cmd = exec_box.execute_in_background(
        "while true; do echo -n '.' && sleep 1; done"
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
                exec_box.kill_background(bg_cmd.pid)
                logger.info('Background process killed')
                continue
            exit_code, output = exec_box.execute(user_input)
            logger.info('exit code: %d', exit_code)
            logger.info(output)
            if bg_cmd.pid in exec_box.background_commands:
                logs = exec_box.read_logs(bg_cmd.pid)
                logger.info('background logs: %s', logs)
            sys.stdout.flush()
    except KeyboardInterrupt:
        logger.info('Exiting...')
    exec_box.close()
