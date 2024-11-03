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

    def __init__(self, sid: str, file_store: FileStore):
        """Initializes a new instance of the Session class

        Parameters:
        - sid: The session ID
        - file_store: Instance of the FileStore
        """

        self.sid = sid
        self.event_stream = EventStream(sid, file_store)
        self.file_store = file_store

    async def start(
        self,
        runtime_name: str,
        config: AppConfig,
        agent: Agent,
        max_iterations: int,
        max_budget_per_task: float | None = None,
        agent_to_llm_config: dict[str, LLMConfig] | None = None,
        agent_configs: dict[str, AgentConfig] | None = None,
        status_message_callback: Optional[Callable] = None,
    ):
        """Starts the Agent session with proper error handling and timeouts
        Parameters:
        - runtime_name: The name of the runtime associated with the session
        - config: Application configuration
        - agent: Agent instance to use
        - max_iterations: Maximum number of iterations
        - max_budget_per_task: Maximum budget per task
        - agent_to_llm_config: LLM configurations for different agents
        - agent_configs: Agent configurations
        - status_message_callback: Callback for status updates
        """
        if self.controller or self.runtime:
            raise RuntimeError(
                'Session already started. You need to close this session and start a new one.'
            )

        # Create a future to track the start operation
        start_future = asyncio.Future()
        
        def start_callback(future):
            try:
                exc = future.exception()
                if exc:
                    start_future.set_exception(exc)
                else:
                    start_future.set_result(None)
            except asyncio.CancelledError:
                start_future.cancel()
            except Exception as e:
                start_future.set_exception(e)

        # Start the agent in a thread pool with proper error propagation
        task = asyncio.get_event_loop().run_in_executor(
            None,
            self._start_thread,
            runtime_name,
            config,
            agent,
            max_iterations,
            max_budget_per_task,
            agent_to_llm_config,
            agent_configs,
            status_message_callback,
        )
        task.add_done_callback(start_callback)

        try:
            # Wait for start with timeout
            await asyncio.wait_for(start_future, timeout=120)
        except asyncio.TimeoutError:
            logger.error("Agent session start timed out")
            # Cleanup if start times out
            await self.close()
            raise RuntimeError("Agent session start timed out")
        except Exception as e:
            logger.exception("Error starting agent session")
            await self.close()
            raise

    def _start_thread(self, *args):
        """Start the agent in a separate thread with proper error handling"""
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Run with timeout
                loop.run_until_complete(
                    asyncio.wait_for(self._start(*args), timeout=25)
                )
            except asyncio.TimeoutError:
                logger.error("Timeout in agent start")
                raise RuntimeError("Timeout in agent start")
            except Exception as e:
                logger.exception("Error in agent start")
                raise
            finally:
                try:
                    # Clean up the loop
                    loop.run_until_complete(loop.shutdown_asyncgens())
                    loop.close()
                except Exception as e:
                    logger.error(f"Error cleaning up thread loop: {e}")
        except Exception as e:
            logger.error(f"Fatal error in start thread: {e}")
            raise

    async def _start(
        self,
        runtime_name: str,
        config: AppConfig,
        agent: Agent,
        max_iterations: int,
        max_budget_per_task: float | None = None,
        agent_to_llm_config: dict[str, LLMConfig] | None = None,
        agent_configs: dict[str, AgentConfig] | None = None,
        status_message_callback: Optional[Callable] = None,
    ):
        self._create_security_analyzer(config.security.security_analyzer)
        await self._create_runtime(
            runtime_name=runtime_name,
            config=config,
            agent=agent,
            status_message_callback=status_message_callback,
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

    async def close(self):
        """Closes the Agent session with proper cleanup and timeouts"""
        if self._closed:
            return

        try:
            # Set closed flag early to prevent multiple close attempts
            self._closed = True

            # Save state with timeout
            if self.controller is not None:
                try:
                    async with asyncio.timeout(5):
                        end_state = self.controller.get_state()
                        end_state.save_to_session(self.sid, self.file_store)
                except asyncio.TimeoutError:
                    logger.error("Timeout saving agent state")
                except Exception as e:
                    logger.error(f"Error saving agent state: {e}")

            # Close controller with timeout
            if self.controller is not None:
                try:
                    async with asyncio.timeout(5):
                        await self.controller.close()
                except asyncio.TimeoutError:
                    logger.error("Timeout closing controller")
                except Exception as e:
                    logger.error(f"Error closing controller: {e}")
                self.controller = None

            # Close runtime (this is synchronous but should be quick)
            if self.runtime is not None:
                try:
                    self.runtime.close()
                except Exception as e:
                    logger.error(f"Error closing runtime: {e}")
                self.runtime = None

            # Close security analyzer with timeout
            if self.security_analyzer is not None:
                try:
                    async with asyncio.timeout(5):
                        await self.security_analyzer.close()
                except asyncio.TimeoutError:
                    logger.error("Timeout closing security analyzer")
                except Exception as e:
                    logger.error(f"Error closing security analyzer: {e}")
                self.security_analyzer = None

        except Exception as e:
            logger.exception(f"Unexpected error during session cleanup: {e}")
        finally:
            # Ensure closed flag is set even if cleanup fails
            self._closed = True

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
        status_message_callback: Optional[Callable] = None,
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
            status_message_callback=status_message_callback,
        )

        try:
            await self.runtime.connect()
        except Exception as e:
            logger.error(f'Runtime initialization failed: {e}', exc_info=True)
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
            # AgentSession is designed to communicate with the frontend, so we don't want to
            # run the agent in headless mode.
            headless_mode=False,
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
