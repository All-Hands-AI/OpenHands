import os
import subprocess
import time
import uuid
from dataclasses import dataclass

from openhands.core.logger import openhands_logger as logger
from openhands.runtime.plugins.requirement import Plugin, PluginRequirement
from openhands.runtime.utils.system import check_port_available
from openhands.utils.shutdown_listener import should_continue


@dataclass
class VSCodeRequirement(PluginRequirement):
    name: str = 'vscode'


class VSCodePlugin(Plugin):
    name: str = 'vscode'
    vscode_port: int | None = None
    vscode_connection_token: str | None = None

    async def initialize(self, username: str):
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

        self.gateway_process = subprocess.Popen(
            cmd,
            stderr=subprocess.STDOUT,
            shell=True,
        )
        # read stdout until the kernel gateway is ready
        output = ''
        while should_continue() and self.gateway_process.stdout is not None:
            line = self.gateway_process.stdout.readline().decode('utf-8')
            print(line)
            output += line
            if 'at' in line:
                break
            time.sleep(1)
            logger.debug('Waiting for VSCode server to start...')

        logger.debug(
            f'VSCode server started at port {self.vscode_port}. Output: {output}'
        )
