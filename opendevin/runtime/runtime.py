import asyncio
from abc import abstractmethod

from opendevin.core.config import config
from opendevin.core.exceptions import BrowserInitException
from opendevin.core.logger import opendevin_logger as logger
from opendevin.events import EventSource, EventStream, EventStreamSubscriber
from opendevin.events.action import (
    Action,
    AgentRecallAction,
    BrowseInteractiveAction,
    BrowseURLAction,
    CmdKillAction,
    CmdRunAction,
    FileReadAction,
    FileWriteAction,
    IPythonRunCellAction,
)
from opendevin.events.event import Event
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
from opendevin.storage import FileStore, InMemoryFileStore


def create_sandbox(sid: str = 'default', sandbox_type: str = 'exec') -> Sandbox:
    if sandbox_type == 'exec':
        return DockerExecBox(sid=sid)
    elif sandbox_type == 'local':
        return LocalBox()
    elif sandbox_type == 'ssh':
        return DockerSSHBox(sid=sid)
    elif sandbox_type == 'e2b':
        return E2BBox()
    else:
        raise ValueError(f'Invalid sandbox type: {sandbox_type}')


class Runtime:
    """
    The runtime is how the agent interacts with the external environment.
    This includes a bash sandbox, a browser, and filesystem interactions.

    sid is the session id, which is used to identify the current user session.
    """

    sid: str
    file_store: FileStore

    def __init__(
        self,
        event_stream: EventStream,
        sid: str = 'default',
        sandbox: Sandbox | None = None,
    ):
        self.sid = sid
        if sandbox is None:
            self.sandbox = create_sandbox(sid, config.sandbox_type)
            self._is_external_sandbox = False
        else:
            self.sandbox = sandbox
            self._is_external_sandbox = True
        self.browser: BrowserEnv | None = None
        try:
            self.browser = BrowserEnv()
        except BrowserInitException:
            logger.warn(
                'Failed to start browser environment, web browsing functionality will not work'
            )
        self.file_store = InMemoryFileStore()
        self.event_stream = event_stream
        self.event_stream.subscribe(EventStreamSubscriber.RUNTIME, self.on_event)
        self._bg_task = asyncio.create_task(self._start_background_observation_loop())

    def close(self):
        if not self._is_external_sandbox:
            self.sandbox.close()
        if self.browser is not None:
            self.browser.close()
        self._bg_task.cancel()

    def init_sandbox_plugins(self, plugins: list[PluginRequirement]) -> None:
        self.sandbox.init_plugins(plugins)

    async def on_event(self, event: Event) -> None:
        if isinstance(event, Action):
            observation = await self.run_action(event)
            observation._cause = event.id  # type: ignore[attr-defined]
            source = event.source if event.source else EventSource.AGENT
            await self.event_stream.add_event(observation, source)

    async def run_action(self, action: Action) -> Observation:
        """
        Run an action and return the resulting observation.
        If the action is not runnable in any runtime, a NullObservation is returned.
        If the action is not supported by the current runtime, an ErrorObservation is returned.
        """
        if not action.runnable:
            return NullObservation('')
        action_type = action.action  # type: ignore[attr-defined]
        if action_type not in ACTION_TYPE_TO_CLASS:
            return ErrorObservation(f'Action {action_type} does not exist.')
        if not hasattr(self, action_type):
            return ErrorObservation(
                f'Action {action_type} is not supported in the current runtime.'
            )
        observation = await getattr(self, action_type)(action)
        observation._parent = action.id  # type: ignore[attr-defined]
        return observation

    async def _start_background_observation_loop(self):
        while True:
            await self.submit_background_obs()
            await asyncio.sleep(1)

    async def submit_background_obs(self):
        """
        Returns all observations that have accumulated in the runtime's background.
        Right now, this is just background commands, but could include e.g. asynchronous
        events happening in the browser.
        """
        for _id, cmd in self.sandbox.background_commands.items():
            output = cmd.read_logs()
            if output:
                await self.event_stream.add_event(
                    CmdOutputObservation(
                        content=output, command_id=_id, command=cmd.command
                    ),
                    EventSource.AGENT,  # FIXME: use the original action's source
                )
        await asyncio.sleep(1)

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
    async def browse_interactive(self, action: BrowseInteractiveAction) -> Observation:
        pass

    @abstractmethod
    async def recall(self, action: AgentRecallAction) -> Observation:
        pass
