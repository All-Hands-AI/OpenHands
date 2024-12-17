from dataclasses import dataclass
from typing import Type, TypeVar

from openhands.server.session.session_init_data import SessionInitData
from openhands.server.shared import file_store
from openhands.storage.files import FileStore
from openhands.storage.item_store import ItemStore

T = TypeVar('T')


@dataclass
class SessionInitStore(ItemStore[SessionInitData]):
    type: Type = SessionInitData
    files: FileStore = file_store
    pattern: str = 'config.json'
