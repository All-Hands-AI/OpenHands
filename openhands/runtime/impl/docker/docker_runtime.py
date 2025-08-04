import os
import platform
import threading
import typing
import uuid
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Callable, Optional
from uuid import UUID

import docker
import httpx
import tenacity
from docker.models.containers import Container

from openhands.core.config import OpenHandsConfig
from openhands.core.exceptions import (
    AgentRuntimeDisconnectedError,
    AgentRuntimeNotFoundError,
)
from openhands.core.logger import DEBUG, DEBUG_RUNTIME
from openhands.core.logger import openhands_logger as logger
from openhands.events import EventStream
from openhands.events.action import Action
from openhands.events.observation import Observation
from openhands.integrations.provider import PROVIDER_TOKEN_TYPE
from openhands.runtime.builder import DockerRuntimeBuilder
from openhands.runtime.impl.action_execution.action_execution_client import (
    ActionExecutionClient,
)
from openhands.runtime.impl.docker.containers import stop_all_containers
from openhands.runtime.plugins import PluginRequirement
from openhands.runtime.runtime_status import RuntimeStatus
from openhands.runtime.utils import find_available_tcp_port
from openhands.runtime.utils.command import (
    DEFAULT_MAIN_MODULE,
    get_action_execution_server_startup_command,
)
from openhands.runtime.utils.log_streamer import LogStreamer
from openhands.runtime.utils.port_lock import PortLock, find_available_port_with_lock
from openhands.runtime.utils.runtime_build import build_runtime_image
from openhands.utils.async_utils import call_sync_from_async
from openhands.utils.shutdown_listener import add_shutdown_listener
from openhands.utils.tenacity_stop import stop_if_should_exit

CONTAINER_NAME_PREFIX = 'openhands-runtime-'
WARM_CONTAINER_PREFIX = 'openhands-warm-'

EXECUTION_SERVER_PORT_RANGE = (30000, 39999)
VSCODE_PORT_RANGE = (40000, 49999)
APP_PORT_RANGE_1 = (50000, 54999)
APP_PORT_RANGE_2 = (55000, 59999)

if os.name == 'nt' or platform.release().endswith('microsoft-standard-WSL2'):
    EXECUTION_SERVER_PORT_RANGE = (30000, 34999)
    VSCODE_PORT_RANGE = (35000, 39999)
    APP_PORT_RANGE_1 = (40000, 44999)
    APP_PORT_RANGE_2 = (45000, 49151)

# Global variables to track warm containers
_WARM_CONTAINERS: list[Any] = []
_RUNNING_CONTAINERS: dict[str, Any] = {}


@dataclass
class DockerContainerInfo:
    """Information about a running Docker container."""

    container: Container
    host_port: int
    container_port: int
    vscode_port: int
    app_ports: list[int]
    host_port_lock: Optional[PortLock] = None
    vscode_port_lock: Optional[PortLock] = None
    app_port_locks: Optional[list[PortLock]] = None
    log_streamer: Optional[Any] = None
    api_url: Optional[str] = None


def _is_retryablewait_until_alive_error(exception: Exception) -> bool:
    if isinstance(exception, tenacity.RetryError):
        cause = exception.last_attempt.exception()
        return _is_retryablewait_until_alive_error(cause)

    return isinstance(
        exception,
        (
            ConnectionError,
            httpx.ConnectTimeout,
            httpx.NetworkError,
            httpx.RemoteProtocolError,
            httpx.HTTPStatusError,
            httpx.ReadTimeout,
        ),
    )


def _create_warm_container(
    config: OpenHandsConfig,
    plugins: list[PluginRequirement],
    runtime_container_image: str,
) -> DockerContainerInfo:
    """Create a warm container for future use.

    Args:
        config: The OpenHands configuration.
        plugins: List of plugin requirements.
        runtime_container_image: The container image to use.

    Returns:
        DockerContainerInfo: Information about the created container.
    """
    # Generate a unique ID for the warm container
    warm_id = f'{WARM_CONTAINER_PREFIX}{uuid.uuid4().hex[:8]}'
    logger.info(f'Creating warm container {warm_id}')

    # Create a temporary DockerRuntime instance to create the container
    from openhands.core.file_store import FileStore

    file_store = FileStore(warm_id)
    event_stream = EventStream(sid=warm_id, file_store=file_store)
    runtime = DockerRuntime(
        config=config,
        sid=warm_id,
        plugins=plugins,
        attach_to_existing=False,
        event_stream=event_stream,
    )

    # Set the runtime container image
    if runtime_container_image:
        # Explicitly cast to string to help mypy
        runtime.runtime_container_image = str(runtime_container_image)

    # Initialize the container
    runtime.init_container()

    # Create container info
    if runtime.container is None:
        raise RuntimeError('Failed to create container')

    container_info = DockerContainerInfo(
        container=runtime.container,
        host_port=runtime._host_port,
        container_port=runtime._container_port,
        vscode_port=runtime._vscode_port,
        app_ports=runtime._app_ports,
        host_port_lock=runtime._host_port_lock,
        vscode_port_lock=runtime._vscode_port_lock,
        app_port_locks=runtime._app_port_locks,
        log_streamer=None,
        api_url=runtime.api_url if hasattr(runtime, 'api_url') else None,
    )

    # Wait for the container to be ready
    runtime.wait_until_alive()

    # Return the container info
    return container_info


