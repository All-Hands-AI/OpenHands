import asyncio
import atexit
import copy
import json
import os
from abc import abstractmethod
from typing import Any, Optional

from opendevin.core.config import AppConfig, SandboxConfig
from opendevin.core.logger import opendevin_logger as logger
from opendevin.events import EventStream, EventStreamSubscriber
from opendevin.events.action import (
    Action,
    ActionConfirmationStatus,
    BrowseInteractiveAction,
    BrowseURLAction,
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
    RejectObservation,
)
from opendevin.events.serialization.action import ACTION_TYPE_TO_CLASS
from opendevin.runtime.plugins import PluginRequirement
from opendevin.runtime.tools import RuntimeTool
from opendevin.storage import FileStore


def _default_env_vars(sandbox_config: SandboxConfig) -> dict[str, str]:
    ret = {}
    for key in os.environ:
        if key.startswith('SANDBOX_ENV_'):
            sandbox_key = key.removeprefix('SANDBOX_ENV_')
            ret[sandbox_key] = os.environ[key]
    if sandbox_config.enable_auto_lint:
        ret['ENABLE_AUTO_LINT'] = 'true'
    return ret


class Runtime:
    """The runtime is how the agent interacts with the external environment.
    This includes a bash sandbox, a browser, and filesystem interactions.

    sid is the session id, which is used to identify the current user session.
    """

    sid: str
    file_store: FileStore
    DEFAULT_ENV_VARS: dict[str, str]

    def __init__(
        self,
        config: AppConfig,
        event_stream: EventStream,
        sid: str = 'default',
    ):
        self.sid = sid
        self.event_stream = event_stream
        self.event_stream.subscribe(EventStreamSubscriber.RUNTIME, self.on_event)
        self.config = copy.deepcopy(config)
        self.DEFAULT_ENV_VARS = _default_env_vars(config.sandbox)
        atexit.register(self.close_sync)

    async def ainit(self, env_vars: dict[str, str] | None = None) -> None:
        """
        Initialize the runtime (asynchronously).

        This method should be called after the runtime's constructor.
        """
        if self.DEFAULT_ENV_VARS:
            logger.debug(f'Adding default env vars: {self.DEFAULT_ENV_VARS}')
            await self.add_env_vars(self.DEFAULT_ENV_VARS)
        if env_vars is not None:
            logger.debug(f'Adding provided env vars: {env_vars}')
            await self.add_env_vars(env_vars)

    async def close(self) -> None:
        pass

    def close_sync(self) -> None:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # No running event loop, use asyncio.run()
            asyncio.run(self.close())
        else:
            # There is a running event loop, create a task
            if loop.is_running():
                loop.create_task(self.close())
            else:
                loop.run_until_complete(self.close())

    # ====================================================================
    # Methods we plan to deprecate when we move to new EventStreamRuntime
    # ====================================================================

    def init_sandbox_plugins(self, plugins: list[PluginRequirement]) -> None:
        # TODO: deprecate this method when we move to the new EventStreamRuntime
        raise NotImplementedError('This method is not implemented in the base class.')

    def init_runtime_tools(
        self,
        runtime_tools: list[RuntimeTool],
        runtime_tools_config: Optional[dict[RuntimeTool, Any]] = None,
        is_async: bool = True,
    ) -> None:
        # TODO: deprecate this method when we move to the new EventStreamRuntime
        raise NotImplementedError('This method is not implemented in the base class.')

    # ====================================================================

    async def add_env_vars(self, env_vars: dict[str, str]) -> None:
        cmd = ''
        for key, value in env_vars.items():
            # Note: json.dumps gives us nice escaping for free
            cmd += f'export {key}={json.dumps(value)}; '
        if not cmd:
            return
        cmd = cmd.strip()
        logger.debug(f'Adding env var: {cmd}')
        obs: Observation = await self.run(CmdRunAction(cmd))
        if not isinstance(obs, CmdOutputObservation) or obs.exit_code != 0:
            raise RuntimeError(
                f'Failed to add env vars [{env_vars}] to environment: {obs.content}'
            )

    async def on_event(self, event: Event) -> None:
        if isinstance(event, Action):
            observation = await self.run_action(event)
            observation._cause = event.id  # type: ignore[attr-defined]
            self.event_stream.add_event(observation, event.source)  # type: ignore[arg-type]

    async def run_action(self, action: Action) -> Observation:
        """Run an action and return the resulting observation.
        If the action is not runnable in any runtime, a NullObservation is returned.
        If the action is not supported by the current runtime, an ErrorObservation is returned.
        """
        if not action.runnable:
            return NullObservation('')
        if (
            hasattr(action, 'is_confirmed')
            and action.is_confirmed == ActionConfirmationStatus.AWAITING_CONFIRMATION
        ):
            return NullObservation('')
        action_type = action.action  # type: ignore[attr-defined]
        if action_type not in ACTION_TYPE_TO_CLASS:
            return ErrorObservation(f'Action {action_type} does not exist.')
        if not hasattr(self, action_type):
            return ErrorObservation(
                f'Action {action_type} is not supported in the current runtime.'
            )
        if (
            hasattr(action, 'is_confirmed')
            and action.is_confirmed == ActionConfirmationStatus.REJECTED
        ):
            return RejectObservation(
                'Action has been rejected by the user! Waiting for further user input.'
            )
        observation = await getattr(self, action_type)(action)
        observation._parent = action.id  # type: ignore[attr-defined]
        return observation

    # ====================================================================
    # Implement these methods in the subclass
    # ====================================================================

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
