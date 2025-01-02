import os

import frontmatter
import pydantic


class MicroAgentMetadata(pydantic.BaseModel):
    name: str = 'default'
    agent: str = ''
    triggers: list[str] = []


class MicroAgent:
    def __init__(self, path: str | None = None, content: str | None = None):
        if path and not content:
            self.path = path
            if not os.path.exists(path):
                raise FileNotFoundError(f'Micro agent file {path} is not found')
            with open(path, 'r') as file:
                loaded = frontmatter.load(file)
                self._content = loaded.content
                self._metadata = MicroAgentMetadata(**loaded.metadata)
        elif content and not path:
            metadata, self._content = frontmatter.parse(content)
            self._metadata = MicroAgentMetadata(**metadata)
        else:
            raise Exception('You must pass either path or file content, but not both.')

    def get_trigger(self, message: str) -> str | None:
        message = message.lower()
        for trigger in self.triggers:
            if trigger.lower() in message:
                return trigger
        return None

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
