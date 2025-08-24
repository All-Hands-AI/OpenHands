from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel


class ConversationStatus(str, Enum):
    RUNNING = 'RUNNING'
    IDLE = 'IDLE'
    FINISHED = 'FINISHED'
    ERROR = 'ERROR'
    CANCELED = 'CANCELED'


class ToolResult(BaseModel):
    status: Literal['ok', 'error']
    output: Any | None = None
    error: str | None = None


class SDKEvent(BaseModel):
    type: Literal[
        'system_message',
        'user_message',
        'assistant_message',
        'tool_call',
        'tool_result',
        'status_update',
        'error',
    ]
    ts: datetime
    conversation_id: str
    data: dict
