import os

import frontmatter
import pydantic

from openhands.controller.agent import Agent
from openhands.core.logger import openhands_logger as logger


class MicroAgentMetadata(pydantic.BaseModel):
    name: str
    agent: str
    triggers: list[str] = []


class MicroAgent:
    def __init__(self, path: str):
        self.path = path
        if not os.path.exists(path):
            raise FileNotFoundError(f'Micro agent file {path} is not found')
        with open(path, 'r') as file:
            self._loaded = frontmatter.load(file)
            self._content = self._loaded.content
            self._metadata = MicroAgentMetadata(**self._loaded.metadata)
        self._validate_micro_agent()

    def should_trigger(self, message: str) -> bool:
        for trigger in self.triggers:
            if trigger in message:
                return True
        return False

    @property
    def content(self) -> str:
        return self._content

    @property
    def metadata(self) -> MicroAgentMetadata:
        return self._metadata

    @property
    def name(self) -> str:
        return self._metadata.name

    @property
    def triggers(self) -> list[str]:
        return self._metadata.triggers

    @property
    def agent(self) -> str:
        return self._metadata.agent

    def _validate_micro_agent(self):
        logger.info(
            f'Loading and validating micro agent [{self._metadata.name}] based on [{self._metadata.agent}]'
        )
        # Make sure the agent is registered
        agent_cls = Agent.get_cls(self._metadata.agent)
        assert agent_cls is not None
