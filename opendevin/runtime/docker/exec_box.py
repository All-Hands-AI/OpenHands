import atexit
import os
import shlex
import sys
import tarfile
import time
import uuid
from collections import namedtuple
from glob import glob

import docker

from opendevin.core.config import config
from opendevin.core.const.guide_url import TROUBLESHOOTING_URL
from opendevin.core.exceptions import SandboxInvalidBackgroundCommandError
from opendevin.core.logger import opendevin_logger as logger
from opendevin.core.schema import CancellableStream
from opendevin.runtime.docker.process import DockerProcess, Process
from opendevin.runtime.sandbox import Sandbox

# FIXME these are not used, should we remove them?
InputType = namedtuple('InputType', ['content'])
OutputType = namedtuple('OutputType', ['content'])


ExecResult = namedtuple('ExecResult', 'exit_code,output')
""" A result of Container.exec_run with the properties ``exit_code`` and
    ``output``. """


class DockerExecCancellableStream(CancellableStream):
    # Reference: https://github.com/docker/docker-py/issues/1989
    def __init__(self, _client, _id, _output):
        super().__init__(self.read_output())
        self._id = _id
        self._client = _client
        self._output = _output

    def close(self):
        self.closed = True

    def exit_code(self):
        return self.inspect()['ExitCode']

    def inspect(self):
        return self._client.api.exec_inspect(self._id)

    def read_output(self):
        for chunk in self._output:
            yield chunk.decode('utf-8')


def container_exec_run(
    container,
    cmd,
    stdout=True,
    stderr=True,
    stdin=False,
    tty=False,
    privileged=False,
    user='',
    detach=False,
    stream=False,
    socket=False,
    environment=None,
    workdir=None,
) -> ExecResult:
    exec_id = container.client.api.exec_create(
        container.id,
        cmd,
        stdout=stdout,
        stderr=stderr,
        stdin=stdin,
        tty=tty,
        privileged=privileged,
        user=user,
        environment=environment,
        workdir=workdir,
    )['Id']

    output = container.client.api.exec_start(
        exec_id, detach=detach, tty=tty, stream=stream, socket=socket
    )

    if stream:
        return ExecResult(
            None, DockerExecCancellableStream(container.client, exec_id, output)
        )

    if socket:
        return ExecResult(None, output)

    return ExecResult(container.client.api.exec_inspect(exec_id)['ExitCode'], output)


class DockerExecBox(Sandbox):
    instance_id: str
    container_image: str
    container_name_prefix = 'opendevin-sandbox-'
    container_name: str
    container: docker.models.containers.Container
    docker_client: docker.DockerClient

    cur_background_id = 0
    background_commands: dict[int, Process] = {}

    def __init__(
        self,
        container_image: str | None = None,
        timeout: int = config.sandbox_timeout,
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

        self.instance_id = (
            sid + str(uuid.uuid4()) if sid is not None else str(uuid.uuid4())
        )

        # TODO: this timeout is actually essential - need a better way to set it
        # if it is too short, the container may still waiting for previous
        # command to finish (e.g. apt-get update)
        # if it is too long, the user may have to wait for a unnecessary long time
        self.timeout = timeout
        self.container_image = (
            config.sandbox_container_image
            if container_image is None
            else container_image
        )
        self.container_name = self.container_name_prefix + self.instance_id

        logger.info(
            'Starting Docker container with image %s, sandbox workspace dir=%s',
            self.container_image,
            self.sandbox_workspace_dir,
        )

        # always restart the container, cuz the initial be regarded as a new session
        self.restart_docker_container()

        if self.run_as_devin:
            self.setup_devin_user()
        atexit.register(self.close)
        super().__init__()

    def setup_devin_user(self):
        cmds = [
            f'useradd --shell /bin/bash -u {self.user_id} -o -c "" -m devin',
            r"echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers",
            'sudo adduser devin sudo',
        ]
        for cmd in cmds:
            exit_code, logs = self.container.exec_run(
                ['/bin/bash', '-c', cmd],
                workdir=self.sandbox_workspace_dir,
                environment=self._env,
            )
            if exit_code != 0:
                raise Exception(f'Failed to setup devin user: {logs}')

    def get_exec_cmd(self, cmd: str) -> list[str]:
        if self.run_as_devin:
            return ['su', 'devin', '-c', cmd]
        else:
            return ['/bin/bash', '-c', cmd]

    def read_logs(self, id) -> str:
        if id not in self.background_commands:
            raise SandboxInvalidBackgroundCommandError()
        bg_cmd = self.background_commands[id]
        return bg_cmd.read_logs()

    def execute(
        self, cmd: str, stream: bool = False, timeout: int | None = None
    ) -> tuple[int, str | CancellableStream]:
        timeout = timeout if timeout is not None else self.timeout
        wrapper = f'timeout {self.timeout}s bash -c {shlex.quote(cmd)}'
        _exit_code, _output = container_exec_run(
            self.container,
            wrapper,
            stream=stream,
            workdir=self.sandbox_workspace_dir,
            environment=self._env,
        )

        if stream:
            return _exit_code, _output

        print(_output)
        _output = _output.decode('utf-8')
        if _output.endswith('\n'):
            _output = _output[:-1]
        return _exit_code, _output

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
            mount_dir = config.workspace_mount_path
            self.container = self.docker_client.containers.run(
                self.container_image,
                command='tail -f /dev/null',
                network_mode='host',
                working_dir=self.sandbox_workspace_dir,
                name=self.container_name,
                detach=True,
                volumes={mount_dir: {'bind': self.sandbox_workspace_dir, 'mode': 'rw'}},
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
        return self.sandbox_workspace_dir

    @property
    def user_id(self):
        return config.sandbox_user_id

    @property
    def run_as_devin(self):
        # FIXME: On some containers, the devin user doesn't have enough permission, e.g. to install packages
        # How do we make this more flexible?
        return config.run_as_devin

    @property
    def sandbox_workspace_dir(self):
        return config.workspace_mount_path_in_sandbox


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
