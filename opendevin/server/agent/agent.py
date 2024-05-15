from typing import Optional

from agenthub.codeact_agent.codeact_agent import CodeActAgent
from opendevin.const.guide_url import TROUBLESHOOTING_URL
from opendevin.controller import AgentController
from opendevin.controller.agent import Agent
from opendevin.core.config import config
from opendevin.core.logger import opendevin_logger as logger
from opendevin.core.schema import ActionType, AgentState, ConfigType
from opendevin.events.action import (
    ChangeAgentStateAction,
    NullAction,
)
from opendevin.events.event import Event
from opendevin.events.observation import (
    NullObservation,
)
from opendevin.events.serialization.action import action_from_dict
from opendevin.events.serialization.event import event_to_dict
from opendevin.events.stream import EventSource, EventStream, EventStreamSubscriber
from opendevin.llm.llm import LLM
from opendevin.runtime import DockerSSHBox
from opendevin.runtime.e2b.runtime import E2BRuntime
from opendevin.runtime.runtime import Runtime
from opendevin.runtime.server.runtime import ServerRuntime
from opendevin.server.session import session_manager


class AgentUnit:
    """Represents a session with an agent.

    Attributes:
        controller: The AgentController instance for controlling the agent.
    """

    sid: str
    event_stream: EventStream
    controller: Optional[AgentController] = None
    runtime: Optional[Runtime] = None

    def __init__(self, sid):
        """Initializes a new instance of the Session class."""
        self.sid = sid
        self.event_stream = EventStream(sid)
        self.event_stream.subscribe(EventStreamSubscriber.SERVER, self.on_event)
        if config.runtime == 'server':
            logger.info('Using server runtime')
            self.runtime = ServerRuntime(self.event_stream, sid)
        elif config.runtime == 'e2b':
            logger.info('Using E2B runtime')
            self.runtime = E2BRuntime(self.event_stream, sid)

    async def send_error(self, message):
        """Sends an error message to the client.

        Args:
            message: The error message to send.
        """
        await session_manager.send_error(self.sid, message)

    async def send_message(self, message):
        """Sends a message to the client.

        Args:
            message: The message to send.
        """
        await session_manager.send_message(self.sid, message)

    async def send(self, data):
        """Sends data to the client.

        Args:
            data: The data to send.
        """
        await session_manager.send(self.sid, data)

    async def dispatch(self, action: str | None, data: dict):
        """Dispatches actions to the agent from the client."""
        if action is None:
            await self.send_error('Invalid action')
            return

        if action == ActionType.INIT:
            await self.create_controller(data)
            await self.event_stream.add_event(
                ChangeAgentStateAction(AgentState.INIT), EventSource.USER
            )
            return

        action_dict = data.copy()
        action_dict['action'] = action
        action_obj = action_from_dict(action_dict)
        await self.event_stream.add_event(action_obj, EventSource.USER)

    async def create_controller(self, start_event: dict):
        """Creates an AgentController instance.

        Args:
            start_event: The start event data (optional).
        """
        args = {
            key: value
            for key, value in start_event.get('args', {}).items()
            if value != ''
        }  # remove empty values, prevent FE from sending empty strings
        agent_cls = args.get(ConfigType.AGENT, config.agent.name)
        model = args.get(ConfigType.LLM_MODEL, config.llm.model)
        api_key = args.get(ConfigType.LLM_API_KEY, config.llm.api_key)
        api_base = config.llm.base_url
        max_iterations = args.get(ConfigType.MAX_ITERATIONS, config.max_iterations)
        max_chars = args.get(ConfigType.MAX_CHARS, config.llm.max_chars)

        logger.info(f'Creating agent {agent_cls} using LLM {model}')
        llm = LLM(model=model, api_key=api_key, base_url=api_base)
        agent = Agent.get_cls(agent_cls)(llm)
        if isinstance(agent, CodeActAgent):
            if not self.runtime or not isinstance(self.runtime.sandbox, DockerSSHBox):
                logger.warning(
                    'CodeActAgent requires DockerSSHBox as sandbox! Using other sandbox that are not stateful (LocalBox, DockerExecBox) will not work properly.'
                )
        # Initializing plugins into the runtime
        assert self.runtime is not None, 'Runtime is not initialized'
        self.runtime.init_sandbox_plugins(agent.sandbox_plugins)

        if self.controller is not None:
            await self.controller.close()
        try:
            self.controller = AgentController(
                sid=self.sid,
                event_stream=self.event_stream,
                agent=agent,
                max_iterations=int(max_iterations),
                max_chars=int(max_chars),
            )
        except Exception as e:
            logger.exception(f'Error creating controller: {e}')
            await self.send_error(
                f'Error creating controller. Please check Docker is running and visit `{TROUBLESHOOTING_URL}` for more debugging information..'
            )
            return

    async def on_event(self, event: Event):
        """Callback function for agent events.

        Args:
            event: The agent event (Observation or Action).
        """
        if isinstance(event, NullAction):
            return
        if isinstance(event, NullObservation):
            return
        if event.source == 'agent' and not isinstance(
            event, (NullAction, NullObservation)
        ):
            await self.send(event_to_dict(event))

    async def close(self):
        if self.controller is not None:
            await self.controller.close()
        if self.runtime is not None:
            self.runtime.close()
