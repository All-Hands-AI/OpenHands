from typing import Dict, List, Optional

from openhands.core.config import AppConfig
from openhands.core.exceptions import AgentRuntimeUnavailableError
from openhands.core.logger import openhands_logger as logger
from openhands.events import EventStream
from openhands.runtime import get_runtime_cls
from openhands.runtime.base import Runtime
from openhands.runtime.plugins import PluginRequirement
from openhands.runtime.utils.singleton import Singleton


class RuntimeManager(metaclass=Singleton):
    def __init__(self, config: AppConfig):
        self._runtimes: Dict[str, Runtime] = {}
        self._config = config

    @property
    def config(self) -> AppConfig:
        return self._config

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

    async def get_runtime(
        self,
        runtime_id: str,
        create_if_not_exists: bool = False,
        event_stream: Optional[EventStream] = None,
        plugins: Optional[List[PluginRequirement]] = None,
        env_vars: Optional[Dict[str, str]] = None,
        status_callback=None,
        attach_to_existing: bool = True,
        headless_mode: bool = False,
    ) -> Optional[Runtime]:
        """Get a runtime by ID, optionally creating it if it doesn't exist.

        Args:
            runtime_id: The ID of the runtime to get
            create_if_not_exists: If True and no runtime exists, create one
            event_stream: Required if create_if_not_exists is True
            plugins: Optional plugins for the new runtime
            env_vars: Optional environment variables for the new runtime
            status_callback: Optional callback for runtime status updates
            attach_to_existing: Whether to attach to an existing runtime (default True)
            headless_mode: Whether to run in headless mode (default False)

        Returns:
            The runtime if it exists or was created, None otherwise

        Raises:
            ValueError: If create_if_not_exists is True but event_stream is None
        """
        runtime = self._runtimes.get(runtime_id)
        if runtime is None and create_if_not_exists:
            if event_stream is None:
                raise ValueError(
                    'event_stream is required when create_if_not_exists is True'
                )
            try:
                runtime = await self.create_runtime(
                    event_stream=event_stream,
                    sid=runtime_id,
                    plugins=plugins,
                    env_vars=env_vars,
                    status_callback=status_callback,
                    attach_to_existing=attach_to_existing,
                    headless_mode=headless_mode,
                )
            except AgentRuntimeUnavailableError:
                return None
        return runtime

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
