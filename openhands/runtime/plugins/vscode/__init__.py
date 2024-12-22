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

    async def initialize(self, username: str):
        self.vscode_port = int(os.environ['VSCODE_PORT'])
        self.vscode_connection_token = str(uuid.uuid4())
        assert check_port_available(self.vscode_port)
        cmd = (
            f"su - {username} -s /bin/bash << 'EOF'\n"
            f'sudo chown -R {username}:{username} /openhands/.openvscode-server\n'
            'cd /workspace\n'
            f'exec /openhands/.openvscode-server/bin/openvscode-server --host 0.0.0.0 --connection-token {self.vscode_connection_token} --port {self.vscode_port}\n'
            'EOF'
        )
        print(cmd)
        self.gateway_process = subprocess.Popen(
            cmd,
            stderr=subprocess.STDOUT,
            shell=True,
        )
        # Wait for the VSCode server to start and be ready
        output = ''
        start_time = time.time()
        timeout = 30  # 30 seconds timeout
        
        while should_continue() and time.time() - start_time < timeout:
            if not check_port_available(self.vscode_port):
                # Port is in use, which means server is running
                logger.debug(f'VSCode server started at port {self.vscode_port}')
                return
            time.sleep(1)
            logger.debug('Waiting for VSCode server to start...')

        if check_port_available(self.vscode_port):
            logger.error('VSCode server failed to start within timeout period')
            raise RuntimeError('VSCode server failed to start within timeout period')
