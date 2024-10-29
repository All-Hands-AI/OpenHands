import os

import frontmatter
import pydantic

from openhands.controller.agent import Agent
from openhands.core.exceptions import MicroAgentValidationError
from openhands.core.logger import openhands_logger as logger


class MicroAgentMetadata(pydantic.BaseModel):
    name: str
    agent: str
    require_env_var: dict[str, str]


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

    @property
    def content(self) -> str:
        return self._content

    def _validate_micro_agent(self):
        logger.debug(
            f'Loading and validating micro agent [{self._metadata.name}] based on [{self._metadata.agent}]'
        )
        # Make sure the agent is registered
        agent_cls = Agent.get_cls(self._metadata.agent)
        assert agent_cls is not None
        # Make sure the environment variables are set
        for env_var, instruction in self._metadata.require_env_var.items():
            if env_var not in os.environ:
                raise MicroAgentValidationError(
                    f'Environment variable [{env_var}] is required by micro agent [{self._metadata.name}] but not set. {instruction}'
                )
