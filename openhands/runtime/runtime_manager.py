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
        logger.info(
            f'Created runtime with ID: {sid}. There are now {len(self._runtimes)} runtimes active.'
        )
        return runtime

    def get_runtime(self, sid: str) -> Optional[Runtime]:
        return self._runtimes.get(sid)

    def list_runtimes(self) -> List[str]:
        return list(self._runtimes.keys())

    def destroy_runtime(self, sid: str) -> bool:
        runtime = self._runtimes.get(sid)
        if runtime:
            del self._runtimes[sid]
            runtime.close()
            logger.info(f'Destroyed runtime with ID: {sid}')
            return True
        return False

    async def destroy_all_runtimes(self):
        for runtime_id in list(self._runtimes.keys()):
            self.destroy_runtime(runtime_id)
