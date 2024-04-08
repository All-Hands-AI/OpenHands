from typing import Dict, Tuple
from e2b import Sandbox
from e2b.sandbox.exception import (
    TimeoutException,
)

from opendevin import config
from opendevin.sandbox.e2b.process import E2BProcess


class E2BSandbox:
    closed = False
    cur_background_id = 0
    background_commands: Dict[int, E2BProcess] = {}

    def __init__(
        self,
        template: str = 'base',
        timeout: int = 120,
    ):
        self.sandbox = Sandbox(
            api_key=config.get('E2B_API_KEY'),
            template=template,
            on_stderr=lambda x: print(f'E2B SANDBOX STDERR: {x}'),
            on_stdout=lambda x: print(f'E2B SANDBOX STDOUT: {x}'),
        )
        self.timeout = timeout
        print('Started E2B sandbox')

    def read_logs(self, process_id: int) -> str:
        proc = self.background_commands.get(process_id)
        if proc is None:
            raise ValueError(f'Process {process_id} not found')
        return '\n'.join([m.line for m in proc.output_messages])

    def execute(self, cmd: str) -> Tuple[int, str]:
        print('Running command in e2b sandbox:', cmd)
        process = self.sandbox.process.start(cmd)
        try:
            process_output = process.wait(timeout=self.timeout)
        except TimeoutException:
            print('Command timed out, killing process...')
            process.kill()
            return -1, f'Command: "{cmd}" timed out'

        logs = [m.line for m in process_output.messages]
        logs_str = '\n'.join(logs)
        if process.exit_code is None:
            return -1, logs_str

        assert process_output.exit_code is not None
        return process_output.exit_code, logs_str

    def execute_in_background(self, cmd: str) -> E2BProcess:
        print('Running background command in e2b sandbox:', cmd)
        process = self.sandbox.process.start(cmd)
        e2b_process = E2BProcess(process, cmd)
        self.cur_background_id += 1
        self.background_commands[self.cur_background_id] = e2b_process
        return e2b_process

    def kill_background(self, process_id: int):
        process = self.background_commands.get(process_id)
        if process is None:
            raise ValueError(f'Process {process_id} not found')
        process.kill()
        return process

    def close(self):
        self.sandbox.close()
