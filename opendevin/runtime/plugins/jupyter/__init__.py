import os
import subprocess
import time
from dataclasses import dataclass

from opendevin.events.action import Action, IPythonRunCellAction
from opendevin.events.observation import IPythonRunCellObservation, Observation
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

    def initialize(self, kernel_id: str = 'opendevin-default'):
        self.kernel_gateway_port = find_available_tcp_port()
        self.kernel_id = kernel_id
        self.gateway_process = subprocess.Popen(
            [
                '/opendevin/miniforge3/bin/mamba',
                'run',
                '-n',
                'base',
                'poetry',
                'run',
                'jupyter',
                'kernelgateway',
                '--KernelGatewayApp.ip=0.0.0.0',
                f'--KernelGatewayApp.port={self.kernel_gateway_port}',
            ],
            stderr=subprocess.STDOUT,
        )
        # read stdout until the kernel gateway is ready
        while True and self.gateway_process.stdout is not None:
            line = self.gateway_process.stdout.readline().decode('utf-8')
            if 'at' in line:
                break
            time.sleep(1)
            print('Waiting for jupyter kernel gateway to start...')

    async def run(self, action: Action) -> Observation:
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
