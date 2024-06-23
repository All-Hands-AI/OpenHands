import json
import os
from abc import ABC, abstractmethod

from opendevin.core.config import config
from opendevin.core.schema import CancellableStream
from opendevin.runtime.plugins.mixin import PluginMixin
from opendevin.runtime.utils.async_utils import async_to_sync


class Sandbox(ABC, PluginMixin):
    _env: dict[str, str] = {}
    is_initial_session: bool = True

    def __init__(self, **kwargs):
        self._env = {}
        if isinstance(config.sandbox.env, dict):
            self._env = config.sandbox.env.copy()
        for key, value in self._env.items():
            self.add_to_env(key, value)

        try:
            for key, value in os.environ.items():
                if key.startswith('SANDBOX_ENV_'):
                    sandbox_key = key.removeprefix('SANDBOX_ENV_')
                    self.add_to_env(sandbox_key, value)
        except Exception:
            pass

        if config.enable_auto_lint:
            self.add_to_env('ENABLE_AUTO_LINT', 'true')
        self.initialize_plugins: bool = config.initialize_plugins

    def add_to_env(self, key: str, value: str):
        self._env[key] = value
        # Note: json.dumps gives us nice escaping for free
        self.execute(f'export {key}={json.dumps(value)}')

    @abstractmethod
    @async_to_sync
    def execute(
        self, cmd: str, stream: bool = False, timeout: int | None = None
    ) -> tuple[int, str | CancellableStream]:
        pass

    @abstractmethod
    async def execute_async(
        self, cmd: str, stream: bool = False, timeout: int | None = None
    ) -> tuple[int, str | CancellableStream]:
        pass

    @abstractmethod
    def close(self):
        pass

    @abstractmethod
    @async_to_sync
    def copy_to(self, host_src: str, sandbox_dest: str, recursive: bool = False):
        pass

    @abstractmethod
    async def copy_to_async(
        self, host_src: str, sandbox_dest: str, recursive: bool = False
    ):
        pass

    @abstractmethod
    def get_working_directory(self):
        pass
