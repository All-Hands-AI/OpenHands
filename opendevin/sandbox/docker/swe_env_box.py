import atexit
import os
import sys
import time
import uuid
from glob import glob
from collections import namedtuple
from typing import Dict, List, Tuple, Union

import docker

from opendevin import config
from opendevin.logger import opendevin_logger as logger
from opendevin.sandbox.docker.ssh_box import DockerSSHBox
from opendevin.schema import ConfigType
from opendevin.utils import find_available_tcp_port

InputType = namedtuple('InputType', ['content'])
OutputType = namedtuple('OutputType', ['content'])

SANDBOX_WORKSPACE_DIR = config.get(ConfigType.WORKSPACE_MOUNT_PATH_IN_SANDBOX)

CONTAINER_IMAGE = config.get(ConfigType.SANDBOX_CONTAINER_IMAGE)

SSH_HOSTNAME = config.get(ConfigType.SSH_HOSTNAME)

USE_HOST_NETWORK = config.get(ConfigType.USE_HOST_NETWORK)

# FIXME: On some containers, the devin user doesn't have enough permission, e.g. to install packages
# How do we make this more flexible?
RUN_AS_DEVIN = config.get(ConfigType.RUN_AS_DEVIN).lower() != 'false'
USER_ID = 1000
if SANDBOX_USER_ID := config.get(ConfigType.SANDBOX_USER_ID):
    USER_ID = int(SANDBOX_USER_ID)
elif hasattr(os, 'getuid'):
    USER_ID = os.getuid()

class SWEEnvSSHBox(DockerSSHBox):
    
    def __init__(
        self,
        container_image: str | None = None,
        timeout: int = 120,
        sid: str | None = None,
        swe_instance_id: str | None = None,
        od_swe_bench_dir: str | None = None,
        conda_envs_dir: str | None = None,
    ):
        # Initialize docker client. Throws an exception if Docker is not reachable.
        try:
            self.docker_client = docker.from_env()
        except Exception as ex:
            logger.exception(
                'Please check Docker is running using `docker ps`.', exc_info=False)
            raise ex

        self.instance_id = sid if sid is not None else str(uuid.uuid4())

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

        if swe_instance_id is None:
            raise ValueError("swe_instance_id cannot be None")
        if od_swe_bench_dir is None:
            raise ValueError("od_swe_bench_dir cannot be None")
        if conda_envs_dir is None:
            raise ValueError("conda_envs_dir cannot be None")
        self.swe_instance_id = swe_instance_id
        self.od_swe_bench_dir = od_swe_bench_dir
        self.conda_envs_dir = conda_envs_dir

        # always restart the container, cuz the initial be regarded as a new session
        self.restart_docker_container()

        self.setup_user()
        self.start_ssh_session()
        
        exit_code, output = self.execute(f"echo 'SWEUTIL_DIR=/swe_util' >> ~/.bashrc && " + \
            f"echo 'export SWE_INSTANCE_ID={self.swe_instance_id}' >> ~/.bashrc && " + \
            f"echo 'export CACHE_DIR={self.tgt_cache_dir}' >> ~/.bashrc")
        logger.info('exit code: %d', exit_code)
        logger.info(output)

        exit_code, output = self.execute(f"{SANDBOX_WORKSPACE_DIR}/swe_env_setup.sh")
        logger.info('exit code: %d', exit_code)
        logger.info(output)

        # source the bashrc
        exit_code, output = self.execute('source ~/.bashrc')
        if exit_code != 0:
            raise RuntimeError(f'Failed to source ~/.bashrc with exit code {exit_code} and output {output}')
        logger.info('Sourced ~/.bashrc successfully')
        
        atexit.register(self.close)
        

    def restart_docker_container(self):
        try:
            self.stop_docker_container()
            logger.info('Container stopped')
        except docker.errors.DockerException as ex:
            logger.exception('Failed to stop container', exc_info=False)
            raise ex

        try:
            network_kwargs: Dict[str, Union[str, Dict[str, int]]] = {}
            if USE_HOST_NETWORK:
                network_kwargs['network_mode'] = 'host'
            else:
                # FIXME: This is a temporary workaround for Mac OS
                network_kwargs['ports'] = {f'{self._ssh_port}/tcp': self._ssh_port}
                logger.warning(
                    ('Using port forwarding for Mac OS. '
                     'Server started by OpenDevin will not be accessible from the host machine at the moment. '
                     'See https://github.com/OpenDevin/OpenDevin/issues/897 for more information.'
                     )
                )

            mount_dir = config.get(ConfigType.WORKSPACE_MOUNT_PATH)
            self.tgt_cache_dir = '/home/opendevin/.cache' if RUN_AS_DEVIN else '/root/.cache'
            logger.info(f'Mounting workspace directory: {mount_dir}')
            # start the container
            self.container = self.docker_client.containers.run(
                self.container_image,
                # allow root login
                command=f"/usr/sbin/sshd -D -p {self._ssh_port} -o 'PermitRootLogin=yes'",
                **network_kwargs,
                working_dir=SANDBOX_WORKSPACE_DIR,
                name=self.container_name,
                hostname='opendevin_sandbox',
                detach=True,
                volumes={
                    mount_dir: {
                        'bind': SANDBOX_WORKSPACE_DIR,
                        'mode': 'rw'
                    },
                    # mount cache directory to /home/opendevin/.cache for pip cache reuse
                    config.get(ConfigType.CACHE_DIR): {
                        'bind': self.tgt_cache_dir,
                        'mode': 'rw'
                    },
                    self.od_swe_bench_dir: {
                        'bind': '/swe_util/OD-SWE-bench',
                        'mode': 'ro'
                    },
                    self.conda_envs_dir: {
                        'bind': '/swe_util/conda_envs',
                        'mode': 'ro'
                    },
                },
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


if __name__ == '__main__':

    try:
        ssh_box = SWEEnvSSHBox(swe_instance_id="django__django-11099",
                               od_swe_bench_dir="/shared/bowen/codellm/swe/OD-SWE-bench",
                               conda_envs_dir="/shared/bowen/codellm/swe/temp/conda_envs")
    except Exception as e:
        logger.exception('Failed to start Docker container: %s', e)
        sys.exit(1)

    logger.info(
        "Interactive Docker container started. Type 'exit' or use Ctrl+C to exit.")

    bg_cmd = ssh_box.execute_in_background(
        "while true; do echo 'dot ' && sleep 10; done"
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