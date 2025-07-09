"""Runtime pooling implementation for OpenHands.

This module provides a RuntimePool class that manages a pool of pre-connected runtime instances
to improve performance by avoiding the slow connect() process for each new runtime request.
"""

import asyncio
import os
import threading
from queue import Empty, Queue
from typing import Any, Callable

from openhands.core.config import OpenHandsConfig
from openhands.core.logger import openhands_logger as logger
from openhands.events import EventStream, EventStreamSubscriber
from openhands.integrations.provider import PROVIDER_TOKEN_TYPE

# Import get_runtime_cls inside functions to avoid circular import
from openhands.runtime.base import Runtime
from openhands.runtime.plugins import PluginRequirement


class RuntimePool:
    """A pool of pre-connected runtime instances for improved performance.

    This class manages a pool of runtime instances that are pre-connected and ready to use.
    When a runtime is requested, it's taken from the pool. When it's closed, it's returned
    to the pool for reuse.

    Environment variables:
    - POOLED_RUNTIME_CLASS: The name of the runtime class to pool
    - INITIAL_NUM_WARM_SERVERS: Number of runtimes to pre-create (default: 2)
    - TARGET_NUM_WARM_SERVERS: Target number of warm runtimes to maintain (default: 2)
    """

    _instance: 'RuntimePool | None' = None
    _lock = threading.Lock()

    def __init__(self):
        self.runtime_class_name = os.environ.get('POOLED_RUNTIME_CLASS', '')
        self.initial_num_warm = int(os.environ.get('INITIAL_NUM_WARM_SERVERS', '2'))
        self.target_num_warm = int(os.environ.get('TARGET_NUM_WARM_SERVERS', '2'))

        if not self.runtime_class_name:
            logger.info('POOLED_RUNTIME_CLASS not set, runtime pooling disabled')
            self.enabled = False
            return

        try:
            from openhands.runtime import get_runtime_cls

            self.runtime_cls = get_runtime_cls(self.runtime_class_name)
            self.enabled = True
            logger.info(f'Runtime pooling enabled for {self.runtime_class_name}')
        except Exception as e:
            logger.error(f'Failed to get runtime class {self.runtime_class_name}: {e}')
            self.enabled = False
            return

        self.pool: Queue[Runtime] = Queue()
        self.active_runtimes: set[Runtime] = set()
        self.shutdown_event = threading.Event()
        self.maintenance_thread: threading.Thread | None = None
        self._config: OpenHandsConfig | None = None

    @classmethod
    def get_instance(cls) -> 'RuntimePool':
        """Get the singleton RuntimePool instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def setup(self, config: OpenHandsConfig) -> None:
        """Set up the runtime pool with the given configuration."""
        if not self.enabled:
            return

        self._config = config

        # Call the runtime class setup method
        self.runtime_cls.setup(config)

        # Start the maintenance thread
        self.maintenance_thread = threading.Thread(
            target=self._maintenance_loop, daemon=True, name='RuntimePool-Maintenance'
        )
        self.maintenance_thread.start()

        # Pre-create initial warm runtimes
        self._create_warm_runtimes(self.initial_num_warm)

        logger.info(
            f'RuntimePool setup complete with {self.initial_num_warm} initial warm runtimes'
        )

    def teardown(self) -> None:
        """Tear down the runtime pool and clean up all resources."""
        if not self.enabled:
            return

        logger.info('Shutting down RuntimePool...')

        # Signal shutdown
        self.shutdown_event.set()

        # Wait for maintenance thread to finish
        if self.maintenance_thread and self.maintenance_thread.is_alive():
            self.maintenance_thread.join(timeout=5.0)

        # Close all pooled runtimes
        while not self.pool.empty():
            try:
                runtime = self.pool.get_nowait()
                runtime.close()
            except Empty:
                break

        # Close all active runtimes
        for runtime in list(self.active_runtimes):
            runtime.close()
        self.active_runtimes.clear()

        # Call the runtime class teardown method
        if self._config:
            self.runtime_cls.teardown(self._config)

        logger.info('RuntimePool shutdown complete')

    def get_runtime(
        self,
        config: OpenHandsConfig,
        event_stream: EventStream,
        sid: str = 'default',
        plugins: list[PluginRequirement] | None = None,
        env_vars: dict[str, str] | None = None,
        status_callback: Callable[[str, str, str], None] | None = None,
        attach_to_existing: bool = False,
        headless_mode: bool = True,
        user_id: str | None = None,
        git_provider_tokens: PROVIDER_TOKEN_TYPE | None = None,
        **kwargs: Any,
    ) -> Runtime:
        """Get a runtime from the pool or create a new one if pool is empty."""
        if not self.enabled:
            # If pooling is disabled, create runtime normally
            from openhands.runtime import get_runtime_cls

            runtime_cls = get_runtime_cls('local')  # Default to local runtime
            return runtime_cls(
                config=config,
                event_stream=event_stream,
                sid=sid,
                plugins=plugins,
                env_vars=env_vars,
                status_callback=status_callback,
                attach_to_existing=attach_to_existing,
                headless_mode=headless_mode,
                user_id=user_id,
                git_provider_tokens=git_provider_tokens,
                **kwargs,
            )

        # Try to get a runtime from the pool
        try:
            runtime = self.pool.get_nowait()
            logger.debug(f'Retrieved runtime from pool, pool size: {self.pool.qsize()}')
        except Empty:
            # Pool is empty, create a new runtime
            logger.debug('Pool empty, creating new runtime')
            runtime = self._create_runtime(
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
                **kwargs,
            )

        # Update runtime configuration for this session
        self._configure_runtime_for_session(
            runtime,
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

        self.active_runtimes.add(runtime)
        return runtime

    def return_runtime(self, runtime: Runtime) -> None:
        """Return a runtime to the pool for reuse."""
        if not self.enabled:
            runtime.close()
            return

        if runtime in self.active_runtimes:
            self.active_runtimes.remove(runtime)

        # Reset runtime to a clean state
        if self._reset_runtime(runtime):
            self.pool.put(runtime)
            logger.debug(f'Returned runtime to pool, pool size: {self.pool.qsize()}')
        else:
            # Runtime couldn't be reset, close it
            runtime.close()
            logger.debug('Runtime could not be reset, closed instead')

    def _create_runtime(
        self,
        config: OpenHandsConfig,
        event_stream: EventStream,
        sid: str = 'default',
        plugins: list[PluginRequirement] | None = None,
        env_vars: dict[str, str] | None = None,
        status_callback: Callable[[str, str, str], None] | None = None,
        attach_to_existing: bool = False,
        headless_mode: bool = True,
        user_id: str | None = None,
        git_provider_tokens: PROVIDER_TOKEN_TYPE | None = None,
        **kwargs: Any,
    ) -> Runtime:
        """Create and connect a new runtime instance."""
        runtime = self.runtime_cls(
            config=config,
            event_stream=event_stream,
            sid=sid,
            plugins=plugins,
            env_vars=env_vars,
            status_callback=status_callback,
            attach_to_existing=attach_to_existing,
            headless_mode=headless_mode,
            user_id=user_id,
            git_provider_tokens=git_provider_tokens,
            **kwargs,
        )

        # Connect the runtime
        asyncio.run(runtime.connect())

        return runtime

    def _configure_runtime_for_session(
        self,
        runtime: Runtime,
        config: OpenHandsConfig,
        event_stream: EventStream,
        sid: str,
        plugins: list[PluginRequirement] | None,
        env_vars: dict[str, str] | None,
        status_callback: Callable[[str, str, str], None] | None,
        attach_to_existing: bool,
        headless_mode: bool,
        user_id: str | None,
        git_provider_tokens: PROVIDER_TOKEN_TYPE | None,
    ) -> None:
        """Configure a pooled runtime for a specific session."""
        # Update runtime properties for this session
        runtime.sid = sid
        runtime.event_stream = event_stream
        runtime.status_callback = status_callback
        runtime.user_id = user_id
        runtime.git_provider_tokens = git_provider_tokens

        # Subscribe to the new event stream
        if event_stream:
            event_stream.subscribe(EventStreamSubscriber.RUNTIME, runtime.on_event, sid)

        # Add session-specific environment variables
        if env_vars:
            runtime.add_env_vars(env_vars)

    def _reset_runtime(self, runtime: Runtime) -> bool:
        """Reset a runtime to a clean state for reuse."""
        try:
            # Unsubscribe from the current event stream
            if runtime.event_stream:
                runtime.event_stream.unsubscribe(
                    EventStreamSubscriber.RUNTIME, runtime.sid
                )

            # Reset runtime properties
            runtime.sid = 'pooled'
            runtime.event_stream = None  # type: ignore[assignment]
            runtime.status_callback = None
            runtime.user_id = None
            runtime.git_provider_tokens = None

            # TODO: Add more cleanup logic here as needed
            # For example, clearing temporary files, resetting environment variables, etc.

            return True
        except Exception as e:
            logger.error(f'Failed to reset runtime: {e}')
            return False

    def _create_warm_runtimes(self, count: int) -> None:
        """Create warm runtimes and add them to the pool."""
        if not self._config:
            logger.warning('Cannot create warm runtimes: config not set')
            return

        for i in range(count):
            if self.shutdown_event.is_set():
                break

            try:
                # Create a minimal runtime for pooling
                # We need to create a dummy event stream for initialization
                from openhands.events.stream import EventStream as ES
                from openhands.storage import get_file_store

                file_store = get_file_store(
                    self._config.file_store, self._config.file_store_path
                )
                dummy_stream = ES(sid=f'warm-{i}', file_store=file_store)

                runtime = self._create_runtime(
                    config=self._config,
                    event_stream=dummy_stream,
                    sid=f'warm-{i}',
                    plugins=None,
                    env_vars=None,
                    status_callback=None,
                    attach_to_existing=False,
                    headless_mode=True,
                    user_id=None,
                    git_provider_tokens=None,
                )
                self.pool.put(runtime)
                logger.debug(f'Created warm runtime {i + 1}/{count}')
            except Exception as e:
                logger.error(f'Failed to create warm runtime {i + 1}: {e}')

    def _maintenance_loop(self) -> None:
        """Background thread that maintains the target number of warm runtimes."""
        logger.debug('RuntimePool maintenance thread started')

        while not self.shutdown_event.is_set():
            try:
                current_pool_size = self.pool.qsize()
                if current_pool_size < self.target_num_warm:
                    needed = self.target_num_warm - current_pool_size
                    logger.debug(
                        f'Pool has {current_pool_size} runtimes, creating {needed} more'
                    )
                    self._create_warm_runtimes(needed)

                # Sleep for a bit before checking again
                self.shutdown_event.wait(timeout=10.0)

            except Exception as e:
                logger.error(f'Error in RuntimePool maintenance loop: {e}')
                self.shutdown_event.wait(timeout=5.0)

        logger.debug('RuntimePool maintenance thread stopped')


class PooledRuntime(Runtime):
    """A proxy runtime that uses the RuntimePool for improved performance.

    This class acts as a proxy for another runtime object. When connect() is called,
    it grabs a runtime from the pool. When close() is called, it returns the runtime
    to the pool instead of actually closing it.
    """

    def __init__(
        self,
        config: OpenHandsConfig,
        event_stream: EventStream,
        sid: str = 'default',
        plugins: list[PluginRequirement] | None = None,
        env_vars: dict[str, str] | None = None,
        status_callback: Callable[[str, str, str], None] | None = None,
        attach_to_existing: bool = False,
        headless_mode: bool = True,
        user_id: str | None = None,
        git_provider_tokens: PROVIDER_TOKEN_TYPE | None = None,
        **kwargs: Any,
    ):
        # Store initialization parameters
        self._init_config = config
        self._init_event_stream = event_stream
        self._init_sid = sid
        self._init_plugins = plugins
        self._init_env_vars = env_vars
        self._init_status_callback = status_callback
        self._init_attach_to_existing = attach_to_existing
        self._init_headless_mode = headless_mode
        self._init_user_id = user_id
        self._init_git_provider_tokens = git_provider_tokens
        self._init_kwargs = kwargs

        self._actual_runtime: Runtime | None = None
        self._pool = RuntimePool.get_instance()

        # Initialize the base class with minimal setup
        super().__init__(
            config=config,
            event_stream=event_stream,
            sid=sid,
            plugins=plugins,
            env_vars=env_vars,
            status_callback=status_callback,
            attach_to_existing=attach_to_existing,
            headless_mode=headless_mode,
            user_id=user_id,
            git_provider_tokens=git_provider_tokens,
        )

    async def connect(self) -> None:
        """Get a runtime from the pool and connect to it."""
        if self._actual_runtime is not None:
            logger.warning('PooledRuntime.connect() called but already connected')
            return

        self._actual_runtime = self._pool.get_runtime(
            config=self._init_config,
            event_stream=self._init_event_stream,
            sid=self._init_sid,
            plugins=self._init_plugins,
            env_vars=self._init_env_vars,
            status_callback=self._init_status_callback,
            attach_to_existing=self._init_attach_to_existing,
            headless_mode=self._init_headless_mode,
            user_id=self._init_user_id,
            git_provider_tokens=self._init_git_provider_tokens,
            **self._init_kwargs,
        )

        # Copy important attributes from the actual runtime
        self._runtime_initialized = self._actual_runtime._runtime_initialized
        self.runtime_status = self._actual_runtime.runtime_status

    def close(self) -> None:
        """Return the runtime to the pool instead of closing it."""
        if self._actual_runtime is None:
            return

        self._pool.return_runtime(self._actual_runtime)
        self._actual_runtime = None
        self._runtime_initialized = False

    def _ensure_connected(self) -> Runtime:
        """Ensure we have a connected runtime and return it."""
        if self._actual_runtime is None:
            raise RuntimeError('PooledRuntime not connected. Call connect() first.')
        return self._actual_runtime

    # Delegate all other methods to the actual runtime
    def __getattr__(self, name: str) -> Any:
        """Delegate attribute access to the actual runtime."""
        if name.startswith('_'):
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{name}'"
            )
        return getattr(self._ensure_connected(), name)

    # Override abstract methods to delegate to actual runtime
    def get_mcp_config(self, extra_stdio_servers=None):
        return self._ensure_connected().get_mcp_config(extra_stdio_servers)

    def run(self, action):
        return self._ensure_connected().run(action)

    def run_ipython(self, action):
        return self._ensure_connected().run_ipython(action)

    def read(self, action):
        return self._ensure_connected().read(action)

    def write(self, action):
        return self._ensure_connected().write(action)

    def edit(self, action):
        return self._ensure_connected().edit(action)

    def browse(self, action):
        return self._ensure_connected().browse(action)

    def browse_interactive(self, action):
        return self._ensure_connected().browse_interactive(action)

    async def call_tool_mcp(self, action):
        return await self._ensure_connected().call_tool_mcp(action)

    def copy_to(self, host_src: str, sandbox_dest: str, recursive: bool = False):
        return self._ensure_connected().copy_to(host_src, sandbox_dest, recursive)

    def list_files(self, path: str | None = None) -> list[str]:
        return self._ensure_connected().list_files(path)

    def copy_from(self, path: str):
        return self._ensure_connected().copy_from(path)

    @property
    def workspace_root(self):
        return self._ensure_connected().workspace_root

    @property
    def vscode_url(self):
        return self._ensure_connected().vscode_url

    @classmethod
    def setup(cls, config: OpenHandsConfig):
        """Set up the runtime pool."""
        RuntimePool.get_instance().setup(config)

    @classmethod
    def teardown(cls, config: OpenHandsConfig):
        """Tear down the runtime pool."""
        RuntimePool.get_instance().teardown()
