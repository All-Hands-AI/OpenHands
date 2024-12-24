from typing import Dict, Optional

from openhands.core.config import AppConfig
from openhands.core.logger import openhands_logger as logger
from openhands.events import EventStream
from openhands.runtime.base import Runtime
from openhands.runtime.plugins import PluginRequirement
from openhands.runtime.utils.singleton import Singleton


class RuntimeManager(metaclass=Singleton):
    """Manages all active runtimes in memory.
    
    This class is a singleton to ensure there's only one instance managing all runtimes.
    """

    def __init__(self):
        self._runtimes: Dict[str, Runtime] = {}

    def create_runtime(
        self,
        runtime_cls: type[Runtime],
        config: AppConfig,
        event_stream: EventStream,
        sid: str = "default",
        plugins: list[PluginRequirement] | None = None,
        env_vars: dict[str, str] | None = None,
        status_callback: Optional[callable] = None,
        attach_to_existing: bool = False,
        headless_mode: bool = False,
    ) -> Runtime:
        """Creates a new runtime instance and stores it in memory.
        
        If a runtime with the same sid already exists, it will be closed before creating a new one.
        """
        if sid in self._runtimes:
            logger.warning(f"Runtime with sid {sid} already exists. Closing it before creating a new one.")
            self.delete_runtime(sid)

        runtime = runtime_cls(
            config=config,
            event_stream=event_stream,
            sid=sid,
            plugins=plugins,
            env_vars=env_vars,
            status_callback=status_callback,
            attach_to_existing=attach_to_existing,
            headless_mode=headless_mode,
        )
        self._runtimes[sid] = runtime
        return runtime

    def get_runtime(self, sid: str) -> Optional[Runtime]:
        """Gets a runtime by its session id."""
        return self._runtimes.get(sid)

    def delete_runtime(self, sid: str) -> None:
        """Deletes a runtime by its session id.
        
        If the runtime exists, it will be closed before being deleted.
        """
        if sid in self._runtimes:
            runtime = self._runtimes[sid]
            runtime.close()
            del self._runtimes[sid]

    def close_all(self) -> None:
        """Closes and deletes all active runtimes."""
        for sid in list(self._runtimes.keys()):
            self.delete_runtime(sid)