def _create_warm_container_in_background(
    config: OpenHandsConfig,
    plugins: list[PluginRequirement],
    runtime_container_image: str,
) -> None:
    """Create a warm container in a background thread.

    Args:
        config: The OpenHands configuration.
        plugins: List of plugin requirements.
        runtime_container_image: The container image to use.
    """

    def _create_container_thread():
        try:
            container_info = _create_warm_container(
                config, plugins, runtime_container_image
            )
            _WARM_CONTAINERS.append(container_info)
            logger.info(
                f'Added warm container to pool (total: {len(_WARM_CONTAINERS)})'
            )
        except Exception as e:
            logger.error(f'Error creating warm container: {e}')

    # Start a thread to create the container
    thread = threading.Thread(target=_create_container_thread)
    thread.daemon = True
    thread.start()


def cleanup_warm_containers() -> None:
    """Clean up all warm containers."""
    logger.info(f'Cleaning up {len(_WARM_CONTAINERS)} warm containers')

    # Create a copy of the list to avoid modification during iteration
    containers_to_cleanup = _WARM_CONTAINERS.copy()
    _WARM_CONTAINERS.clear()

    # Clean up each container
    for container_info in containers_to_cleanup:
        try:
            # Stop and remove the container
            container_info.container.stop()
            container_info.container.remove(force=True)

            # Release port locks
            if container_info.host_port_lock:
                container_info.host_port_lock.release()

            if container_info.vscode_port_lock:
                container_info.vscode_port_lock.release()

            if container_info.app_port_locks:
                for lock in container_info.app_port_locks:
                    if lock:
                        lock.release()
        except Exception as e:
            logger.error(f'Error cleaning up warm container: {e}')


# The DockerRuntime class will be initialized at the end of the file


