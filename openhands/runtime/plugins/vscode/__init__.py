import asyncio
import os
import uuid
from dataclasses import dataclass
from typing import Optional

from openhands.core.logger import openhands_logger as logger
from openhands.events.action import Action
from openhands.events.observation import Observation
from openhands.runtime.plugins.requirement import Plugin, PluginRequirement
from openhands.runtime.utils.system import check_port_available
from openhands.utils.shutdown_listener import should_continue


@dataclass
class VSCodeRequirement(PluginRequirement):
    name: str = 'vscode'


class VSCodePlugin(Plugin):
    name: str = 'vscode'
    vscode_port: Optional[int] = None
    vscode_connection_token: Optional[str] = None
    gateway_process: asyncio.subprocess.Process

    async def initialize(self, username: str) -> None:
        if username not in ['root', 'openhands']:
            self.vscode_port = None
            self.vscode_connection_token = None
            logger.warning(
                'VSCodePlugin is only supported for root or openhands user. '
                'It is not yet supported for other users (i.e., when running LocalRuntime).'
            )
            return

        self.vscode_port = int(os.environ['VSCODE_PORT'])
        self.vscode_connection_token = str(uuid.uuid4())
        assert check_port_available(self.vscode_port)
        cmd = (
            f"su - {username} -s /bin/bash << 'EOF'\n"
            f'sudo chown -R {username}:{username} /openhands/.openvscode-server\n'
            'cd /workspace\n'
            f'exec /openhands/.openvscode-server/bin/openvscode-server --host 0.0.0.0 --connection-token {self.vscode_connection_token} --port {self.vscode_port} --disable-workspace-trust\n'
            'EOF'
        )

        # Using asyncio.create_subprocess_shell instead of subprocess.Popen
        # to avoid ASYNC101 linting error
        self.gateway_process = await asyncio.create_subprocess_shell(
            cmd,
            stderr=asyncio.subprocess.STDOUT,
            stdout=asyncio.subprocess.PIPE,
        )
        # read stdout until the kernel gateway is ready
        output = ''
        while should_continue() and self.gateway_process.stdout is not None:
            line_bytes = await self.gateway_process.stdout.readline()
            line = line_bytes.decode('utf-8')
            print(line)
            output += line
            if 'at' in line:
                break
            await asyncio.sleep(1)
            logger.debug('Waiting for VSCode server to start...')

        logger.debug(
            f'VSCode server started at port {self.vscode_port}. Output: {output}'
        )

    async def run(self, action: Action) -> Observation:
        """Run the plugin for a given action."""
        raise NotImplementedError('VSCodePlugin does not support run method')
