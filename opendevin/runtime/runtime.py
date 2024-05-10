from abc import abstractmethod

from opendevin.core.config import config
from opendevin.events.action import (
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
from opendevin.events.serialization.action import ACTION_TYPE_TO_CLASS
from opendevin.runtime import (
    DockerExecBox,
    DockerSSHBox,
    E2BBox,
    LocalBox,
    Sandbox,
)
from opendevin.runtime.browser.browser_env import BrowserEnv
from opendevin.runtime.plugins import PluginRequirement


def create_sandbox(sid: str = 'default', sandbox_type: str = 'exec') -> Sandbox:
    if sandbox_type == 'exec':
        return DockerExecBox(sid=sid, timeout=config.sandbox_timeout)
    elif sandbox_type == 'local':
        return LocalBox(timeout=config.sandbox_timeout)
    elif sandbox_type == 'ssh':
        return DockerSSHBox(sid=sid, timeout=config.sandbox_timeout)
    elif sandbox_type == 'e2b':
        return E2BBox(timeout=config.sandbox_timeout)
    else:
        raise ValueError(f'Invalid sandbox type: {sandbox_type}')


class Runtime:
    """
    The runtime is how the agent interacts with the external environment.
    This includes a bash sandbox, a browser, and filesystem interactions.

    sid is the session id, which is used to identify the current user session.
    """

    sid: str
    sandbox: Sandbox

    def __init__(
        self,
        sid: str = 'default',
    ):
        self.sid = sid
        self.sandbox = create_sandbox(sid, config.sandbox_type)
        self.browser = BrowserEnv()

    def init_sandbox_plugins(self, plugins: list[PluginRequirement]) -> None:
        self.sandbox.init_plugins(plugins)

    async def run_action(self, action: Action) -> Observation:
        """
        Run an action and return the resulting observation.
        If the action is not runnable in any runtime, a NullObservation is returned.
        If the action is not supported by the current runtime, an ErrorObservation is returned.
        """
        if not action.runnable:
            return NullObservation('')
        action_id = action.action  # type: ignore[attr-defined]
        if action_id not in ACTION_TYPE_TO_CLASS:
            return ErrorObservation(f'Action {action_id} does not exist.')
        if not hasattr(self, action_id):
            return ErrorObservation(
                f'Action {action_id} is not supported in the current runtime.'
            )
        observation = await getattr(self, action_id)(action)
        return observation

    def get_background_obs(self) -> list[CmdOutputObservation]:
        """
        Returns all observations that have accumulated in the runtime's background.
        Right now, this is just background commands, but could include e.g. asyncronous
        events happening in the browser.
        """
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
