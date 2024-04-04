import concurrent.futures
from typing import Dict
from e2b import Sandbox
from e2b import Process
from e2b.sandbox.exception import (
    TimeoutException,
)

from opendevin import config


class E2BSandbox:
    closed = False
    background_commands: Dict[int, Process] = {}

    def __init__(
        self,
        template: str = "base",
        timeout: int = 120,
    ):
        self.sandbox = Sandbox(
            api_key=config.get("E2B_API_KEY"),
            template=template,
        )
        self.timeout = timeout

    def execute2(self, cmd: str):
        print("Executing command in E2B sandbox:", cmd)

        process = self.sandbox.process.start(cmd)
        try:
            process_output = process.wait(timeout=self.timeout)
        except TimeoutException:
            print("Command timed out, killing process...")
            process.kill()
            return -1, f'Command: "{cmd}" timed out'

        logs = [m.line for m in process_output.messages]
        logs_str = "\n".join(logs)
        return process_output.exit_code, logs_str

    def execute(self, cmd: str):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            print("Executing command in E2B sandbox:", cmd)
            process = self.sandbox.process.start(cmd)
            future = executor.submit(process.wait)
            try:
                process_output = future.result(timeout=self.timeout)
            except concurrent.futures.TimeoutError:
                print("Command timed out, killing process...")
                process.kill()
                return -1, f'Command: "{cmd}" timed out'

        logs = [m.line for m in process_output.messages]
        logs_str = "\n".join(logs)
        return process_output.exit_code, logs_str

    def close(self):
        self.sandbox.close()
