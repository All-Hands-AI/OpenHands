from opendevin.storage.files import FileStore
from opendevin.runtime.utils.async_utils import async_to_sync

class E2BFileStore(FileStore):
    def __init__(self, filesystem):
        self.filesystem = filesystem

    @async_to_sync
    async def write(self, path, contents):
        # type: (str, str) -> None
        await self.filesystem.write(path, contents)

    @async_to_sync
    async def read(self, path):
        # type: (str) -> str
        return await self.filesystem.read(path)

    def list(self, path):
        # type: (str) -> list[str]
        return self.filesystem.list(path)

    @async_to_sync
    async def delete(self, path):
        # type: (str) -> None
        await self.filesystem.delete(path)
