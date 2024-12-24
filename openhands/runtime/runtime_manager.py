from typing import Dict, List, Optional, Type

from openhands.core.config import AppConfig
from openhands.core.exceptions import AgentRuntimeUnavailableError
from openhands.core.logger import openhands_logger as logger
from openhands.events import EventStream
from openhands.runtime.base import Runtime
from openhands.runtime.plugins import PluginRequirement
from openhands.utils.singleton import Singleton


class RuntimeManager(metaclass=Singleton):
    def __init__(self):
        self._runtimes: Dict[str, Runtime] = {}

    async def create_runtime(
        self,
        runtime_class: Type[Runtime],
        config: AppConfig,
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

        runtime = runtime_class(
            config=config,
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

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        for runtime_id in list(self._runtimes.keys()):
            self.destroy_runtime(runtime_id)
