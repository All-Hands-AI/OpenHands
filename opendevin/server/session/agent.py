from typing import Optional

from agenthub.codeact_agent.codeact_agent import CodeActAgent
from opendevin.controller import AgentController
from opendevin.controller.agent import Agent
from opendevin.controller.state.state import State
from opendevin.core.logger import opendevin_logger as logger
from opendevin.events.stream import EventStream
from opendevin.runtime import DockerSSHBox, get_runtime_cls
from opendevin.runtime.runtime import Runtime
from opendevin.runtime.server.runtime import ServerRuntime


class AgentSession:
    """Represents a session with an agent.

    Attributes:
        controller: The AgentController instance for controlling the agent.
    """

    sid: str
    event_stream: EventStream
    controller: Optional[AgentController] = None
    runtime: Optional[Runtime] = None
    _closed: bool = False

    def __init__(self, sid):
        """Initializes a new instance of the Session class."""
        self.sid = sid
        self.event_stream = EventStream(sid)

    async def start(
        self,
        runtime_name: str,
        agent: Agent,
        confirmation_mode: bool,
        max_iterations: int,
    ):
        """Starts the agent session.

        Args:
            start_event: The start event data (optional).
        """
        if self.controller or self.runtime:
            raise Exception(
                'Session already started. You need to close this session and start a new one.'
            )
        await self._create_runtime(runtime_name)
        await self._create_controller(agent, confirmation_mode, max_iterations)

    async def close(self):
        if self._closed:
            return
        if self.controller is not None:
            end_state = self.controller.get_state()
            end_state.save_to_session(self.sid)
            await self.controller.close()
        if self.runtime is not None:
            await self.runtime.close()
        self._closed = True

    async def _create_runtime(self, runtime_name: str):
        """Creates a runtime instance."""
        if self.runtime is not None:
            raise Exception('Runtime already created')

        logger.info(f'Using runtime: {runtime_name}')
        runtime_cls = get_runtime_cls(runtime_name)
        self.runtime = runtime_cls(self.event_stream, self.sid)
        await self.runtime.ainit()

    async def _create_controller(
        self, agent: Agent, confirmation_mode: bool, max_iterations: int
    ):
        """Creates an AgentController instance."""
        if self.controller is not None:
            raise Exception('Controller already created')
        if self.runtime is None:
            raise Exception('Runtime must be initialized before the agent controller')

        logger.info(f'Creating agent {agent.name} using LLM {agent.llm.config.model}')
        if isinstance(agent, CodeActAgent):
            if not self.runtime or not (
                isinstance(self.runtime, ServerRuntime)
                and isinstance(self.runtime.sandbox, DockerSSHBox)
            ):
                logger.warning(
                    'CodeActAgent requires DockerSSHBox as sandbox! Using other sandbox that are not stateful'
                    ' LocalBox will not work properly.'
                )
        self.runtime.init_sandbox_plugins(agent.sandbox_plugins)
        self.runtime.init_runtime_tools(agent.runtime_tools)

        self.controller = AgentController(
            sid=self.sid,
            event_stream=self.event_stream,
            agent=agent,
            max_iterations=int(max_iterations),
            confirmation_mode=confirmation_mode,
        )
        try:
            agent_state = State.restore_from_session(self.sid)
            self.controller.set_initial_state(agent_state)
            logger.info(f'Restored agent state from session, sid: {self.sid}')
        except Exception as e:
            print('Error restoring state', e)
