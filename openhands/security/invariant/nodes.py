from typing import Any, Iterable

from pydantic import BaseModel, Field
from pydantic.dataclasses import dataclass


@dataclass
class LLM:
    vendor: str
    model: str


class Event(BaseModel):
    metadata: dict[str, Any] | None = Field(
        default_factory=lambda: dict(), description='Metadata associated with the event'
    )


class Function(BaseModel):
    name: str
    arguments: dict[str, Any]


class ToolCall(Event):
    id: str
    type: str
    function: Function


class Message(Event):
    role: str
    content: str | None
    tool_calls: list[ToolCall] | None = None

    def __rich_repr__(
        self,
    ) -> Iterable[Any | tuple[Any] | tuple[str, Any] | tuple[str, Any, Any]]:
        # Print on separate line
        yield 'role', self.role
        yield 'content', self.content
        yield 'tool_calls', self.tool_calls


class ToolOutput(Event):
    role: str
    content: str
    tool_call_id: str | None = None

    _tool_call: ToolCall | None = None
