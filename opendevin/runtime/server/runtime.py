import os
import pathlib

from opendevin.core.config import config
from opendevin.events.action import (
    AgentRecallAction,
    BrowseURLAction,
    CmdKillAction,
    CmdRunAction,
    FileReadAction,
    FileWriteAction,
    IPythonRunCellAction,
)
from opendevin.events.observation import (
    CmdOutputObservation,
    ErrorObservation,
    IPythonRunCellObservation,
    NullObservation,
    Observation,
)
from opendevin.runtime.runtime import Runtime

from .browse import browse
from .files import read_file, write_file


class ServerRuntime(Runtime):
    async def run(self, action: CmdRunAction) -> Observation:
        return self._run_command(action.command, background=action.background)

    async def kill(self, action: CmdKillAction) -> Observation:
        cmd = self.sandbox.kill_background(action.command_id)
        return CmdOutputObservation(
            content=f'Background command with id {action.command_id} has been killed.',
            command_id=action.command_id,
            command=cmd.command,
            exit_code=0,
        )

    async def run_ipython(self, action: IPythonRunCellAction) -> Observation:
        # echo "import math" | execute_cli
        # write code to a temporary file and pass it to `execute_cli` via stdin
        tmp_filepath = os.path.join(
            config.workspace_base, '.tmp', '.ipython_execution_tmp.py'
        )
        pathlib.Path(os.path.dirname(tmp_filepath)).mkdir(parents=True, exist_ok=True)
        with open(tmp_filepath, 'w') as tmp_file:
            tmp_file.write(action.code)

        tmp_filepath_inside_sandbox = os.path.join(
            config.workspace_mount_path_in_sandbox,
            '.tmp',
            '.ipython_execution_tmp.py',
        )
        obs = self._run_command(
            f'execute_cli < {tmp_filepath_inside_sandbox}', background=False
        )
        return IPythonRunCellObservation(content=obs.content, code=action.code)

    async def read(self, action: FileReadAction) -> Observation:
        working_dir = self.sandbox.get_working_directory()
        return await read_file(action.path, working_dir, action.start, action.end)

    async def write(self, action: FileWriteAction) -> Observation:
        working_dir = self.sandbox.get_working_directory()
        return await write_file(
            action.path, working_dir, action.content, action.start, action.end
        )

    async def browse(self, action: BrowseURLAction) -> Observation:
        return await browse(action, self.browser)

    async def recall(self, action: AgentRecallAction) -> Observation:
        return NullObservation('')

    def _run_command(self, command: str, background=False) -> Observation:
        if background:
            return self._run_background(command)
        else:
            return self._run_immediately(command)

    def _run_immediately(self, command: str) -> Observation:
        try:
            exit_code, output = self.sandbox.execute(command)
            return CmdOutputObservation(
                command_id=-1, content=output, command=command, exit_code=exit_code
            )
        except UnicodeDecodeError:
            return ErrorObservation('Command output could not be decoded as utf-8')

    def _run_background(self, command: str) -> Observation:
        bg_cmd = self.sandbox.execute_in_background(command)
        content = f'Background command started. To stop it, send a `kill` action with command_id {bg_cmd.pid}'
        return CmdOutputObservation(
            content=content,
            command_id=bg_cmd.pid,
            command=command,
            exit_code=0,
        )
