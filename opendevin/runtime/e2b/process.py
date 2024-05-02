from e2b import Process as E2BSandboxProcess

from opendevin.runtime.docker.process import Process


class E2BProcess(Process):
    def __init__(self, process: E2BSandboxProcess, cmd: str):
        self._process = process
        self._command = cmd

    def kill(self):
        self._process.kill()

    def read_logs(self):
        return '\n'.join([m.line for m in self._process.output_messages])

    @property
    def pid(self) -> int:
        return int(self._process.process_id)

    @property
    def command(self) -> str:
        return self._command

    @property
    def output_messages(self):
        return self._process.output_messages
