import asyncio
import json
import os

import websockets

from opendevin.core.config import config
from opendevin.core.schema import CancellableStream
from opendevin.runtime.docker.process import Process
from opendevin.runtime.sandbox import Sandbox


class WebSocketBox(Sandbox):
    _env: dict[str, str] = {}
    is_initial_session: bool = True
    uri = 'ws://localhost:8080'

    def __init__(self, **kwargs):
        for key in os.environ:
            if key.startswith('SANDBOX_ENV_'):
                sandbox_key = key.removeprefix('SANDBOX_ENV_')
                self.add_to_env(sandbox_key, os.environ[key])
        if config.enable_auto_lint:
            self.add_to_env('ENABLE_AUTO_LINT', 'true')
        self.initialize_plugins: bool = config.initialize_plugins
        self.websocket = websockets.connect(self.uri)

    def add_to_env(self, key: str, value: str):
        self._env[key] = value
        # Note: json.dumps gives us nice escaping for free
        self.execute(f'export {key}={json.dumps(value)}')

    async def send_and_receive(self, cmd):
        await self.websocket.send(cmd)
        output = await self.websocket.recv()
        return output

    def execute(
        self, cmd: str, stream: bool = False, timeout: int | None = None
    ) -> tuple[int, str | CancellableStream]:
        output = asyncio.run(self.send_and_receive(cmd))
        exit_code = output[-1].strip()
        print('Exit Code:', exit_code)
        print(output)
        return exit_code, output

    def execute_in_background(self, cmd: str) -> Process:
        raise NotImplementedError

    def kill_background(self, id: int) -> Process:
        raise NotImplementedError

    def read_logs(self, id: int) -> str:
        raise NotImplementedError

    def close(self):
        self.websocket.close()

    def copy_to(self, host_src: str, sandbox_dest: str, recursive: bool = False):
        raise NotImplementedError

    def get_working_directory(self):
        pass
