from opendevin.events.action import (
    FileReadAction,
    FileWriteAction,
)
from opendevin.events.observation import (
    ErrorObservation,
    FileReadObservation,
    FileWriteObservation,
    Observation,
)
from opendevin.events.stream import EventStream
from opendevin.runtime import Sandbox
from opendevin.runtime.server.files import insert_lines, read_lines
from opendevin.runtime.server.runtime import ServerRuntime

from .filestore import E2BFileStore
from .sandbox import E2BSandbox


class E2BRuntime(ServerRuntime):
    def __init__(
        self,
        event_stream: EventStream,
        sid: str = 'default',
        sandbox: Sandbox | None = None,
    ):
        super().__init__(event_stream, sid, sandbox)
        if not isinstance(self.sandbox, E2BSandbox):
            raise ValueError('E2BRuntime requires an E2BSandbox')
        self.file_store = E2BFileStore(self.sandbox.filesystem)

    async def read(self, action: FileReadAction) -> Observation:
        content = self.file_store.read(action.path)
        lines = read_lines(content.split('\n'), action.start, action.end)
        code_view = ''.join(lines)
        return FileReadObservation(code_view, path=action.path)

    async def write(self, action: FileWriteAction) -> Observation:
        if action.start == 0 and action.end == -1:
            self.file_store.write(action.path, action.content)
            return FileWriteObservation(content='', path=action.path)
        files = self.file_store.list(action.path)
        if action.path in files:
            all_lines = self.file_store.read(action.path).split('\n')
            new_file = insert_lines(
                action.content.split('\n'), all_lines, action.start, action.end
            )
            self.file_store.write(action.path, ''.join(new_file))
            return FileWriteObservation('', path=action.path)
        else:
            # FIXME: we should create a new file here
            return ErrorObservation(f'File not found: {action.path}')
