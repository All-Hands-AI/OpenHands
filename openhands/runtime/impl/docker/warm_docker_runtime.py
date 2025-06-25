import asyncio
import threading
import uuid
from typing import Optional

from openhands.core.config import OpenHandsConfig
from openhands.core.logger import openhands_logger as logger
from openhands.events import EventStream
from openhands.runtime.impl.docker.docker_runtime import (
    CONTAINER_NAME_PREFIX,
    DockerRuntime,
)
from openhands.runtime.plugins import PluginRequirement
from openhands.runtime.runtime_status import RuntimeStatus


class WarmDockerRuntime(DockerRuntime):
    """A Docker runtime implementation that keeps a pool of warm containers.

    This runtime maintains a pool of pre-initialized DockerRuntime instances to reduce
    the time needed to connect to a new runtime. When connect() is called, if a matching
    warm runtime is available, it will be returned instead of creating a new one.

    Args:
        config (OpenHandsConfig): The application configuration.
        event_stream (EventStream): The event stream to subscribe to.
        sid (str, optional): The session ID. Defaults to 'default'.
        plugins (list[PluginRequirement] | None, optional): List of plugin requirements. Defaults to None.
        env_vars (dict[str, str] | None, optional): Environment variables to set. Defaults to None.
        status_callback (Callable | None, optional): Callback for status updates. Defaults to None.
        attach_to_existing (bool, optional): Whether to attach to an existing container. Defaults to False.
        headless_mode (bool, optional): Whether to run in headless mode. Defaults to True.
        user_id (str | None, optional): User ID. Defaults to None.
        git_provider_tokens (PROVIDER_TOKEN_TYPE | None, optional): Git provider tokens. Defaults to None.
        main_module (str, optional): Main module to run. Defaults to DEFAULT_MAIN_MODULE.
    """

    # Static pool of warm runtimes
    _warm_pool: list[DockerRuntime] = []

    # Number of warm containers to keep in the pool
    _warm_pool_size: int = 2

    # Lock for thread safety when accessing the warm pool
    _pool_lock = threading.Lock()

    @classmethod
    def set_warm_pool_size(cls, size: int) -> None:
        """Set the number of warm containers to keep in the pool.

        Args:
            size (int): The number of warm containers to keep in the pool.
        """
        cls._warm_pool_size = size

    @classmethod
    def get_warm_pool_size(cls) -> int:
        """Get the number of warm containers to keep in the pool.

        Returns:
            int: The number of warm containers to keep in the pool.
        """
        return cls._warm_pool_size

    @classmethod
    def _create_warm_runtime(
        cls,
        config: OpenHandsConfig,
        event_stream: EventStream,
        plugins: Optional[list[PluginRequirement]] = None,
        env_vars: Optional[dict[str, str]] = None,
        headless_mode: bool = True,
    ) -> DockerRuntime:
        """Create a new warm runtime with a random session ID.

        Args:
            config (OpenHandsConfig): The application configuration.
            event_stream (EventStream): The event stream to subscribe to.
            plugins (Optional[List[PluginRequirement]], optional): List of plugin requirements. Defaults to None.
            env_vars (Optional[Dict[str, str]], optional): Environment variables to set. Defaults to None.
            headless_mode (bool, optional): Whether to run in headless mode. Defaults to True.

        Returns:
            DockerRuntime: A new warm runtime.
        """
        # Generate a random session ID for the warm runtime
        warm_sid = f'warm-{str(uuid.uuid4())}'

        # Create a new DockerRuntime instance
        runtime = DockerRuntime(
            config=config,
            event_stream=event_stream,
            sid=warm_sid,
            plugins=plugins,
            env_vars=env_vars,
            headless_mode=headless_mode,
        )

        return runtime

    @classmethod
    def _get_plugin_env_key(
        cls,
        plugins: Optional[list[PluginRequirement]],
        env_vars: Optional[dict[str, str]],
    ) -> str:
        """Generate a key for matching plugins and environment variables.

        Args:
            plugins (Optional[List[PluginRequirement]]): List of plugin requirements.
            env_vars (Optional[Dict[str, str]]): Environment variables.

        Returns:
            str: A string key representing the plugins and environment variables.
        """
        plugin_names = sorted([p.name for p in (plugins or [])])
        env_items = sorted([(k, v) for k, v in (env_vars or {}).items()])

        return (
            f'{",".join(plugin_names)}|{",".join([f"{k}={v}" for k, v in env_items])}'
        )

    @classmethod
    def _find_matching_warm_runtime(
        cls,
        plugins: Optional[list[PluginRequirement]],
        env_vars: Optional[dict[str, str]],
    ) -> Optional[DockerRuntime]:
        """Find a matching warm runtime in the pool.

        Args:
            plugins (Optional[List[PluginRequirement]]): List of plugin requirements.
            env_vars (Optional[Dict[str, str]]): Environment variables.

        Returns:
            Optional[DockerRuntime]: A matching warm runtime, or None if no match is found.
        """
        target_key = cls._get_plugin_env_key(plugins, env_vars)

        with cls._pool_lock:
            for i, runtime in enumerate(cls._warm_pool):
                runtime_key = cls._get_plugin_env_key(
                    runtime.plugins, runtime.initial_env_vars
                )
                if runtime_key == target_key:
                    # Remove the runtime from the pool
                    return cls._warm_pool.pop(i)

        return None

    @classmethod
    def _replenish_warm_pool(
        cls,
        config: OpenHandsConfig,
        event_stream: EventStream,
    ) -> None:
        """Replenish the warm pool to maintain the desired size.

        Args:
            config (OpenHandsConfig): The application configuration.
            event_stream (EventStream): The event stream to subscribe to.
        """
        with cls._pool_lock:
            current_size = len(cls._warm_pool)

            # If the pool is already at or above the desired size, do nothing
            if current_size >= cls._warm_pool_size:
                return

            # Add new warm runtimes to the pool
            for _ in range(cls._warm_pool_size - current_size):
                try:
                    # Create a new warm runtime
                    runtime = cls._create_warm_runtime(config, event_stream)

                    # Connect to the runtime asynchronously
                    asyncio.create_task(runtime.connect())

                    # Add the runtime to the pool
                    cls._warm_pool.append(runtime)

                    logger.debug(f'Added new warm runtime to pool: {runtime.sid}')
                except Exception as e:
                    logger.error(f'Failed to create warm runtime: {str(e)}')

    async def connect(self) -> None:
        """Connect to the runtime.

        If a matching warm runtime is available in the pool, it will be used.
        Otherwise, a new runtime will be created.
        """
        # Try to find a matching warm runtime
        warm_runtime = self._find_matching_warm_runtime(
            self.plugins, self.initial_env_vars
        )

        if warm_runtime:
            logger.info(f'Using warm runtime {warm_runtime.sid} for session {self.sid}')

            # The warm runtime is already connected, so we just need to update its session ID
            # and rename the container
            self.container = warm_runtime.container

            if self.container:
                # Rename the container to match the new session ID
                old_name = self.container.name
                new_name = CONTAINER_NAME_PREFIX + self.sid

                try:
                    # Rename the container
                    self.container.rename(new_name)
                    logger.debug(f'Renamed container from {old_name} to {new_name}')

                    # Update container reference
                    self.container = self.docker_client.containers.get(new_name)
                except Exception as e:
                    logger.error(f'Failed to rename container: {str(e)}')

            # Copy over the necessary attributes from the warm runtime
            self._host_port = warm_runtime._host_port
            self._container_port = warm_runtime._container_port
            self._vscode_port = warm_runtime._vscode_port
            self._app_ports = warm_runtime._app_ports
            self.api_url = warm_runtime.api_url
            self._runtime_initialized = True

            # Set the runtime status to ready
            self.set_runtime_status(RuntimeStatus.READY)
        else:
            # No matching warm runtime found, create a new one
            logger.info(
                f'No matching warm runtime found for session {self.sid}, creating new runtime'
            )
            await super().connect()

        # Replenish the warm pool
        self._replenish_warm_pool(self.config, self.event_stream)

    def close(self, rm_all_containers: bool | None = None) -> None:
        """Close the runtime.

        Args:
            rm_all_containers (bool | None, optional): Whether to remove all containers. Defaults to None.
        """
        # Call the parent close method
        super().close(rm_all_containers)

        # Replenish the warm pool
        self._replenish_warm_pool(self.config, self.event_stream)
