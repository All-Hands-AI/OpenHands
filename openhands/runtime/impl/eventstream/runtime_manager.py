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
from openhands.core.logger import DEBUG, openhands_logger as logger
from openhands.runtime.plugins import PluginRequirement, VSCodeRequirement
from openhands.runtime.container import ContainerInfo
from openhands.runtime.builder import DockerRuntimeBuilder
from openhands.events import EventStream
from openhands.runtime.base import Runtime
from openhands.runtime.runtime_manager import RuntimeManager
from openhands.runtime.utils.runtime_build import build_runtime_image
from openhands.runtime.utils import find_available_tcp_port
from openhands.runtime.utils.log_streamer import LogStreamer
from openhands.runtime.utils.request import send_request
from openhands.utils.tenacity_stop import stop_if_should_exit

CONTAINER_NAME_PREFIX = 'openhands-runtime-'

_atexit_registered = False



class EventStreamRuntimeManager(RuntimeManager):
    """Manages Docker container lifecycle for EventStreamRuntime instances."""

    def __init__(self, config: AppConfig):
        super().__init__(config)
        global _atexit_registered
        if not _atexit_registered:
            _atexit_registered = True
            atexit.register(self._cleanup_all_containers)

        self._containers: Dict[str, ContainerInfo] = {}
        self._docker_client = self._init_docker_client()
        self._runtime_builder: DockerRuntimeBuilder = DockerRuntimeBuilder(self._docker_client)

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
        """Create a new EventStreamRuntime with an initialized container.
        
        This overrides the base create_runtime to handle container initialization
        before creating the runtime.
        """
        if sid in self._runtimes:
            raise RuntimeError(f'Runtime with ID {sid} already exists')

        # First initialize or attach to the container
        try:
            if attach_to_existing:
                container_info = self.attach_to_container(sid)
            else:
                runtime_container_image = self.config.sandbox.runtime_container_image
                if runtime_container_image is None:
                    if self.config.sandbox.base_container_image is None:
                        raise ValueError(
                            'Neither runtime container image nor base container image is set'
                        )
                    if status_callback:
                        status_callback('info', 'STATUS$STARTING_CONTAINER')
                    runtime_container_image = build_runtime_image(
                        self.config.sandbox.base_container_image,
                        self._runtime_builder,
                        platform=self.config.sandbox.platform,
                        extra_deps=self.config.sandbox.runtime_extra_deps,
                        force_rebuild=self.config.sandbox.force_rebuild_runtime,
                        extra_build_args=self.config.sandbox.runtime_extra_build_args,
                    )

                container_info = self.initialize_container(
                    runtime_container_image,
                    sid,
                    plugins,
                    env_vars,
                    status_callback,
                )

            # Import here to avoid circular dependency
            from openhands.runtime.impl.eventstream.eventstream_runtime import EventStreamRuntime

            # Create the runtime with the initialized container
            runtime = EventStreamRuntime(
                config=self.config,
                event_stream=event_stream,
                sid=sid,
                plugins=plugins,
                env_vars=env_vars,
                status_callback=status_callback,
                attach_to_existing=attach_to_existing,
                headless_mode=headless_mode,
                container_info=container_info,
            )

            # Initialize the runtime
            try:
                await runtime.connect()
            except AgentRuntimeUnavailableError as e:
                logger.error(f'Runtime initialization failed: {e}', exc_info=True)
                if status_callback:
                    status_callback('error', 'STATUS$ERROR_RUNTIME_DISCONNECTED', str(e))
                self._cleanup_container(sid)
                raise

            self._runtimes[sid] = runtime
            logger.info(f'Created runtime with ID: {sid}')
            return runtime

        except Exception as e:
            logger.error(f'Failed to create runtime: {str(e)}')
            self._cleanup_container(sid)
            raise

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

    def initialize_container(
        self,
        runtime_container_image: str,
        sid: str,
        plugins: Optional[list[PluginRequirement]] = None,
        env_vars: Optional[Dict[str, str]] = None,
        status_callback=None,
    ) -> ContainerInfo:
        """Initialize a new container for a runtime.
        
        Args:
            runtime_container_image: The Docker image to use
            sid: The session ID that will be used to generate the container name
            plugins: Optional list of plugins to enable
            env_vars: Optional environment variables to set
            status_callback: Optional callback for status updates
            
        Returns:
            ContainerInfo object with connection details
        """
        logger.debug('Preparing to start container...')
        if status_callback:
            status_callback('info', 'STATUS$PREPARING_CONTAINER')

        container_name = f'{CONTAINER_NAME_PREFIX}{sid}'
        if container_name in self._containers:
            raise RuntimeError(f'Container {container_name} already exists')

        # Find an available port
        container_port = self._find_available_port()
        host_port = container_port  # In future this might differ

        plugin_arg = ''
        if plugins:
            plugin_arg = f'--plugins {" ".join([plugin.name for plugin in plugins])} '

        use_host_network = self.config.sandbox.use_host_network
        network_mode: str | None = 'host' if use_host_network else None

        port_mapping: dict[str, list[dict[str, str]]] | None = (
            None
            if use_host_network
            else {f'{container_port}/tcp': [{'HostPort': str(host_port)}]}
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
                    {'HostPort': str(host_port + 1)}
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
            
            api_url = f'{self.config.sandbox.local_runtime_url}:{container_port}'
            logger.debug(f'Container started. Server url: {api_url}')
            
            if status_callback:
                status_callback('info', 'STATUS$CONTAINER_STARTED')

            container_info = ContainerInfo(
                container_id=container.id,
                api_url=api_url,
                host_port=host_port,
                container_port=container_port,
                container=container,
            )
            self._containers[container_name] = container_info
            return container_info

        except docker.errors.APIError as e:
            if '409' in str(e):
                logger.warning(
                    f'Container {container_name} already exists. Removing...',
                )
                self._cleanup_container(container_name)
                return self.initialize_container(
                    runtime_container_image,
                    sid,
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

    def attach_to_container(self, sid: str) -> ContainerInfo:
        """Attach to an existing container.
        
        Args:
            sid: The session ID used to generate the container name
            
        Returns:
            ContainerInfo object with connection details
            
        Raises:
            AgentRuntimeNotFoundError: If the container doesn't exist
        """
        container_name = f'{CONTAINER_NAME_PREFIX}{sid}'
        
        # Check if we already have the container info
        if container_name in self._containers:
            return self._containers[container_name]
            
        try:
            container = self._docker_client.containers.get(container_name)
            container_port = 0
            for port in container.attrs['NetworkSettings']['Ports']:
                container_port = int(port.split('/')[0])
                break
                
            host_port = container_port  # In future this might differ
            api_url = f'{self.config.sandbox.local_runtime_url}:{container_port}'
            
            container_info = ContainerInfo(
                container_id=container.id,
                api_url=api_url,
                host_port=host_port,
                container_port=container_port,
                container=container,
            )
            self._containers[container_name] = container_info
            return container_info
            
        except docker.errors.NotFound:
            raise AgentRuntimeNotFoundError(f'Container {container_name} not found.')

    @tenacity.retry(
        stop=tenacity.stop_after_delay(120) | stop_if_should_exit(),
        retry=tenacity.retry_if_exception_type(
            (ConnectionError, requests.exceptions.ConnectionError)
        ),
        reraise=True,
        wait=tenacity.wait_fixed(2),
    )
    def wait_until_alive(
        self,
        sid: str,
        log_streamer: Optional[LogStreamer] = None,
    ):
        """Wait until a container is ready to accept connections.
        
        Args:
            sid: The session ID used to generate the container name
            log_streamer: Optional log streamer that must be ready
            
        Raises:
            AgentRuntimeNotFoundError: If the container doesn't exist
            AgentRuntimeDisconnectedError: If the container has exited
            AgentRuntimeNotReadyError: If the log streamer isn't ready
        """
        container_name = f'{CONTAINER_NAME_PREFIX}{sid}'
        container_info = self._containers.get(container_name)
        if not container_info:
            raise AgentRuntimeNotFoundError(f'Container {container_name} not found.')
            
        try:
            if container_info.container.status == 'exited':
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
            f'{container_info.api_url}/alive',
            timeout=5,
        ):
            pass

    def _cleanup_container(self, sid: str, remove_all: bool = False) -> None:
        """Clean up a container and its resources.
        
        Args:
            sid: The session ID used to generate the container name
            remove_all: If True, remove all containers with the same prefix
        """
        container_name = f'{CONTAINER_NAME_PREFIX}{sid}'
        if remove_all:
            self._cleanup_all_containers()
        else:
            try:
                container = self._docker_client.containers.get(container_name)
                container.remove(force=True)
                if container_name in self._containers:
                    del self._containers[container_name]
            except docker.errors.NotFound:
                pass

    def _cleanup_all_containers(self):
        """Clean up all containers managed by this RuntimeManager."""
        containers = self._docker_client.containers.list(all=True)
        for container in containers:
            if container.name.startswith(CONTAINER_NAME_PREFIX):
                try:
                    container.remove(force=True)
                except docker.errors.NotFound:
                    pass
        self._containers.clear()

    def destroy_runtime(self, runtime_id: str) -> bool:
        """Destroy a runtime and its container.
        
        Args:
            runtime_id: The runtime ID to destroy
            
        Returns:
            True if the runtime was found and destroyed, False otherwise
        """
        runtime = self._runtimes.get(runtime_id)
        if runtime:
            runtime.close()
            self._cleanup_container(runtime_id)
            del self._runtimes[runtime_id]
            logger.info(f'Destroyed runtime with ID: {runtime_id}')
            return True
        return False

    async def destroy_all_runtimes(self):
        """Destroy all runtimes and their containers."""
        for runtime_id in list(self._runtimes.keys()):
            self.destroy_runtime(runtime_id)
        self._cleanup_all_containers()