from opendevin.events.action import (
    FileReadAction,
    FileWriteAction,
)
from opendevin.events.observation import (
    AgentErrorObservation,
    FileReadObservation,
    FileWriteObservation,
    Observation,
)
from opendevin.runtime.server.files import insert_lines, read_lines
from opendevin.runtime.server.runtime import ServerRuntime

from .sandbox import E2BSandbox


class E2BRuntime(ServerRuntime):
    def __init__(
        self,
        sid: str = 'default',
    ):
        super().__init__()
        if not isinstance(self.sandbox, E2BSandbox):
            raise ValueError('E2BRuntime requires an E2BSandbox')
        self.filesystem = self.sandbox.filesystem

    async def read(self, action: FileReadAction) -> Observation:
        content = self.filesystem.read(action.path)
        lines = read_lines(action, content.split('\n'))
        code_view = ''.join(lines)
        return FileReadObservation(code_view, path=action.path)

    async def write(self, action: FileWriteAction) -> Observation:
        files = self.filesystem.list(action.path)
        if action.path in files:
            all_lines = self.filesystem.read(action.path)
            new_file = insert_lines(action, action.content.split('\n'), all_lines)
            self.filesystem.write(action.path, ''.join(new_file))
            return FileWriteObservation('', path=action.path)
        else:
            # FIXME: we should create a new file here
            return AgentErrorObservation(f'File not found: {action.path}')
