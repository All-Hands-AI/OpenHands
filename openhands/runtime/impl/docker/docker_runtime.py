import atexit
from functools import lru_cache
from typing import Callable

import docker
import requests
import tenacity

from openhands.core.config import AppConfig
from openhands.core.exceptions import (
    AgentRuntimeDisconnectedError,
    AgentRuntimeNotFoundError,
    AgentRuntimeNotReadyError,
)
from openhands.core.logger import DEBUG
from openhands.core.logger import openhands_logger as logger
from openhands.events import EventStream
from openhands.runtime.builder import DockerRuntimeBuilder
from openhands.runtime.impl.action_execution.action_execution_client import (
    ActionExecutionClient,
)
from openhands.runtime.impl.docker.containers import remove_all_containers
from openhands.runtime.plugins import PluginRequirement
from openhands.runtime.utils import find_available_tcp_port
from openhands.runtime.utils.log_streamer import LogStreamer
from openhands.runtime.utils.runtime_build import build_runtime_image
from openhands.utils.async_utils import call_sync_from_async
from openhands.utils.tenacity_stop import stop_if_should_exit

CONTAINER_NAME_PREFIX = 'openhands-runtime-'


def remove_all_runtime_containers():
    remove_all_containers(CONTAINER_NAME_PREFIX)


_atexit_registered = False


