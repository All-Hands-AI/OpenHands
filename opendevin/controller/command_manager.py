from typing import List

from opendevin.observation import CmdOutputObservation
from opendevin.sandbox.e2b_sandbox import E2BSandbox


class CommandManager:
    def __init__(
        self,
        id: str,
        dir: str,
        container_image: str | None = None,
    ):
        self.directory = dir
        # self.shell = DockerInteractive(
        #     id=(id or "default"), workspace_dir=dir, container_image=container_image
        # )
        self.shell = E2BSandbox()

    def run_command(self, command: str, background=False) -> CmdOutputObservation:
        if background:
            return self._run_background(command)
        else:
            return self._run_immediately(command)

    def _run_immediately(self, command: str) -> CmdOutputObservation:
        exit_code, output = self.shell.execute(command)
        return CmdOutputObservation(
            command_id=-1, content=output, command=command, exit_code=exit_code
        )

    def _run_background(self, command: str) -> CmdOutputObservation:
        bg_cmd = self.shell.execute_in_background(command)
        return CmdOutputObservation(
            content=f'Background command started. To stop it, send a `kill` action with id {bg_cmd.process_id}',
            command_id=bg_cmd.process_id,
            command=command,
            exit_code=0,
        )

    def kill_command(self, id: int) -> CmdOutputObservation:
        cmd = self.shell.kill_background(str(id))
        return CmdOutputObservation(
            content=f'Background command with id {id} has been killed.',
            command_id=id,
            command=cmd.command,
            exit_code=0,
        )

    def get_background_obs(self) -> List[CmdOutputObservation]:
        obs = []
        for _id, cmd in self.shell.background_commands.items():
            output = cmd.read_logs()
            if output is not None and output != '':
                id_int = int(_id)
                obs.append(
                    CmdOutputObservation(
                        content=output, command_id=id_int, command=cmd.command
                    )
                )
        return obs
