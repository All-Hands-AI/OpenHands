from typing import List

from opendevin import config
from opendevin.observation import CmdOutputObservation
from opendevin.sandbox import DockerExecBox, DockerSSHBox, E2Bbox, Sandbox
from opendevin.schema import ConfigType


class CommandManager:
    id: str
    directory: str
    sandbox: Sandbox

    def __init__(
            self,
            sid: str,
            directory: str,
            container_image: str | None = None,
    ):
        self.directory = directory

        sandbox_type = config.get(ConfigType.SANDBOX_TYPE).lower()
        if sandbox_type == 'ssh':
            self.sandbox = DockerSSHBox(
                sid=(sid or 'default'), workspace_dir=directory, container_image=container_image
            )
        elif sandbox_type == 'e2b':
            self.sandbox = E2Bbox()
        else:
            self.sandbox = DockerExecBox(
                sid=(sid or 'default'), workspace_dir=directory, container_image=container_image
            )

    def run_command(self, command: str, background=False) -> CmdOutputObservation:
        if background:
            return self._run_background(command)
        else:
            return self._run_immediately(command)

    def _run_immediately(self, command: str) -> CmdOutputObservation:
        exit_code, output = self.sandbox.execute(command)
        return CmdOutputObservation(
            command_id=-1, content=output, command=command, exit_code=exit_code
        )

    def _run_background(self, command: str) -> CmdOutputObservation:
        bg_cmd = self.sandbox.execute_in_background(command)
        # FIXME: autopep8 and mypy are fighting each other on this line
        # autopep8: off
        content = f'Background command started. To stop it, send a `kill` action with id {bg_cmd.pid}'
        return CmdOutputObservation(
            content=content,
            command_id=bg_cmd.pid,
            command=command,
            exit_code=0,
        )

    def kill_command(self, id: int) -> CmdOutputObservation:
        cmd = self.sandbox.kill_background(id)
        return CmdOutputObservation(
            content=f'Background command with id {id} has been killed.',
            command_id=id,
            command=cmd.command,
            exit_code=0,
        )

    def get_background_obs(self) -> List[CmdOutputObservation]:
        obs = []
        for _id, cmd in self.sandbox.background_commands.items():
            output = cmd.read_logs()
            if output is not None and output != '':
                obs.append(
                    CmdOutputObservation(
                        content=output, command_id=_id, command=cmd.command
                    )
                )
        return obs
