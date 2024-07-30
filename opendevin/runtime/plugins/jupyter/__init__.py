import os
import selectors
import subprocess
import time
from dataclasses import dataclass

from opendevin.core.logger import opendevin_logger as logger
from opendevin.events.action import Action, IPythonRunCellAction
from opendevin.events.observation import IPythonRunCellObservation
from opendevin.runtime.plugins.requirement import Plugin, PluginRequirement
from opendevin.runtime.utils import find_available_tcp_port

from .execute_server import JupyterKernel


@dataclass
class JupyterRequirement(PluginRequirement):
    name: str = 'jupyter'
    host_src: str = os.path.dirname(
        os.path.abspath(__file__)
    )  # The directory of this file (opendevin/runtime/plugins/jupyter)
    sandbox_dest: str = '/opendevin/plugins/jupyter'
    bash_script_path: str = 'setup.sh'

    # ================================================================
    # Plugin methods, which will ONLY be used in the runtime client
    # running inside docker
    # ================================================================


class JupyterPlugin(Plugin):
    name: str = 'jupyter'

    async def initialize(self, username: str, kernel_id: str = 'opendevin-default'):
        self.kernel_gateway_port = find_available_tcp_port()
        self.kernel_id = kernel_id
        self.gateway_process = subprocess.Popen(
            (
                f"su - {username} -s /bin/bash << 'EOF'\n"
                'cd /opendevin/code\n'
                'export POETRY_VIRTUALENVS_PATH=/opendevin/poetry;\n'
                '/opendevin/miniforge3/bin/mamba run -n base '
                'poetry run jupyter kernelgateway '
                '--KernelGatewayApp.ip=0.0.0.0 '
                f'--KernelGatewayApp.port={self.kernel_gateway_port}\n'
                'EOF'
            ),
            stderr=subprocess.STDOUT,
            shell=True,
        )
        # read stdout until the kernel gateway is ready
        elapsed_time: int = 0
        start_time = time.time()
        timeout = 30  # 30 seconds timeout
        output = ''

        if self.gateway_process.stdout is None:
            raise RuntimeError('Failed to capture stdout from the gateway process')

        stdout = self.gateway_process.stdout  # Remove the cast
        sel = selectors.DefaultSelector()
        sel.register(stdout, selectors.EVENT_READ)

        while time.time() - start_time < timeout:
            events = sel.select(timeout=1)  # Wait for up to 1 second
            if events:
                line = stdout.readline().decode('utf-8')
                if line:
                    output += line
                    if 'at' in line:
                        break
            elapsed_time = int(time.time() - start_time)  # Change type hint to float
            logger.debug(
                f'Waiting for jupyter kernel gateway to start... (Elapsed time: {elapsed_time}s)'
            )

        sel.close()

        if time.time() - start_time >= timeout:
            logger.error(
                f'Timeout waiting for jupyter kernel gateway to start after {timeout} seconds'
            )
            # Handle the timeout case (e.g., raise an exception or clean up)
        logger.info(
            f'Jupyter kernel gateway started at port {self.kernel_gateway_port} after {elapsed_time}s. Output: {output}'
        )

    async def run(self, action: Action) -> IPythonRunCellObservation:
        if not isinstance(action, IPythonRunCellAction):
            raise ValueError(
                f'Jupyter plugin only supports IPythonRunCellAction, but got {action}'
            )

        if not hasattr(self, 'kernel'):
            self.kernel = JupyterKernel(
                f'localhost:{self.kernel_gateway_port}', self.kernel_id
            )

        if not self.kernel.initialized:
            await self.kernel.initialize()
        output = await self.kernel.execute(action.code)
        return IPythonRunCellObservation(
            content=output,
            code=action.code,
        )
