from typing import Optional

from agenthub.codeact_agent.codeact_agent import CodeActAgent
from opendevin.controller import AgentController
from opendevin.controller.agent import Agent
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

    def __init__(self, sid):
        """Initializes a new instance of the Session class."""
        self.sid = sid
        self.event_stream = EventStream(sid)
        if config.runtime == 'server':
            logger.info('Using server runtime')
            self.runtime = ServerRuntime(self.event_stream, sid)
        elif config.runtime == 'e2b':
            logger.info('Using E2B runtime')
            self.runtime = E2BRuntime(self.event_stream, sid)

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
        self.controller = AgentController(
            sid=self.sid,
            event_stream=self.event_stream,
            agent=agent,
            max_iterations=int(max_iterations),
            max_chars=int(max_chars),
        )

    async def close(self):
        if self.controller is not None:
            await self.controller.close()
        if self.runtime is not None:
            self.runtime.close()
