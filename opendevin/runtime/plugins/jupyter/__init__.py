import os
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
    sandbox_dest: str = '/opendevin/plugins/'
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
                'export PYTHONPATH=/opendevin/code/opendevin/runtime/plugins/agent_skills:$PYTHONPATH;\n'
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
        output = ''
        while True and self.gateway_process.stdout is not None:
            line = self.gateway_process.stdout.readline().decode('utf-8')
            output += line
            if 'at' in line:
                break
            time.sleep(1)
            logger.debug('Waiting for jupyter kernel gateway to start...')

        logger.info(
            f'Jupyter kernel gateway started at port {self.kernel_gateway_port}. Output: {output}'
        )

    async def _run(self, action: Action) -> IPythonRunCellObservation:
        """Internal method to run a code cell in the jupyter kernel."""
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
        output = await self.kernel.execute(action.code, timeout=action.timeout)
        return IPythonRunCellObservation(
            content=output,
            code=action.code,
        )

    async def run(self, action: Action) -> IPythonRunCellObservation:
        obs = await self._run(action)
        return obs