class DockerRuntime(ActionExecutionClient):
    """This runtime will subscribe the event stream.

    When receive an event, it will send the event to runtime-client which run inside the docker environment.

    Args:
        config (OpenHandsConfig): The application configuration.
        event_stream (EventStream): The event stream to subscribe to.
        sid (str, optional): The session ID. Defaults to 'default'.
        plugins (list[PluginRequirement] | None, optional): List of plugin requirements. Defaults to None.
        env_vars (dict[str, str] | None, optional): Environment variables to set. Defaults to None.
    """

    _shutdown_listener_id: UUID | None = None

    def __init__(
        self,
        config: OpenHandsConfig,
        event_stream: EventStream,
        sid: str = 'default',
        plugins: list[PluginRequirement] | None = None,
        env_vars: dict[str, str] | None = None,
        status_callback: Callable | None = None,
        attach_to_existing: bool = False,
        headless_mode: bool = True,
        user_id: str | None = None,
        git_provider_tokens: PROVIDER_TOKEN_TYPE | None = None,
        main_module: str = DEFAULT_MAIN_MODULE,
    ):
        if not DockerRuntime._shutdown_listener_id:
            DockerRuntime._shutdown_listener_id = add_shutdown_listener(
                lambda: stop_all_containers(CONTAINER_NAME_PREFIX)
            )

        self.config = config
        self.status_callback = status_callback

        self._host_port = -1
        self._container_port = -1
        self._vscode_port = -1
        self._app_ports: list[int] = []

        # Port locks to prevent race conditions
        self._host_port_lock: PortLock | None = None
        self._vscode_port_lock: PortLock | None = None
        self._app_port_locks: list[PortLock] = []

        if os.environ.get('DOCKER_HOST_ADDR'):
            logger.info(
                f'Using DOCKER_HOST_IP: {os.environ["DOCKER_HOST_ADDR"]} for local_runtime_url'
            )
            self.config.sandbox.local_runtime_url = (
                f'http://{os.environ["DOCKER_HOST_ADDR"]}'
            )

        self.docker_client: docker.DockerClient = self._init_docker_client()
        self.api_url = f'{self.config.sandbox.local_runtime_url}:{self._container_port}'

        self.base_container_image = self.config.sandbox.base_container_image
        self.runtime_container_image = self.config.sandbox.runtime_container_image
        self.container_name = CONTAINER_NAME_PREFIX + sid
        self.container: Container | None = None
        self.main_module = main_module

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
            user_id,
            git_provider_tokens,
        )

        # Log runtime_extra_deps after base class initialization so self.sid is available
        if self.config.sandbox.runtime_extra_deps:
            self.log(
                'debug',
                f'Installing extra user-provided dependencies in the runtime image: {self.config.sandbox.runtime_extra_deps}',
            )

    @property
    def action_execution_server_url(self) -> str:
        return self.api_url

    async def connect(self) -> None:
        self.set_runtime_status(RuntimeStatus.STARTING_RUNTIME)

        # Get environment variables for warm container configuration
        desired_num_warm_containers = int(os.getenv('DESIRED_NUM_WARM_CONTAINERS', '0'))

        # Check if there's already a container running for this session ID
        if self.sid in _RUNNING_CONTAINERS:
            self.log('info', f'Connecting to existing container for session {self.sid}')
            container_info = _RUNNING_CONTAINERS[self.sid]
            self.container = container_info.container
            self._host_port = container_info.host_port
            self._container_port = container_info.container_port
            self._vscode_port = container_info.vscode_port
            self._app_ports = container_info.app_ports
            self.api_url = container_info.api_url
            self._host_port_lock = container_info.host_port_lock
            self._vscode_port_lock = container_info.vscode_port_lock
            self._app_port_locks = container_info.app_port_locks
            self.log_streamer = container_info.log_streamer
        else:
            # Try to use a warm container if available
            warm_container_available = False

            if not self.attach_to_existing:
                try:
                    # Check if there are any warm containers available
                    if _WARM_CONTAINERS:
                        # Pop a warm container from the list
                        self.log('info', 'Using a warm container')
                        container_info = _WARM_CONTAINERS.pop(0)

                        # Use the warm container
                        self.container = container_info.container
                        self._host_port = container_info.host_port
                        self._container_port = container_info.container_port
                        self._vscode_port = container_info.vscode_port
                        self._app_ports = container_info.app_ports
                        self._host_port_lock = container_info.host_port_lock
                        self._vscode_port_lock = container_info.vscode_port_lock
                        self._app_port_locks = container_info.app_port_locks

                        # Rename the container to match the session ID
                        if self.container:
                            old_name = self.container.name
                            self.container.rename(self.container_name)
                        else:
                            self.log('error', 'Container is None, cannot rename')
                        if self.container:
                            self.log(
                                'info',
                                f'Renamed container from {old_name} to {self.container_name}',
                            )

                        # Update the API URL
                        self.api_url = container_info.api_url

                        # Set up log streamer if needed
                        if DEBUG_RUNTIME and self.container:
                            self.log_streamer = LogStreamer(self.container, self.log)
                        else:
                            self.log_streamer = None

                        # Store the container in the global dictionary
                        if self.container:
                            _RUNNING_CONTAINERS[self.sid] = DockerContainerInfo(
                                container=self.container,
                                host_port=self._host_port,
                                container_port=self._container_port,
                                vscode_port=self._vscode_port,
                                app_ports=self._app_ports,
                                host_port_lock=self._host_port_lock,
                                vscode_port_lock=self._vscode_port_lock,
                                app_port_locks=self._app_port_locks,
                                log_streamer=self.log_streamer,
                                api_url=self.api_url,
                            )

                        warm_container_available = True
                    else:
                        # No warm containers available
                        self.log(
                            'info',
                            'No warm containers available, starting a new container',
                        )
                        warm_container_available = False
                except Exception as e:
                    # Error using warm container
                    self.log('error', f'Error using warm container: {e}')
                    warm_container_available = False

            # If no warm container is available, start a new one
            if not warm_container_available:
                try:
                    await call_sync_from_async(self._attach_to_container)
                except docker.errors.NotFound as e:
                    if self.attach_to_existing:
                        self.log(
                            'warning',
                            f'Container {self.container_name} not found.',
                        )
                        raise AgentRuntimeDisconnectedError from e
                    self.maybe_build_runtime_container_image()
                    self.log(
                        'info',
                        f'Starting runtime with image: {self.runtime_container_image}',
                    )
                    await call_sync_from_async(self.init_container)
                    self.log(
                        'info',
                        f'Container started: {self.container_name}. VSCode URL: {self.vscode_url}',
                    )

                    # Set up log streamer if needed
                    if DEBUG_RUNTIME and self.container:
                        self.log_streamer = LogStreamer(self.container, self.log)
                    else:
                        self.log_streamer = None

                    # Store the container in the global dictionary
                    if self.container:
                        _RUNNING_CONTAINERS[self.sid] = DockerContainerInfo(
                            container=self.container,
                            host_port=self._host_port,
                            container_port=self._container_port,
                            vscode_port=self._vscode_port,
                            app_ports=self._app_ports,
                            host_port_lock=self._host_port_lock,
                            vscode_port_lock=self._vscode_port_lock,
                            app_port_locks=self._app_port_locks,
                            log_streamer=self.log_streamer,
                            api_url=self.api_url,
                        )

        if not self.attach_to_existing:
            self.log('info', f'Waiting for client to become ready at {self.api_url}...')
            self.set_runtime_status(RuntimeStatus.STARTING_RUNTIME)

        await call_sync_from_async(self.wait_until_alive)

        if not self.attach_to_existing:
            self.set_runtime_status(RuntimeStatus.READY)
        self._runtime_initialized = True

        # Check if we need to create more warm containers after connecting
        if (
            desired_num_warm_containers > 0
            and len(_WARM_CONTAINERS) < desired_num_warm_containers
        ):
            num_to_create = desired_num_warm_containers - len(_WARM_CONTAINERS)
            self.log(
                'info',
                f'Creating {num_to_create} additional warm containers to reach desired count',
            )
            for _ in range(num_to_create):
                if self.runtime_container_image:
                    _create_warm_container_in_background(
                        self.config, self.plugins, self.runtime_container_image
                    )

        if not self.attach_to_existing:
            self.log('info', 'Runtime is ready.')

        if not self.attach_to_existing:
            await call_sync_from_async(self.setup_initial_env)

        self.log(
            'debug',
            f'Container initialized with plugins: {[plugin.name for plugin in self.plugins]}. VSCode URL: {self.vscode_url}',
        )
        if not self.attach_to_existing:
            self.set_runtime_status(RuntimeStatus.READY)
        self._runtime_initialized = True

    def maybe_build_runtime_container_image(self):
        if self.runtime_container_image is None:
            if self.base_container_image is None:
                raise ValueError(
                    'Neither runtime container image nor base container image is set'
                )
            self.set_runtime_status(RuntimeStatus.BUILDING_RUNTIME)
            self.runtime_container_image = build_runtime_image(
                self.base_container_image,
                self.runtime_builder,
                platform=self.config.sandbox.platform,
                extra_deps=self.config.sandbox.runtime_extra_deps,
                force_rebuild=self.config.sandbox.force_rebuild_runtime,
                extra_build_args=self.config.sandbox.runtime_extra_build_args,
                enable_browser=self.config.enable_browser,
            )

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

    @classmethod
    def initialize(cls) -> None:
        """Initialize the DockerRuntime class.

        This method is called at module import time to set up any class-level resources.
        """
        # Register shutdown handler to clean up warm containers
        add_shutdown_listener(cleanup_warm_containers)

    @staticmethod
    def initialize_warm_containers(
        config: OpenHandsConfig,
        plugins: list[PluginRequirement],
        runtime_container_image: Optional[str] = None,
    ) -> None:
        """Initialize warm containers for future use.

        Args:
            config: The OpenHands configuration.
            plugins: List of plugin requirements.
            runtime_container_image: The container image to use, or None to build it.
        """
        initial_num_warm_containers = int(os.getenv('INITIAL_NUM_WARM_CONTAINERS', '0'))
        # Initialize warm containers if needed
        if initial_num_warm_containers > 0 and len(_WARM_CONTAINERS) == 0:
            logger.info(
                f'Initializing {initial_num_warm_containers} warm containers for future use'
            )

            # Build the runtime container image if needed
            if (
                runtime_container_image is None
                and config.sandbox.runtime_container_image is None
            ):
                if config.sandbox.base_container_image is None:
                    raise ValueError(
                        'Neither runtime container image nor base container image is set'
                    )
                docker_client = docker.from_env()
                runtime_builder = DockerRuntimeBuilder(docker_client)
                runtime_container_image = build_runtime_image(
                    config.sandbox.base_container_image,
                    runtime_builder,
                    platform=config.sandbox.platform,
                    extra_deps=config.sandbox.runtime_extra_deps,
                    force_rebuild=config.sandbox.force_rebuild_runtime,
                    extra_build_args=config.sandbox.runtime_extra_build_args,
                    enable_browser=config.enable_browser,
                )
            elif runtime_container_image is None:
                runtime_container_image = config.sandbox.runtime_container_image

            for _ in range(initial_num_warm_containers):
                if runtime_container_image:
                    _create_warm_container_in_background(
                        config, plugins, runtime_container_image
                    )

    def _process_volumes(self) -> dict[str, dict[str, str]]:
        """Process volume mounts based on configuration.

        Returns:
            A dictionary mapping host paths to container bind mounts with their modes.
        """
        # Initialize volumes dictionary
        volumes: dict[str, dict[str, str]] = {}

        # Process volumes (comma-delimited)
        if self.config.sandbox.volumes is not None:
            # Handle multiple mounts with comma delimiter
            mounts = self.config.sandbox.volumes.split(',')

            for mount in mounts:
                parts = mount.split(':')
                if len(parts) >= 2:
                    host_path = os.path.abspath(parts[0])
                    container_path = parts[1]
                    # Default mode is 'rw' if not specified
                    mount_mode = parts[2] if len(parts) > 2 else 'rw'

                    volumes[host_path] = {
                        'bind': container_path,
                        'mode': mount_mode,
                    }
                    logger.debug(
                        f'Mount dir (sandbox.volumes): {host_path} to {container_path} with mode: {mount_mode}'
                    )

        # Legacy mounting with workspace_* parameters
        elif (
            self.config.workspace_mount_path is not None
            and self.config.workspace_mount_path_in_sandbox is not None
        ):
            mount_mode = 'rw'  # Default mode

            # e.g. result would be: {"/home/user/openhands/workspace": {'bind': "/workspace", 'mode': 'rw'}}
            # Add os.path.abspath() here so that relative paths can be used when workspace_mount_path is configured in config.toml
            volumes[os.path.abspath(self.config.workspace_mount_path)] = {
                'bind': self.config.workspace_mount_path_in_sandbox,
                'mode': mount_mode,
            }
            logger.debug(
                f'Mount dir (legacy): {self.config.workspace_mount_path} with mode: {mount_mode}'
            )

        return volumes

    def init_container(self) -> None:
        self.log('debug', 'Preparing to start container...')
        self.set_runtime_status(RuntimeStatus.STARTING_RUNTIME)

        # Allocate host port with locking to prevent race conditions
        self._host_port, self._host_port_lock = self._find_available_port_with_lock(
            EXECUTION_SERVER_PORT_RANGE
        )
        self._container_port = self._host_port

        # Use the configured vscode_port if provided, otherwise find an available port
        if self.config.sandbox.vscode_port:
            self._vscode_port = self.config.sandbox.vscode_port
            self._vscode_port_lock = None  # No lock needed for configured port
        else:
            self._vscode_port, self._vscode_port_lock = (
                self._find_available_port_with_lock(VSCODE_PORT_RANGE)
            )

        # Allocate app ports with locking
        app_port_1, app_lock_1 = self._find_available_port_with_lock(APP_PORT_RANGE_1)
        app_port_2, app_lock_2 = self._find_available_port_with_lock(APP_PORT_RANGE_2)

        self._app_ports = [app_port_1, app_port_2]
        self._app_port_locks = [
            lock for lock in [app_lock_1, app_lock_2] if lock is not None
        ]

        self.api_url = f'{self.config.sandbox.local_runtime_url}:{self._container_port}'

        use_host_network = self.config.sandbox.use_host_network
        network_mode: typing.Literal['host'] | None = (
            'host' if use_host_network else None
        )

        # Initialize port mappings
        port_mapping: dict[str, list[dict[str, str]]] | None = None
        if not use_host_network:
            port_mapping = {
                f'{self._container_port}/tcp': [
                    {
                        'HostPort': str(self._host_port),
                        'HostIp': self.config.sandbox.runtime_binding_address,
                    }
                ],
            }

            if self.vscode_enabled:
                port_mapping[f'{self._vscode_port}/tcp'] = [
                    {
                        'HostPort': str(self._vscode_port),
                        'HostIp': self.config.sandbox.runtime_binding_address,
                    }
                ]

            for port in self._app_ports:
                port_mapping[f'{port}/tcp'] = [
                    {
                        'HostPort': str(port),
                        'HostIp': self.config.sandbox.runtime_binding_address,
                    }
                ]
        else:
            self.log(
                'warn',
                'Using host network mode. If you are using MacOS, please make sure you have the latest version of Docker Desktop and enabled host network feature: https://docs.docker.com/network/drivers/host/#docker-desktop',
            )

        # Combine environment variables
        environment = dict(**self.initial_env_vars)
        environment.update(
            {
                'port': str(self._container_port),
                'PYTHONUNBUFFERED': '1',
                # Passing in the ports means nested runtimes do not come up with their own ports!
                'VSCODE_PORT': str(self._vscode_port),
                'APP_PORT_1': str(self._app_ports[0]),
                'APP_PORT_2': str(self._app_ports[1]),
                'PIP_BREAK_SYSTEM_PACKAGES': '1',
            }
        )
        if self.config.debug or DEBUG:
            environment['DEBUG'] = 'true'
        # also update with runtime_startup_env_vars
        environment.update(self.config.sandbox.runtime_startup_env_vars)

        self.log('debug', f'Workspace Base: {self.config.workspace_base}')

        # Process volumes for mounting
        volumes = self._process_volumes()

        # If no volumes were configured, set to None
        if not volumes:
            logger.debug(
                'Mount dir is not set, will not mount the workspace directory to the container'
            )
            volumes = {}  # Empty dict instead of None to satisfy mypy
        self.log(
            'debug',
            f'Sandbox workspace: {self.config.workspace_mount_path_in_sandbox}',
        )

        command = self.get_action_execution_server_startup_command()
        self.log('info', f'Starting server with command: {command}')

        if self.config.sandbox.enable_gpu:
            gpu_ids = self.config.sandbox.cuda_visible_devices
            if gpu_ids is None:
                device_requests = [
                    docker.types.DeviceRequest(capabilities=[['gpu']], count=-1)
                ]
            else:
                device_requests = [
                    docker.types.DeviceRequest(
                        capabilities=[['gpu']],
                        device_ids=[str(i) for i in gpu_ids.split(',')],
                    )
                ]
        else:
            device_requests = None
        try:
            if self.runtime_container_image is None:
                raise ValueError('Runtime container image is not set')
            self.container = self.docker_client.containers.run(
                self.runtime_container_image,
                command=command,
                # Override the default 'bash' entrypoint because the command is a binary.
                entrypoint=[],
                network_mode=network_mode,
                ports=port_mapping,
                working_dir='/openhands/code/',  # do not change this!
                name=self.container_name,
                detach=True,
                environment=environment,
                volumes=volumes,  # type: ignore
                device_requests=device_requests,
                **(self.config.sandbox.docker_runtime_kwargs or {}),
            )
            self.log('debug', f'Container started. Server url: {self.api_url}')
            self.set_runtime_status(RuntimeStatus.RUNTIME_STARTED)
        except Exception as e:
            self.log(
                'error',
                f'Error: Instance {self.container_name} FAILED to start container!\n',
            )
            self.close()
            raise e

    def _attach_to_container(self) -> None:
        self.container = self.docker_client.containers.get(self.container_name)
        if self.container.status == 'exited':
            self.container.start()

        config = self.container.attrs['Config']
        for env_var in config['Env']:
            if env_var.startswith('port='):
                self._host_port = int(env_var.split('port=')[1])
                self._container_port = self._host_port
            elif env_var.startswith('VSCODE_PORT='):
                self._vscode_port = int(env_var.split('VSCODE_PORT=')[1])

        self._app_ports = []
        exposed_ports = config.get('ExposedPorts')
        if exposed_ports:
            for exposed_port in exposed_ports.keys():
                exposed_port = int(exposed_port.split('/tcp')[0])
                if (
                    exposed_port != self._host_port
                    and exposed_port != self._vscode_port
                ):
                    self._app_ports.append(exposed_port)

        self.api_url = f'{self.config.sandbox.local_runtime_url}:{self._container_port}'
        self.log(
            'debug',
            f'attached to container: {self.container_name} {self._container_port} {self.api_url}',
        )

    @tenacity.retry(
        stop=tenacity.stop_after_delay(120) | stop_if_should_exit(),
        retry=tenacity.retry_if_exception(_is_retryablewait_until_alive_error),
        reraise=True,
        wait=tenacity.wait_fixed(2),
    )
    def wait_until_alive(self) -> None:
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

        self.check_if_alive()

    def close(self, rm_all_containers: bool | None = None) -> None:
        """Closes the DockerRuntime and associated objects.

        Parameters:
        - rm_all_containers (bool): Whether to remove all containers with the 'openhands-sandbox-' prefix
        """
        # If we're in attach_to_existing mode, don't close the container
        if self.attach_to_existing:
            self.log(
                'info',
                f'Not closing container for session {self.sid} (attach_to_existing=True)',
            )
            # Just clean up our reference to the container, but leave it running
            self.container = None
            super().close()
            return

        # Remove from running containers dictionary
        if self.sid in _RUNNING_CONTAINERS:
            del _RUNNING_CONTAINERS[self.sid]

        # Close log streamer if it exists
        if self.log_streamer:
            self.log_streamer.close()

        if rm_all_containers is None:
            rm_all_containers = self.config.sandbox.rm_all_containers

        if self.config.sandbox.keep_runtime_alive:
            super().close()
            return

        # Stop and remove the container
        if self.container:
            try:
                self.container.stop()
                self.container.remove(force=True)
                self.log(
                    'info', f'Container {self.container_name} stopped and removed.'
                )
            except docker.errors.NotFound:
                self.log('warning', f'Container {self.container_name} not found.')
            except Exception as e:
                self.log('error', f'Error stopping container: {e}')
            finally:
                self.container = None

        # If rm_all_containers is True, stop all containers with the prefix
        if rm_all_containers:
            close_prefix = CONTAINER_NAME_PREFIX
            stop_all_containers(close_prefix)

        # Release port locks
        self._release_port_locks()

        # Clean up warm containers if this is the last runtime being disconnected
        if not _RUNNING_CONTAINERS:
            self.log('info', 'No active containers, cleaning up warm containers')
            cleanup_warm_containers()

        super().close()

    def _release_port_locks(self) -> None:
        """Release all acquired port locks."""
        if self._host_port_lock:
            self._host_port_lock.release()
            self._host_port_lock = None
            logger.debug(f'Released host port lock for port {self._host_port}')

        if self._vscode_port_lock:
            self._vscode_port_lock.release()
            self._vscode_port_lock = None
            logger.debug(f'Released VSCode port lock for port {self._vscode_port}')

        for i, lock in enumerate(self._app_port_locks):
            if lock:
                lock.release()
                logger.debug(
                    f'Released app port lock for port {self._app_ports[i] if i < len(self._app_ports) else "unknown"}'
                )

        self._app_port_locks.clear()

    async def execute_action(self, action: Action) -> Observation:
        """Execute an action by sending it to the container."""
        if not self._runtime_initialized:
            raise AgentRuntimeDisconnectedError('Runtime not initialized')

        # Check if our container is still valid
        if self.container is None:
            # Check if there's a container in the global dictionary
            if self.sid in _RUNNING_CONTAINERS:
                self.container = _RUNNING_CONTAINERS[self.sid].container
            else:
                raise AgentRuntimeDisconnectedError('Container not found')

        # Execute the action using the parent class method
        try:
            # Send the action to the server
            # Handle different Action implementations
            if hasattr(action, 'to_dict'):
                action_dict = action.to_dict()
            elif hasattr(action, 'model_dump'):
                action_dict = action.model_dump()
            else:
                # Fallback to using the Action as a dictionary directly
                action_dict = action
            response = self._send_action_server_request(
                'POST',
                f'{self.action_execution_server_url}/action',
                json={'action': action_dict},
            )

            # After executing the action, check if we need to create more warm containers
            desired_num_warm_containers = int(
                os.getenv('DESIRED_NUM_WARM_CONTAINERS', '0')
            )
            if (
                desired_num_warm_containers > 0
                and len(_WARM_CONTAINERS) < desired_num_warm_containers
            ):
                self.log(
                    'info',
                    f'Creating a new warm container to maintain desired count of {desired_num_warm_containers}',
                )
                if self.runtime_container_image:
                    _create_warm_container_in_background(
                        self.config, self.plugins, self.runtime_container_image
                    )

            # Parse the observation based on available methods
            response_json = response.json()
            if hasattr(Observation, 'parse_obj'):
                return Observation.parse_obj(response_json)
            elif hasattr(Observation, 'model_validate'):
                return Observation.model_validate(response_json)
            else:
                # Fallback to direct instantiation
                return Observation(**response_json)
        except Exception as e:
            if _is_retryablewait_until_alive_error(e):
                self.log('error', f'Error executing action: {e}')
                self.log('info', 'Attempting to reconnect to runtime...')
                await call_sync_from_async(self.wait_until_alive)

                # Try again after reconnecting
                # Send the action to the server
                # Handle different Action implementations
                if hasattr(action, 'to_dict'):
                    action_dict = action.to_dict()
                elif hasattr(action, 'model_dump'):
                    action_dict = action.model_dump()
                else:
                    # Fallback to using the Action as a dictionary directly
                    action_dict = action
                response = self._send_action_server_request(
                    'POST',
                    f'{self.action_execution_server_url}/action',
                    json={'action': action_dict},
                )

                # Parse the observation based on available methods
                response_json = response.json()
                if hasattr(Observation, 'parse_obj'):
                    return Observation.parse_obj(response_json)
                elif hasattr(Observation, 'model_validate'):
                    return Observation.model_validate(response_json)
                else:
                    # Fallback to direct instantiation
                    return Observation(**response_json)
            raise

    def _is_port_in_use_docker(self, port: int) -> bool:
        containers = self.docker_client.containers.list()
        for container in containers:
            container_ports = container.ports
            if str(port) in str(container_ports):
                return True
        return False

    def _find_available_port_with_lock(
        self, port_range: tuple[int, int], max_attempts: int = 5
    ) -> tuple[int, PortLock | None]:
        """Find an available port with race condition protection.

        This method uses file-based locking to prevent multiple workers
        from allocating the same port simultaneously.

        Args:
            port_range: Tuple of (min_port, max_port)
            max_attempts: Maximum number of attempts to find a port

        Returns:
            Tuple of (port_number, port_lock) where port_lock may be None if locking failed
        """
        # Try to find and lock an available port
        result = find_available_port_with_lock(
            min_port=port_range[0],
            max_port=port_range[1],
            max_attempts=max_attempts,
            bind_address='0.0.0.0',
            lock_timeout=1.0,
        )

        if result is None:
            # Fallback to original method if port locking fails
            logger.warning(
                f'Port locking failed for range {port_range}, falling back to original method'
            )
            port = port_range[1]
            for _ in range(max_attempts):
                port = find_available_tcp_port(port_range[0], port_range[1])
                if not self._is_port_in_use_docker(port):
                    return port, None
            return port, None

        port, port_lock = result

        # Additional check with Docker to ensure port is not in use
        if self._is_port_in_use_docker(port):
            port_lock.release()
            # Try again with a different port
            logger.debug(f'Port {port} is in use by Docker, trying again')
            return self._find_available_port_with_lock(port_range, max_attempts - 1)

        return port, port_lock

    def _find_available_port(
        self, port_range: tuple[int, int], max_attempts: int = 5
    ) -> int:
        """Find an available port (legacy method for backward compatibility)."""
        port, _ = self._find_available_port_with_lock(port_range, max_attempts)
        return port

    @property
    def vscode_url(self) -> str | None:
        token = super().get_vscode_token()
        if not token:
            return None

        vscode_url = f'http://localhost:{self._vscode_port}/?tkn={token}&folder={self.config.workspace_mount_path_in_sandbox}'
        return vscode_url

    @property
    def web_hosts(self) -> dict[str, int]:
        hosts: dict[str, int] = {}

        host_addr = os.environ.get('DOCKER_HOST_ADDR', 'localhost')
        for port in self._app_ports:
            hosts[f'http://{host_addr}:{port}'] = port

        return hosts

    def pause(self) -> None:
        """Pause the runtime by stopping the container.

        This is different from container.stop() as it ensures environment variables are properly preserved.
        """
        if not self.container:
            raise RuntimeError('Container not initialized')

        # First, ensure all environment variables are properly persisted in .bashrc
        # This is already handled by add_env_vars in base.py

        # Stop the container
        self.container.stop()
        self.log('debug', f'Container {self.container_name} paused')

    def resume(self) -> None:
        """Resume the runtime by starting the container.

        This is different from container.start() as it ensures environment variables are properly restored.
        """
        if not self.container:
            raise RuntimeError('Container not initialized')

        # Start the container
        self.container.start()
        self.log('debug', f'Container {self.container_name} resumed')

        # Wait for the container to be ready
        self.wait_until_alive()

    @classmethod
    async def delete(cls, conversation_id: str) -> None:
        docker_client = cls._init_docker_client()
        try:
            container_name = CONTAINER_NAME_PREFIX + conversation_id
            container = docker_client.containers.get(container_name)
            container.remove(force=True)
        except docker.errors.APIError:
            pass
        except docker.errors.NotFound:
            pass
        finally:
            docker_client.close()

    def get_action_execution_server_startup_command(self) -> list[str]:
        return get_action_execution_server_startup_command(
            server_port=self._container_port,
            plugins=self.plugins,
            app_config=self.config,
            main_module=self.main_module,
        )


# Initialize the DockerRuntime class at the end of the file
DockerRuntime.initialize()
