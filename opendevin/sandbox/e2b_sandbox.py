from typing import Dict, Tuple
from e2b import Sandbox, Process
from e2b.sandbox.exception import (
    TimeoutException,
)

from opendevin import config


# TODO: Fix types
class BackgroundCommand:
    def __init__(self, process: Process, cmd: str):
        self._process = process
        self._cmd_str = cmd

    def kill(self):
        self._process.kill()

    def read_logs(self):
        return '\n'.join([m.line for m in self._process.output_messages])

    # TODO: OpenDevin expects this to be a int.
    @property
    def process_id(self) -> int:
        return int(self._process.process_id)

    @property
    def command(self) -> str:
        return self._cmd_str

    @property
    def output_messages(self):
        return self._process.output_messages


class E2BSandbox:
    closed = False
    background_commands: Dict[str, BackgroundCommand] = {}

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

    def read_logs(self, process_id: str) -> str:
        proc = self.background_commands.get(process_id)
        if proc is None:
            raise ValueError(f'Process {process_id} not found')
        return '\n'.join([m.line for m in proc.output_messages])

    # TODO: This is synchronous, so there's no reason for it to return None.
    def execute(self, cmd: str) -> Tuple[int, str]:
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
        return process_output.exit_code, logs_str

    def execute_in_background(self, cmd: str):
        process = self.sandbox.process.start(cmd)
        self.background_commands[process.process_id] = BackgroundCommand(
            process, cmd)
        return process

    def kill_background(self, process_id: str):
        process = self.background_commands.get(process_id)
        if process is None:
            raise ValueError(f'Process {process_id} not found')
        process.kill()
        return process

    def close(self):
        self.sandbox.close()
