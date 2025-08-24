from __future__ import annotations

from typing import Callable

from pydantic import BaseModel

from .types import ToolResult


class Tool(BaseModel):
    name: str
    description: str | None = None
    # MCP-aligned camelCase field names
    inputSchema: dict
    outputSchema: dict | None = None
    # Optional local handler hook (not used in minimal SDK flow)
    handler: Callable[[dict], ToolResult] | None = None

    def to_param(self) -> dict:
        # MCP-compatible tool param for litellm/OpenAI function calling
        return {
            'type': 'function',
            'function': {
                'name': self.name,
                'description': self.description or '',
                'parameters': self.inputSchema,
            },
        }
