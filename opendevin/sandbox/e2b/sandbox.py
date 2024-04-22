from typing import Dict, Tuple
from e2b import Sandbox as E2BSandbox
from e2b.sandbox.exception import (
    TimeoutException,
)

from opendevin import config
from opendevin.logger import opendevin_logger as logger
from opendevin.sandbox.sandbox import Sandbox
from opendevin.sandbox.e2b.process import E2BProcess
from opendevin.sandbox.process import Process


class E2BBox(Sandbox):
    closed = False
    cur_background_id = 0
    background_commands: Dict[int, Process] = {}

    def __init__(
        self,
        template: str = 'open-devin',
        timeout: int = 120,
    ):
        self.sandbox = E2BSandbox(
            api_key=config.get('E2B_API_KEY'),
            template=template,
            # It's possible to stream stdout and stderr from sandbox and from each process
            on_stderr=lambda x: logger.info(f'E2B sandbox stderr: {x}'),
            on_stdout=lambda x: logger.info(f'E2B sandbox stdout: {x}'),
            cwd='/home/user',  # Default workdir inside sandbox
        )
        self.timeout = timeout
        logger.info(f'Started E2B sandbox with ID "{self.sandbox.id}"')

    @property
    def filesystem(self):
        return self.sandbox.filesystem

    # TODO: This won't work if we didn't wait for the background process to finish
    def read_logs(self, process_id: int) -> str:
        proc = self.background_commands.get(process_id)
        if proc is None:
            raise ValueError(f'Process {process_id} not found')
        assert isinstance(proc, E2BProcess)
        return '\n'.join([m.line for m in proc.output_messages])

    def execute(self, cmd: str) -> Tuple[int, str]:
        process = self.sandbox.process.start(cmd)
        try:
            process_output = process.wait(timeout=self.timeout)
        except TimeoutException:
            logger.info('Command timed out, killing process...')
            process.kill()
            return -1, f'Command: "{cmd}" timed out'

        logs = [m.line for m in process_output.messages]
        logs_str = '\n'.join(logs)
        if process.exit_code is None:
            return -1, logs_str

        assert process_output.exit_code is not None
        return process_output.exit_code, logs_str

    def copy_to(self, host_src: str, sandbox_dest: str, recursive: bool = False):
        # FIXME
        raise NotImplementedError('Copying files to E2B sandbox is not implemented yet')

    def execute_in_background(self, cmd: str) -> Process:
        process = self.sandbox.process.start(cmd)
        e2b_process = E2BProcess(process, cmd)
        self.cur_background_id += 1
        self.background_commands[self.cur_background_id] = e2b_process
        return e2b_process

    def kill_background(self, process_id: int):
        process = self.background_commands.get(process_id)
        if process is None:
            raise ValueError(f'Process {process_id} not found')
        assert isinstance(process, E2BProcess)
        process.kill()
        return process

    def close(self):
        self.sandbox.close()
