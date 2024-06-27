# This file is deprecated and will be removed in the future. PLS DONOT review.
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
        self.websocket = None
        self.loop = asyncio.get_event_loop()
        self.loop.run_until_complete(self.connect())

    def add_to_env(self, key: str, value: str):
        self._env[key] = value
        # Note: json.dumps gives us nice escaping for free
        self.execute(f'export {key}={json.dumps(value)}')

    async def connect(self):
        self.websocket = await websockets.connect(self.uri)

    async def send_and_receive(self, cmd):
        if self.websocket is None:
            raise Exception("WebSocket is not connected.")
        print(cmd)
        await self.websocket.send(cmd)
        output = await self.websocket.recv()
        print(output)
        return output

    def execute(
        self, cmd: str, stream: bool = False, timeout: int | None = None
    ) -> tuple[int, str | CancellableStream]:
        output = self.loop.run_until_complete(self.send_and_receive(cmd))
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

    async def close(self):
        if self.websocket is not None:
            await self.websocket.close()

    def copy_to(self, host_src: str, sandbox_dest: str, recursive: bool = False):
        raise NotImplementedError

    def get_working_directory(self):
        pass


if __name__ == "__main__":
    sandbox = WebSocketBox()
    sandbox.execute('ls')
    sandbox.execute('pwd')
