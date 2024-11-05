import asyncio
from typing import Callable, Optional

from openhands.controller import AgentController
from openhands.controller.agent import Agent
from openhands.controller.state.state import State
from openhands.core.config import AgentConfig, AppConfig, LLMConfig
from openhands.core.logger import openhands_logger as logger
from openhands.core.schema.agent import AgentState
from openhands.events.action.agent import ChangeAgentStateAction
from openhands.events.event import EventSource
from openhands.events.stream import EventStream
from openhands.runtime import get_runtime_cls
from openhands.runtime.base import Runtime
from openhands.security import SecurityAnalyzer, options
from openhands.storage.files import FileStore


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

        asyncio.get_event_loop().run_in_executor(
            None,
            self._start_thread,
            runtime_name,
            config,
            agent,
            max_iterations,
            max_budget_per_task,
            agent_to_llm_config,
            agent_configs,
        )

    def _start_thread(self, *args):
        try:
            asyncio.run(self._start(*args), debug=True)
        except RuntimeError:
            logger.error(f'Error starting session: {RuntimeError}', exc_info=True)
            logger.debug('Session Finished')

    async def _start(
        self,
        runtime_name: str,
        config: AppConfig,
        agent: Agent,
        max_iterations: int,
        max_budget_per_task: float | None = None,
        agent_to_llm_config: dict[str, LLMConfig] | None = None,
        agent_configs: dict[str, AgentConfig] | None = None,
    ):
        self._create_security_analyzer(config.security.security_analyzer)
        await self._create_runtime(
            runtime_name=runtime_name,
            config=config,
            agent=agent,
        )
        self._create_controller(
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
        if self.controller:
            self.controller.agent_task = self.controller.start_step_loop()
            await self.controller.agent_task  # type: ignore

    def close(self):
        """Closes the Agent session"""
        if self._closed:
            return

        self._closed = True

        def inner_close():
            asyncio.run(self._close())

        asyncio.get_event_loop().run_in_executor(None, inner_close)

    async def _close(self):
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
        self.runtime = runtime_cls(
            config=config,
            event_stream=self.event_stream,
            sid=self.sid,
            plugins=agent.sandbox_plugins,
            status_callback=self._status_callback,
        )

        try:
            await self.runtime.connect()
        except Exception as e:
            logger.error(f'Runtime initialization failed: {e}', exc_info=True)
            if self._status_callback:
                self._status_callback(
                    'error', 'STATUS$ERROR_RUNTIME_DISCONNECTED', str(e)
                )
            raise

        if self.runtime is not None:
            logger.debug(
                f'Runtime initialized with plugins: {[plugin.name for plugin in self.runtime.plugins]}'
            )
        else:
            logger.warning('Runtime initialization failed')

    def _create_controller(
        self,
        agent: Agent,
        confirmation_mode: bool,
        max_iterations: int,
        max_budget_per_task: float | None = None,
        agent_to_llm_config: dict[str, LLMConfig] | None = None,
        agent_configs: dict[str, AgentConfig] | None = None,
    ):
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

        self.controller = AgentController(
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
        )
        try:
            agent_state = State.restore_from_session(self.sid, self.file_store)
            self.controller.set_initial_state(
                agent_state, max_iterations, confirmation_mode
            )
            logger.debug(f'Restored agent state from session, sid: {self.sid}')
        except Exception as e:
            logger.debug(f'State could not be restored: {e}')
        logger.debug('Agent controller initialized.')
