from abc import abstractmethod
from typing import List

from opendevin.core import config
from opendevin.core.schema import ConfigType
from opendevin.events.action import (
    ACTION_TYPE_TO_CLASS,
    Action,
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
    NullObservation,
    Observation,
)
from opendevin.runtime import (
    DockerExecBox,
    DockerSSHBox,
    E2BBox,
    LocalBox,
    Sandbox,
)
from opendevin.runtime.browser.browser_env import BrowserEnv
from opendevin.runtime.plugins import PluginRequirement


def get_sandbox(sid: str = 'default', sandbox_type: str = 'exec') -> Sandbox:
    timeout = config.get(ConfigType.SANDBOX_TIMEOUT)
    if sandbox_type == 'exec':
        return DockerExecBox(sid=sid, timeout=timeout)
    elif sandbox_type == 'local':
        return LocalBox(timeout=timeout)
    elif sandbox_type == 'ssh':
        return DockerSSHBox(sid=sid, timeout=timeout)
    elif sandbox_type == 'e2b':
        return E2BBox(timeout=timeout)
    else:
        raise ValueError(f'Invalid sandbox type: {sandbox_type}')


class Runtime:
    sid: str
    sandbox: Sandbox

    def __init__(
        self,
        sid: str = 'default',
    ):
        self.sid = sid
        sandbox_type = config.get(ConfigType.SANDBOX_TYPE)
        self.sandbox = get_sandbox(sid, sandbox_type)
        self.browser = BrowserEnv()

    def init_sandbox_plugins(self, plugins: List[PluginRequirement]):
        self.sandbox.init_plugins(plugins)

    async def run_action(self, action: Action) -> Observation:
        print('run action!', action.runnable)
        if not action.runnable:
            return NullObservation('')
        action_id = action.action  # type: ignore[attr-defined]
        if action_id not in ACTION_TYPE_TO_CLASS:
            return ErrorObservation(f'Action {action_id} does not exist.')
        if not hasattr(self, action_id):
            return ErrorObservation(
                f'Action {action_id} is not supported in the current runtime.'
            )
        print('actually running')
        observation = await getattr(self, action_id)(action)
        return observation

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

    @abstractmethod
    async def run(self, action: CmdRunAction) -> Observation:
        pass

    @abstractmethod
    async def kill(self, action: CmdKillAction) -> Observation:
        pass

    @abstractmethod
    async def run_ipython(self, action: IPythonRunCellAction) -> Observation:
        pass

    @abstractmethod
    async def read(self, action: FileReadAction) -> Observation:
        pass

    @abstractmethod
    async def write(self, action: FileWriteAction) -> Observation:
        pass

    @abstractmethod
    async def browse(self, action: BrowseURLAction) -> Observation:
        pass

    @abstractmethod
    async def recall(self, action: AgentRecallAction) -> Observation:
        pass
