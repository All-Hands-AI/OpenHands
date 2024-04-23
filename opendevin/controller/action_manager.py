from typing import List
import traceback

from opendevin import config
from opendevin.observation import CmdOutputObservation
from opendevin.sandbox import DockerExecBox, DockerSSHBox, Sandbox, LocalBox, E2BBox
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
from opendevin.sandbox.plugins import PluginRequirement


class ActionManager:
    id: str
    sandbox: Sandbox

    def __init__(
            self,
            sid: str,
            container_image: str | None = None,
    ):
        sandbox_type = config.get(ConfigType.SANDBOX_TYPE).lower()
        if sandbox_type == 'exec':
            self.sandbox = DockerExecBox(
                sid=(sid or 'default'), container_image=container_image
            )
        elif sandbox_type == 'local':
            self.sandbox = LocalBox()
        elif sandbox_type == 'ssh':
            self.sandbox = DockerSSHBox(
                sid=(sid or 'default'), container_image=container_image
            )
        elif sandbox_type == 'e2b':
            self.sandbox = E2BBox()
        else:
            raise ValueError(f'Invalid sandbox type: {sandbox_type}')

    def init_sandbox_plugins(self, plugins: List[PluginRequirement]):
        self.sandbox.init_plugins(plugins)

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
        exit_code, output = self.sandbox.execute(command)
        return CmdOutputObservation(
            command_id=-1, content=output, command=command, exit_code=exit_code
        )

    def _run_background(self, command: str) -> CmdOutputObservation:
        bg_cmd = self.sandbox.execute_in_background(command)
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
