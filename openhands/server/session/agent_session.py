import asyncio
from typing import Callable, Optional

from openhands.controller import AgentController
from openhands.controller.agent import Agent
from openhands.controller.state.state import State
from openhands.core.config import AgentConfig, AppConfig, LLMConfig
from openhands.core.exceptions import AgentRuntimeUnavailableError
from openhands.core.logger import openhands_logger as logger
from openhands.core.schema.agent import AgentState
from openhands.events.action import ChangeAgentStateAction
from openhands.events.event import EventSource
from openhands.events.stream import EventStream
from openhands.microagent import BaseMicroAgent
from openhands.runtime import get_runtime_cls
from openhands.runtime.base import Runtime
from openhands.security import SecurityAnalyzer, options
from openhands.storage.files import FileStore
from openhands.utils.async_utils import call_async_from_sync, call_sync_from_async
from openhands.utils.shutdown_listener import should_continue

WAIT_TIME_BEFORE_CLOSE = 300
WAIT_TIME_BEFORE_CLOSE_INTERVAL = 5


class AgentSession:
    """Represents a session with an Agent

    Attributes:
        controller: The AgentController instance for controlling the agent.
    """

    sid: str
    event_stream: EventStream
    file_store: FileStore
    controller: AgentController | None = None
    runtime: Runtime | None = None
    security_analyzer: SecurityAnalyzer | None = None
    _initializing: bool = False
    _closed: bool = False
    loop: asyncio.AbstractEventLoop | None = None

    def __init__(
        self,
        sid: str,
        file_store: FileStore,
        status_callback: Optional[Callable] = None,
    ):
        """Initializes a new instance of the Session class

        Parameters:
        - sid: The session ID
        - file_store: Instance of the FileStore
        """

        self.sid = sid
        self.event_stream = EventStream(sid, file_store)
        self.file_store = file_store
        self._status_callback = status_callback

    async def start(
        self,
        runtime_name: str,
        config: AppConfig,
        agent: Agent,
        max_iterations: int,
        max_budget_per_task: float | None = None,
        agent_to_llm_config: dict[str, LLMConfig] | None = None,
        agent_configs: dict[str, AgentConfig] | None = None,
        github_token: str | None = None,
        selected_repository: str | None = None,
    ):
        """Starts the Agent session
        Parameters:
        - runtime_name: The name of the runtime associated with the session
        - config:
        - agent:
        - max_iterations:
        - max_budget_per_task:
        - agent_to_llm_config:
        - agent_configs:
        """
        if self.controller or self.runtime:
            raise RuntimeError(
                'Session already started. You need to close this session and start a new one.'
            )

        if self._closed:
            logger.warning('Session closed before starting')
            return
        self._initializing = True
        self._create_security_analyzer(config.security.security_analyzer)
        await self._create_runtime(
            runtime_name=runtime_name,
            config=config,
            agent=agent,
            github_token=github_token,
            selected_repository=selected_repository,
        )

        self.controller = self._create_controller(
            agent,
            config.security.confirmation_mode,
            max_iterations,
            max_budget_per_task=max_budget_per_task,
            agent_to_llm_config=agent_to_llm_config,
            agent_configs=agent_configs,
        )
        self.event_stream.add_event(
            ChangeAgentStateAction(AgentState.INIT), EventSource.ENVIRONMENT
        )
        self._initializing = False

    def close(self):
        """Closes the Agent session"""
        if self._closed:
            return
        self._closed = True
        call_async_from_sync(self._close)

    async def _close(self):
        seconds_waited = 0
        while self._initializing and should_continue():
            logger.debug(
                f'Waiting for initialization to finish before closing session {self.sid}'
            )
            await asyncio.sleep(WAIT_TIME_BEFORE_CLOSE_INTERVAL)
            seconds_waited += WAIT_TIME_BEFORE_CLOSE_INTERVAL
            if seconds_waited > WAIT_TIME_BEFORE_CLOSE:
                logger.error(
                    f'Waited too long for initialization to finish before closing session {self.sid}'
                )
                break
        if self.event_stream is not None:
            self.event_stream.close()
        if self.controller is not None:
            end_state = self.controller.get_state()
            end_state.save_to_session(self.sid, self.file_store)
            await self.controller.close()
        if self.runtime is not None:
            self.runtime.close()
        if self.security_analyzer is not None:
            await self.security_analyzer.close()

    async def stop_agent_loop_for_error(self):
        if self.controller is not None:
            await self.controller.set_agent_state_to(AgentState.ERROR)

    def _create_security_analyzer(self, security_analyzer: str | None):
        """Creates a SecurityAnalyzer instance that will be used to analyze the agent actions

        Parameters:
        - security_analyzer: The name of the security analyzer to use
        """

        if security_analyzer:
            logger.debug(f'Using security analyzer: {security_analyzer}')
            self.security_analyzer = options.SecurityAnalyzers.get(
                security_analyzer, SecurityAnalyzer
            )(self.event_stream)

    async def _create_runtime(
        self,
        runtime_name: str,
        config: AppConfig,
        agent: Agent,
        github_token: str | None = None,
        selected_repository: str | None = None,
    ):
        """Creates a runtime instance

        Parameters:
        - runtime_name: The name of the runtime associated with the session
        - config:
        - agent:
        """

        if self.runtime is not None:
            raise RuntimeError('Runtime already created')

        logger.debug(f'Initializing runtime `{runtime_name}` now...')
        runtime_cls = get_runtime_cls(runtime_name)
        env_vars = (
            {
                'GITHUB_TOKEN': github_token,
            }
            if github_token
            else None
        )
        self.runtime = runtime_cls(
            config=config,
            event_stream=self.event_stream,
            sid=self.sid,
            plugins=agent.sandbox_plugins,
            status_callback=self._status_callback,
            headless_mode=False,
            env_vars=env_vars,
        )

        # FIXME: this sleep is a terrible hack.
        # This is to give the websocket a second to connect, so that
        # the status messages make it through to the frontend.
        # We should find a better way to plumb status messages through.
        await asyncio.sleep(1)
        try:
            await self.runtime.connect()
        except AgentRuntimeUnavailableError as e:
            logger.error(f'Runtime initialization failed: {e}', exc_info=True)
            if self._status_callback:
                self._status_callback(
                    'error', 'STATUS$ERROR_RUNTIME_DISCONNECTED', str(e)
                )
            return

        if selected_repository:
            await call_sync_from_async(
                self.runtime.clone_repo, github_token, selected_repository
            )

        if agent.prompt_manager:
            agent.prompt_manager.set_runtime_info(self.runtime)
            microagents: list[BaseMicroAgent] = await call_sync_from_async(
                self.runtime.get_microagents_from_selected_repo, selected_repository
            )
            agent.prompt_manager.load_microagents(microagents)

        logger.debug(
            f'Runtime initialized with plugins: {[plugin.name for plugin in self.runtime.plugins]}'
        )

    def _create_controller(
        self,
        agent: Agent,
        confirmation_mode: bool,
        max_iterations: int,
        max_budget_per_task: float | None = None,
        agent_to_llm_config: dict[str, LLMConfig] | None = None,
        agent_configs: dict[str, AgentConfig] | None = None,
    ) -> AgentController:
        """Creates an AgentController instance

        Parameters:
        - agent:
        - confirmation_mode: Whether to use confirmation mode
        - max_iterations:
        - max_budget_per_task:
        - agent_to_llm_config:
        - agent_configs:
        """

        if self.controller is not None:
            raise RuntimeError('Controller already created')
        if self.runtime is None:
            raise RuntimeError(
                'Runtime must be initialized before the agent controller'
            )

        msg = (
            '\n--------------------------------- OpenHands Configuration ---------------------------------\n'
            f'LLM: {agent.llm.config.model}\n'
            f'Base URL: {agent.llm.config.base_url}\n'
        )
        if agent.llm.config.draft_editor:
            msg += (
                f'Draft editor LLM (for file editing): {agent.llm.config.draft_editor.model}\n'
                f'Draft editor LLM (for file editing) Base URL: {agent.llm.config.draft_editor.base_url}\n'
            )
        msg += (
            f'Agent: {agent.name}\n'
            f'Runtime: {self.runtime.__class__.__name__}\n'
            f'Plugins: {agent.sandbox_plugins}\n'
            '-------------------------------------------------------------------------------------------'
        )
        logger.debug(msg)

        controller = AgentController(
            sid=self.sid,
            event_stream=self.event_stream,
            agent=agent,
            max_iterations=int(max_iterations),
            max_budget_per_task=max_budget_per_task,
            agent_to_llm_config=agent_to_llm_config,
            agent_configs=agent_configs,
            confirmation_mode=confirmation_mode,
            headless_mode=False,
            status_callback=self._status_callback,
            initial_state=self._maybe_restore_state(),
        )

        return controller

    def _maybe_restore_state(self) -> State | None:
        """Helper method to handle state restore logic."""
        restored_state = None

        # Attempt to restore the state from session.
        # Use a heuristic to figure out if we should have a state:
        # if we have events in the stream.
        try:
            restored_state = State.restore_from_session(self.sid, self.file_store)
            logger.debug(f'Restored state from session, sid: {self.sid}')
        except Exception as e:
            if self.event_stream.get_latest_event_id() > 0:
                # if we have events, we should have a state
                logger.warning(f'State could not be restored: {e}')
            else:
                logger.debug('No events found, no state to restore')
        return restored_state
