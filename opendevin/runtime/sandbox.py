import copy
from abc import ABC, abstractmethod

from opendevin.core.config import SandboxConfig
from opendevin.core.schema import CancellableStream
from opendevin.runtime.plugins.mixin import PluginMixin


class Sandbox(ABC, PluginMixin):
    _env: dict[str, str] = {}
    is_initial_session: bool = True

    def __init__(self, config: SandboxConfig):
        self.config = copy.deepcopy(config)
        self.initialize_plugins: bool = config.initialize_plugins

    @abstractmethod
    def execute(
        self, cmd: str, stream: bool = False, timeout: int | None = None
    ) -> tuple[int, str | CancellableStream]:
        pass

    @abstractmethod
    def close(self):
        pass

    @abstractmethod
    def copy_to(self, host_src: str, sandbox_dest: str, recursive: bool = False):
        pass

    @abstractmethod
    def get_working_directory(self):
        pass
