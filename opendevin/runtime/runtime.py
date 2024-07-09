import asyncio
import atexit
from abc import abstractmethod
from typing import Any, Optional

from opendevin.core.config import config
from opendevin.core.exceptions import BrowserInitException
from opendevin.core.logger import opendevin_logger as logger
from opendevin.events import EventStream, EventStreamSubscriber
from opendevin.events.action import (
    Action,
    AgentRecallAction,
    BrowseInteractiveAction,
    BrowseURLAction,
    CmdRunAction,
    FileReadAction,
    FileWriteAction,
    IPythonRunCellAction,
)
from opendevin.events.event import Event
from opendevin.events.observation import (
    ErrorObservation,
    NullObservation,
    Observation,
)
from opendevin.events.serialization.action import ACTION_TYPE_TO_CLASS
from opendevin.runtime import (
    DockerSSHBox,
    E2BBox,
    LocalBox,
    Sandbox,
)
from opendevin.runtime.browser.browser_env import BrowserEnv
from opendevin.runtime.plugins import PluginRequirement
from opendevin.runtime.tools import RuntimeTool
from opendevin.runtime.utils.async_utils import async_to_sync
from opendevin.storage import FileStore, InMemoryFileStore


async def create_sandbox(sid: str = 'default', box_type: str = 'ssh') -> Sandbox:
    if box_type == 'local':
        sandbox = LocalBox()  # type: ignore
    elif box_type == 'ssh':
        sandbox = DockerSSHBox(sid=sid)  # type: ignore
    elif box_type == 'e2b':
        sandbox = E2BBox()  # type: ignore
    else:
        raise ValueError(f'Invalid sandbox type: {box_type}')

    await sandbox.initialize()
    return sandbox


class Runtime:
    """
    The runtime is how the agent interacts with the external environment.
    This includes a bash sandbox, a browser, and filesystem interactions.

    sid is the session id, which is used to identify the current user session.
    """

    _instance = None
    _initialization_lock = asyncio.Lock()
    _initialized = False

    sid: str
    file_store: FileStore

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        event_stream: EventStream,
        sid: str = 'default',
        sandbox: Optional[Sandbox] = None,
    ):
        if not hasattr(self, 'initialized'):
            self.sid = sid
            self.sandbox = sandbox
            self._is_external_sandbox = sandbox is not None
            self.browser: Optional[BrowserEnv] = None
            self.file_store = InMemoryFileStore()
            self.event_stream = event_stream
            self.initialized = False

    async def initialize(self):
        if self._initialized is False:
            logger.info('Runtime initialize...')
            async with self._initialization_lock:
                if self._initialized is False:
                    logger.info('Runtime class initialization')
                    if self.sandbox is None:
                        logger.info('Creating sandbox.')
                        self.sandbox = await create_sandbox(
                            self.sid, config.sandbox.box_type
                        )
                        logger.info('Sandbox created.')

                    await self._setup_sandbox()
                    self.event_stream.subscribe(
                        EventStreamSubscriber.RUNTIME, self.on_event
                    )
                    logger.info('Runtime class initialization complete.')
                    self._initialized = True

    async def _setup_sandbox(self):
        if self.sandbox is None:
            raise RuntimeError('Sandbox is not initialized')
        logger.info('Setting up sandbox')
        await self.sandbox.execute('mkdir -p /tmp')
        await self.sandbox.execute('git config --global user.name "OpenDevin"')
        await self.sandbox.execute(
            'git config --global user.email "opendevin@all-hands.dev"'
        )
        atexit.register(self.close)
        logger.info('Sandbox setup complete.')

    async def aclose(self):
        if not self._is_external_sandbox and self.sandbox is not None:
            await self.sandbox.close()
        if self.browser is not None:
            self.browser.close()

    @async_to_sync
    def close(self):
        return self.aclose()

    async def init_sandbox_plugins(self, plugins: list[PluginRequirement]) -> None:
        if self.sandbox is not None:
            await self.sandbox.init_plugins(plugins)

    def init_runtime_tools(
        self,
        runtime_tools: list[RuntimeTool],
        runtime_tools_config: Optional[dict[RuntimeTool, Any]] = None,
        is_async: bool = True,
    ) -> None:
        # if browser in runtime_tools, init it
        if RuntimeTool.BROWSER in runtime_tools:
            if runtime_tools_config is None:
                runtime_tools_config = {}
            browser_env_config = runtime_tools_config.get(RuntimeTool.BROWSER, {})
            try:
                self.browser = BrowserEnv(is_async=is_async, **browser_env_config)
            except BrowserInitException:
                logger.warn(
                    'Failed to start browser environment, web browsing functionality will not work'
                )

    async def on_event(self, event: Event) -> None:
        if isinstance(event, Action):
            observation = await self.run_action(event)
            observation._cause = event.id  # type: ignore[attr-defined]
            await self.event_stream.add_event(observation, event.source)  # type: ignore[arg-type]

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

    @abstractmethod
    async def run(self, action: CmdRunAction) -> Observation:
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
