import os

import frontmatter
import pydantic


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

    def should_trigger(self, message: str) -> bool:
        message = message.lower()
        for trigger in self.triggers:
            if trigger.lower() in message:
                print(f'Triggered {self.name} with {trigger}')
                print(f'Message: {message}')
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
