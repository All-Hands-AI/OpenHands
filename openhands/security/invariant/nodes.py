from typing import Any, Dict, Iterable, List, Optional, Tuple, Union

from pydantic import BaseModel, Field
from pydantic.dataclasses import dataclass


@dataclass
class LLM:
    vendor: str
    model: str


class Event(BaseModel):
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=lambda: dict(), description='Metadata associated with the event'
    )


class Function(BaseModel):
    name: str
    arguments: Dict[str, Any]


class ToolCall(Event):
    id: str
    type: str
    function: Function


class Message(Event):
    role: str
    content: Optional[str]
    tool_calls: Optional[List[ToolCall]] = None

    def __rich_repr__(
        self,
    ) -> Iterable[Union[Any, Tuple[Any], Tuple[str, Any], Tuple[str, Any, Any]]]:
        # Print on separate line
        yield 'role', self.role
        yield 'content', self.content
        yield 'tool_calls', self.tool_calls


class ToolOutput(Event):
    role: str
    content: str
    tool_call_id: Optional[str] = None

    _tool_call: Optional[ToolCall] = None
