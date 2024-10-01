from dataclasses import dataclass
from typing import Optional
from uuid import UUID


@dataclass
class TaskFilter:
    conversation_id__eq: Optional[UUID] = None
