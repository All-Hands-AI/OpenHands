import json
from dataclasses import dataclass, field
from typing import Type

from openhands.server.session.session_init_data import SessionInitData
from openhands.storage.files import FileStore
from openhands.storage.item_store import ItemStore, T
from openhands.storage.local import LocalFileStore


@dataclass
class FileItemStore(ItemStore[T]):
    type: Type = SessionInitData
    files: FileStore = field(
        default_factory=lambda: LocalFileStore('~/.openhands/session_init_data/')
    )
    pattern: str = '{id}.json'

    def load(self, id: str) -> T | None:
        file_name = self.pattern.format(id=id)
        try:
            json_str = self.files.read(file_name)
            kwargs = json.loads(json_str)
            item = self.type(**kwargs)
            return item
        except FileNotFoundError:
            return None

    def store(self, id: str, item: T):
        json_str = json.dumps(item.__dict__)
        file_name = self.pattern.format(id=id)
        self.files.write(file_name, json_str)
