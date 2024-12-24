import atexit
import functools
from typing import Dict, List, Optional

import docker
import requests
import tenacity

from openhands.core.config import AppConfig
from openhands.core.exceptions import (
    AgentRuntimeDisconnectedError,
    AgentRuntimeNotFoundError,
    AgentRuntimeNotReadyError,
    AgentRuntimeUnavailableError,
)
from openhands.core.logger import DEBUG
from openhands.core.logger import openhands_logger as logger
from openhands.events import EventStream
from openhands.runtime import get_runtime_cls
from openhands.runtime.base import Runtime
from openhands.runtime.builder import DockerRuntimeBuilder
from openhands.runtime.impl.eventstream.containers import remove_all_containers
from openhands.runtime.plugins import PluginRequirement, VSCodeRequirement
from openhands.runtime.utils import find_available_tcp_port
from openhands.runtime.utils.log_streamer import LogStreamer
from openhands.runtime.utils.request import send_request
from openhands.runtime.utils.singleton import Singleton
from openhands.utils.tenacity_stop import stop_if_should_exit

CONTAINER_NAME_PREFIX = 'openhands-runtime-'

_atexit_registered = False


class RuntimeManager(metaclass=Singleton):
    def __init__(self, config: AppConfig):
        global _atexit_registered
        if not _atexit_registered:
            _atexit_registered = True
            atexit.register(remove_all_containers, CONTAINER_NAME_PREFIX)

        self._runtimes: Dict[str, Runtime] = {}
        self._config = config
        self._docker_client = self._init_docker_client()
        self._runtime_builder = DockerRuntimeBuilder(self._docker_client)

    @property
    def config(self) -> AppConfig:
        return self._config

    @staticmethod
    @functools.lru_cache(maxsize=1)
    def _init_docker_client() -> docker.DockerClient:
        try:
            return docker.from_env()
        except Exception as ex:
            logger.error(
                'Launch docker client failed. Please make sure you have installed docker and started docker desktop/daemon.',
            )
            raise ex

    def _is_port_in_use_docker(self, port):
        containers = self._docker_client.containers.list()
        for container in containers:
            container_ports = container.ports
            if str(port) in str(container_ports):
                return True
        return False

    def _find_available_port(self, max_attempts=5):
        port = 39999
        for _ in range(max_attempts):
            port = find_available_tcp_port(30000, 39999)
            if not self._is_port_in_use_docker(port):
                return port
        return port

    def _initialize_container(
        self,
        runtime_container_image: str,
        container_name: str,
        container_port: int,
        plugins: Optional[List[PluginRequirement]] = None,
        env_vars: Optional[Dict[str, str]] = None,
        status_callback=None,
    ):
        logger.debug('Preparing to start container...')
        if status_callback:
            status_callback('info', 'STATUS$PREPARING_CONTAINER')

        plugin_arg = ''
        if plugins:
            plugin_arg = f'--plugins {" ".join([plugin.name for plugin in plugins])} '

        use_host_network = self.config.sandbox.use_host_network
        network_mode: str | None = 'host' if use_host_network else None

        port_mapping: dict[str, list[dict[str, str]]] | None = (
            None
            if use_host_network
            else {f'{container_port}/tcp': [{'HostPort': str(container_port)}]}
        )

        if use_host_network:
            logger.warn(
                'Using host network mode. If you are using MacOS, please make sure you have the latest version of Docker Desktop and enabled host network feature: https://docs.docker.com/network/drivers/host/#docker-desktop',
            )

        environment = {
            'port': str(container_port),
            'PYTHONUNBUFFERED': '1',
            **(env_vars or {}),
        }
        if self.config.debug or DEBUG:
            environment['DEBUG'] = 'true'

        if any(isinstance(plugin, VSCodeRequirement) for plugin in (plugins or [])):
            if isinstance(port_mapping, dict):
                port_mapping[f'{container_port + 1}/tcp'] = [
                    {'HostPort': str(container_port + 1)}
                ]

        logger.debug(f'Workspace Base: {self.config.workspace_base}')
        if (
            self.config.workspace_mount_path is not None
            and self.config.workspace_mount_path_in_sandbox is not None
        ):
            volumes = {
                self.config.workspace_mount_path: {
                    'bind': self.config.workspace_mount_path_in_sandbox,
                    'mode': 'rw',
                }
            }
            logger.debug(f'Mount dir: {self.config.workspace_mount_path}')
        else:
            logger.debug(
                'Mount dir is not set, will not mount the workspace directory to the container'
            )
            volumes = {}
        logger.debug(
            f'Sandbox workspace: {self.config.workspace_mount_path_in_sandbox}',
        )

        browsergym_arg = ''
        if self.config.sandbox.browsergym_eval_env is not None:
            browsergym_arg = (
                f'--browsergym-eval-env {self.config.sandbox.browsergym_eval_env}'
            )

        try:
            container = self._docker_client.containers.run(
                runtime_container_image,
                command=(
                    f'/openhands/micromamba/bin/micromamba run -n openhands '
                    f'poetry run '
                    f'python -u -m openhands.runtime.action_execution_server {container_port} '
                    f'--working-dir "{self.config.workspace_mount_path_in_sandbox}" '
                    f'{plugin_arg}'
                    f'--username {"openhands" if self.config.run_as_openhands else "root"} '
                    f'--user-id {self.config.sandbox.user_id} '
                    f'{browsergym_arg}'
                ),
                network_mode=network_mode,
                ports=port_mapping,
                working_dir='/openhands/code/',
                name=container_name,
                detach=True,
                environment=environment,
                volumes=volumes,
            )
            logger.debug(
                f'Container started. Server url: http://localhost:{container_port}'
            )
            if status_callback:
                status_callback('info', 'STATUS$CONTAINER_STARTED')
            return container

        except docker.errors.APIError as e:
            if '409' in str(e):
                logger.warning(
                    f'Container {container_name} already exists. Removing...',
                )
                remove_all_containers(container_name)
                return self._initialize_container(
                    runtime_container_image,
                    container_name,
                    container_port,
                    plugins,
                    env_vars,
                    status_callback,
                )
            else:
                logger.error(
                    f'Error: Instance {container_name} FAILED to start container!\n',
                )
                raise
        except Exception as e:
            logger.error(
                f'Error: Instance {container_name} FAILED to start container!\n',
            )
            logger.error(str(e))
            raise

    def _attach_to_container(self, container_name: str):
        container = self._docker_client.containers.get(container_name)
        container_port = 0
        for port in container.attrs['NetworkSettings']['Ports']:
            container_port = int(port.split('/')[0])
            break
        return container, container_port

    @tenacity.retry(
        stop=tenacity.stop_after_delay(120) | stop_if_should_exit(),
        retry=tenacity.retry_if_exception_type(
            (ConnectionError, requests.exceptions.ConnectionError)
        ),
        reraise=True,
        wait=tenacity.wait_fixed(2),
    )
    def _wait_until_alive(
        self,
        container_name: str,
        container_port: int,
        log_streamer: Optional[LogStreamer] = None,
    ):
        try:
            container = self._docker_client.containers.get(container_name)
            if container.status == 'exited':
                raise AgentRuntimeDisconnectedError(
                    f'Container {container_name} has exited.'
                )
        except docker.errors.NotFound:
            raise AgentRuntimeNotFoundError(f'Container {container_name} not found.')

        if not log_streamer:
            raise AgentRuntimeNotReadyError('Runtime client is not ready.')

        with send_request(
            requests.Session(),
            'GET',
            f'http://localhost:{container_port}/alive',
            timeout=5,
        ):
            pass

    async def create_runtime(
        self,
        event_stream: EventStream,
        sid: str,
        plugins: Optional[List[PluginRequirement]] = None,
        env_vars: Optional[Dict[str, str]] = None,
        status_callback=None,
        attach_to_existing: bool = False,
        headless_mode: bool = False,
    ) -> Runtime:
        if sid in self._runtimes:
            raise RuntimeError(f'Runtime with ID {sid} already exists')

        runtime_class = get_runtime_cls(self.config.runtime)
        logger.debug(f'Initializing runtime: {runtime_class.__name__}')
        runtime = runtime_class(
            config=self.config,
            event_stream=event_stream,
            sid=sid,
            plugins=plugins,
            env_vars=env_vars,
            status_callback=status_callback,
            attach_to_existing=attach_to_existing,
            headless_mode=headless_mode,
            runtime_manager=self,
        )

        try:
            await runtime.connect()
        except AgentRuntimeUnavailableError as e:
            logger.error(f'Runtime initialization failed: {e}', exc_info=True)
            if status_callback:
                status_callback('error', 'STATUS$ERROR_RUNTIME_DISCONNECTED', str(e))
            raise

        self._runtimes[sid] = runtime
        logger.info(f'Created runtime with ID: {sid}')
        return runtime

    def get_runtime(self, runtime_id: str) -> Optional[Runtime]:
        return self._runtimes.get(runtime_id)

    def list_runtimes(self) -> List[str]:
        return list(self._runtimes.keys())

    def destroy_runtime(self, runtime_id: str) -> bool:
        runtime = self._runtimes.get(runtime_id)
        if runtime:
            runtime.close()
            del self._runtimes[runtime_id]
            logger.info(f'Destroyed runtime with ID: {runtime_id}')
            return True
        return False

    async def destroy_all_runtimes(self):
        for runtime_id in list(self._runtimes.keys()):
            self.destroy_runtime(runtime_id)