class DockerRuntime(ActionExecutionClient):
    """This runtime will subscribe the event stream.
    When receive an event, it will send the event to runtime-client which run inside the docker environment.

    Args:
        config (AppConfig): The application configuration.
        event_stream (EventStream): The event stream to subscribe to.
        sid (str, optional): The session ID. Defaults to 'default'.
        plugins (list[PluginRequirement] | None, optional): List of plugin requirements. Defaults to None.
        env_vars (dict[str, str] | None, optional): Environment variables to set. Defaults to None.
    """

    def __init__(
        self,
        config: AppConfig,
        event_stream: EventStream,
        sid: str = 'default',
        plugins: list[PluginRequirement] | None = None,
        env_vars: dict[str, str] | None = None,
        status_callback: Callable | None = None,
        attach_to_existing: bool = False,
        headless_mode: bool = True,
    ):
        global _atexit_registered
        if not _atexit_registered:
            _atexit_registered = True
            atexit.register(remove_all_runtime_containers)

        self.config = config
        self._host_port = 30000  # initial dummy value
        self._container_port = 30001  # initial dummy value
        self._runtime_initialized: bool = False
        self.api_url = f'{self.config.sandbox.local_runtime_url}:{self._container_port}'
        self.status_callback = status_callback

        self.docker_client: docker.DockerClient = self._init_docker_client()
        self.base_container_image = self.config.sandbox.base_container_image
        self.runtime_container_image = self.config.sandbox.runtime_container_image
        self.container_name = CONTAINER_NAME_PREFIX + sid
        self.container = None

        self.runtime_builder = DockerRuntimeBuilder(self.docker_client)

        # Buffer for container logs
        self.log_streamer: LogStreamer | None = None

        super().__init__(
            config,
            event_stream,
            sid,
            plugins,
            env_vars,
            status_callback,
            attach_to_existing,
            headless_mode,
        )

        # Log runtime_extra_deps after base class initialization so self.sid is available
        if self.config.sandbox.runtime_extra_deps:
            self.log(
                'debug',
                f'Installing extra user-provided dependencies in the runtime image: {self.config.sandbox.runtime_extra_deps}',
            )

    def _get_action_execution_server_host(self):
        return self.api_url

    async def connect(self):
        self.send_status_message('STATUS$STARTING_RUNTIME')
        try:
            await call_sync_from_async(self._attach_to_container)
        except docker.errors.NotFound as e:
            if self.attach_to_existing:
                self.log(
                    'error',
                    f'Container {self.container_name} not found.',
                )
                raise e
            if self.runtime_container_image is None:
                if self.base_container_image is None:
                    raise ValueError(
                        'Neither runtime container image nor base container image is set'
                    )
                self.send_status_message('STATUS$STARTING_CONTAINER')
                self.runtime_container_image = build_runtime_image(
                    self.base_container_image,
                    self.runtime_builder,
                    platform=self.config.sandbox.platform,
                    extra_deps=self.config.sandbox.runtime_extra_deps,
                    force_rebuild=self.config.sandbox.force_rebuild_runtime,
                    extra_build_args=self.config.sandbox.runtime_extra_build_args,
                )

            self.log(
                'info', f'Starting runtime with image: {self.runtime_container_image}'
            )
            await call_sync_from_async(self._init_container)
            self.log(
                'info',
                f'Container started: {self.container_name}. VSCode URL: {self.vscode_url}',
            )

        self.log_streamer = LogStreamer(self.container, self.log)

        if not self.attach_to_existing:
            self.log('info', f'Waiting for client to become ready at {self.api_url}...')
            self.send_status_message('STATUS$WAITING_FOR_CLIENT')

        await call_sync_from_async(self._wait_until_alive)

        if not self.attach_to_existing:
            self.log('info', 'Runtime is ready.')

        if not self.attach_to_existing:
            await call_sync_from_async(self.setup_initial_env)

        self.log(
            'debug',
            f'Container initialized with plugins: {[plugin.name for plugin in self.plugins]}. VSCode URL: {self.vscode_url}',
        )
        if not self.attach_to_existing:
            self.send_status_message(' ')
        self._runtime_initialized = True

    @staticmethod
    @lru_cache(maxsize=1)
    def _init_docker_client() -> docker.DockerClient:
        try:
            return docker.from_env()
        except Exception as ex:
            logger.error(
                'Launch docker client failed. Please make sure you have installed docker and started docker desktop/daemon.',
            )
            raise ex

    def _init_container(self):
        self.log('debug', 'Preparing to start container...')
        self.send_status_message('STATUS$PREPARING_CONTAINER')
        plugin_arg = ''
        if self.plugins is not None and len(self.plugins) > 0:
            plugin_arg = (
                f'--plugins {" ".join([plugin.name for plugin in self.plugins])} '
            )
        self._host_port = self._find_available_port()
        self._container_port = (
            self._host_port
        )  # in future this might differ from host port
        self.api_url = f'{self.config.sandbox.local_runtime_url}:{self._container_port}'

        use_host_network = self.config.sandbox.use_host_network
        network_mode: str | None = 'host' if use_host_network else None

        port_mapping: dict[str, list[dict[str, str]]] | None = (
            None
            if use_host_network
            else {f'{self._container_port}/tcp': [{'HostPort': str(self._host_port)}]}
        )

        if use_host_network:
            self.log(
                'warn',
                'Using host network mode. If you are using MacOS, please make sure you have the latest version of Docker Desktop and enabled host network feature: https://docs.docker.com/network/drivers/host/#docker-desktop',
            )

        # Combine environment variables
        environment = {
            'port': str(self._container_port),
            'PYTHONUNBUFFERED': 1,
        }
        if self.config.debug or DEBUG:
            environment['DEBUG'] = 'true'

        if self.vscode_enabled:
            # vscode is on port +1 from container port
            if isinstance(port_mapping, dict):
                port_mapping[f'{self._container_port + 1}/tcp'] = [
                    {'HostPort': str(self._host_port + 1)}
                ]

        self.log('debug', f'Workspace Base: {self.config.workspace_base}')
        if (
            self.config.workspace_mount_path is not None
            and self.config.workspace_mount_path_in_sandbox is not None
        ):
            # e.g. result would be: {"/home/user/openhands/workspace": {'bind': "/workspace", 'mode': 'rw'}}
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
            volumes = None
        self.log(
            'debug',
            f'Sandbox workspace: {self.config.workspace_mount_path_in_sandbox}',
        )

        if self.config.sandbox.browsergym_eval_env is not None:
            browsergym_arg = (
                f'--browsergym-eval-env {self.config.sandbox.browsergym_eval_env}'
            )
        else:
            browsergym_arg = ''

        try:
            self.container = self.docker_client.containers.run(
                self.runtime_container_image,
                command=(
                    f'/openhands/micromamba/bin/micromamba run -n openhands '
                    f'poetry run '
                    f'python -u -m openhands.runtime.action_execution_server {self._container_port} '
                    f'--working-dir "{self.config.workspace_mount_path_in_sandbox}" '
                    f'{plugin_arg}'
                    f'--username {"openhands" if self.config.run_as_openhands else "root"} '
                    f'--user-id {self.config.sandbox.user_id} '
                    f'{browsergym_arg}'
                ),
                network_mode=network_mode,
                ports=port_mapping,
                working_dir='/openhands/code/',  # do not change this!
                name=self.container_name,
                detach=True,
                environment=environment,
                volumes=volumes,
                device_requests=(
                    [docker.types.DeviceRequest(capabilities=[['gpu']], count=-1)]
                    if self.config.sandbox.enable_gpu
                    else None
                ),
                **(self.config.sandbox.docker_runtime_kwargs or {}),
            )
            self.log('debug', f'Container started. Server url: {self.api_url}')
            self.send_status_message('STATUS$CONTAINER_STARTED')
        except docker.errors.APIError as e:
            if '409' in str(e):
                self.log(
                    'warning',
                    f'Container {self.container_name} already exists. Removing...',
                )
                remove_all_containers(self.container_name)
                return self._init_container()

            else:
                self.log(
                    'error',
                    f'Error: Instance {self.container_name} FAILED to start container!\n',
                )
        except Exception as e:
            self.log(
                'error',
                f'Error: Instance {self.container_name} FAILED to start container!\n',
            )
            self.log('error', str(e))
            self.close()
            raise e

    def _attach_to_container(self):
        self._container_port = 0
        self.container = self.docker_client.containers.get(self.container_name)
        for port in self.container.attrs['NetworkSettings']['Ports']:  # type: ignore
            self._container_port = int(port.split('/')[0])
            break
        self._host_port = self._container_port
        self.api_url = f'{self.config.sandbox.local_runtime_url}:{self._container_port}'
        self.log(
            'debug',
            f'attached to container: {self.container_name} {self._container_port} {self.api_url}',
        )

    @tenacity.retry(
        stop=tenacity.stop_after_delay(120) | stop_if_should_exit(),
        retry=tenacity.retry_if_exception_type(
            (ConnectionError, requests.exceptions.ConnectionError)
        ),
        reraise=True,
        wait=tenacity.wait_fixed(2),
    )
    def _wait_until_alive(self):
        try:
            container = self.docker_client.containers.get(self.container_name)
            if container.status == 'exited':
                raise AgentRuntimeDisconnectedError(
                    f'Container {self.container_name} has exited.'
                )
        except docker.errors.NotFound:
            raise AgentRuntimeNotFoundError(
                f'Container {self.container_name} not found.'
            )

        if not self.log_streamer:
            raise AgentRuntimeNotReadyError('Runtime client is not ready.')

        self.check_if_alive()

    def close(self, rm_all_containers: bool | None = None):
        """Closes the DockerRuntime and associated objects

        Parameters:
        - rm_all_containers (bool): Whether to remove all containers with the 'openhands-sandbox-' prefix
        """
        super().close()
        if self.log_streamer:
            self.log_streamer.close()

        if rm_all_containers is None:
            rm_all_containers = self.config.sandbox.rm_all_containers

        if self.config.sandbox.keep_runtime_alive or self.attach_to_existing:
            return
        close_prefix = (
            CONTAINER_NAME_PREFIX if rm_all_containers else self.container_name
        )
        remove_all_containers(close_prefix)

    def _is_port_in_use_docker(self, port):
        containers = self.docker_client.containers.list()
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
        # If no port is found after max_attempts, return the last tried port
        return port

    @property
    def vscode_url(self) -> str | None:
        token = super().get_vscode_token()
        if not token:
            return None
        vscode_url = f'http://localhost:{self._host_port + 1}/?tkn={token}&folder={self.config.workspace_mount_path_in_sandbox}'
        return vscode_url
