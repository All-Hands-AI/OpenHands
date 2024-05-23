from typing import Optional

from agenthub.codeact_agent.codeact_agent import CodeActAgent
from opendevin.controller import AgentController
from opendevin.controller.agent import Agent
from opendevin.controller.state.state import State
from opendevin.core.config import config
from opendevin.core.logger import opendevin_logger as logger
from opendevin.core.schema import ConfigType
from opendevin.events.stream import EventStream
from opendevin.llm.llm import LLM
from opendevin.runtime import DockerSSHBox
from opendevin.runtime.e2b.runtime import E2BRuntime
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

    async def start(self, start_event: dict):
        """Starts the agent session.

        Args:
            start_event: The start event data (optional).
        """
        if self.controller or self.runtime:
            raise Exception(
                'Session already started. You need to close this session and start a new one.'
            )
        await self._create_runtime()
        await self._create_controller(start_event)

    async def close(self):
        if self._closed:
            return
        if self.controller is not None:
            end_state = self.controller.get_state()
            end_state.save_to_session(self.sid)
            await self.controller.close()
        if self.runtime is not None:
            self.runtime.close()
        self._closed = True

    async def _create_runtime(self):
        if self.runtime is not None:
            raise Exception('Runtime already created')
        if config.runtime == 'server':
            logger.info('Using server runtime')
            self.runtime = ServerRuntime(self.event_stream, self.sid)
        elif config.runtime == 'e2b':
            logger.info('Using E2B runtime')
            self.runtime = E2BRuntime(self.event_stream, self.sid)
        else:
            raise Exception(
                f'Runtime not defined in config, or is invalid: {config.runtime}'
            )

    async def _create_controller(self, start_event: dict):
        """Creates an AgentController instance.

        Args:
            start_event: The start event data (optional).
        """
        if self.controller is not None:
            raise Exception('Controller already created')
        if self.runtime is None:
            raise Exception('Runtime must be initialized before the agent controller')
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
        self.runtime.init_sandbox_plugins(agent.sandbox_plugins)

        self.controller = AgentController(
            sid=self.sid,
            event_stream=self.event_stream,
            agent=agent,
            max_iterations=int(max_iterations),
            max_chars=int(max_chars),
        )
        try:
            agent_state = State.restore_from_session(self.sid)
            self.controller.set_state(agent_state)
        except Exception as e:
            print('Error restoring state', e)
