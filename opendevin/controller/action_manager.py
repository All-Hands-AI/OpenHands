from typing import List
import traceback

from opendevin import config
from opendevin.observation import CmdOutputObservation
from opendevin.sandbox import DockerExecBox, DockerSSHBox, Sandbox, LocalBox
from opendevin.schema import ConfigType
from opendevin.logger import opendevin_logger as logger
from opendevin.action import (
    Action,
)
from opendevin.observation import (
    Observation,
    AgentErrorObservation,
    NullObservation,
)


class ActionManager:
    id: str
    shell: Sandbox

    def __init__(
            self,
            sid: str,
            container_image: str | None = None,
    ):
        sandbox_type = config.get(ConfigType.SANDBOX_TYPE).lower()
        if sandbox_type == 'exec':
            self.shell = DockerExecBox(
                sid=(sid or 'default'), container_image=container_image
            )
        elif sandbox_type == 'local':
            self.shell = LocalBox()
        elif sandbox_type == 'ssh':
            self.shell = DockerSSHBox(
                sid=(sid or 'default'), container_image=container_image
            )
        else:
            raise ValueError(f'Invalid sandbox type: {sandbox_type}')

    async def run_action(self, action: Action, agent_controller) -> Observation:
        observation: Observation = NullObservation('')
        if not action.executable:
            return observation
        try:
            observation = await action.run(agent_controller)
        except Exception as e:
            observation = AgentErrorObservation(str(e))
            logger.error(e)
            logger.debug(traceback.format_exc())
        return observation

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
        content = f'Background command started. To stop it, send a `kill` action with id {bg_cmd.id}'
        return CmdOutputObservation(
            content=content,
            command_id=bg_cmd.id,
            command=command,
            exit_code=0,
        )

    def kill_command(self, id: int) -> CmdOutputObservation:
        cmd = self.shell.kill_background(id)
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
                obs.append(
                    CmdOutputObservation(
                        content=output, command_id=_id, command=cmd.command
                    )
                )
        return obs
