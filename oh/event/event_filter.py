from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from oh.event.oh_event import OhEvent
from oh.storage.item_filter_abc import ItemFilterABC


@dataclass
class EventFilter(ItemFilterABC[OhEvent]):
    conversation_id__eq: Optional[UUID] = None

    def filter(self, item: OhEvent) -> bool:
        if (
            self.conversation_id__eq
            and item.conversation_id != self.conversation_id__eq
        ):
            return False
        return True
