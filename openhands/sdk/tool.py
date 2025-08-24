from __future__ import annotations

from typing import Callable

from pydantic import BaseModel

from .types import ToolResult


class Tool(BaseModel):
    name: str
    description: str | None = None
    input_schema: dict
    output_schema: dict | None = None
    handler: Callable[[dict], ToolResult] | None = None

    def to_param(self) -> dict:
        # MCP-compatible tool param for litellm
        return {
            'type': 'function',
            'function': {
                'name': self.name,
                'description': self.description or '',
                'parameters': self.input_schema,
            },
        }


# Runtime-backed tools in MCP shape; handlers to be set by Conversation wiring
runtime_execute_bash_tool = Tool(
    name='execute_bash',
    description='Run a shell command inside the runtime',
    input_schema={
        'type': 'object',
        'properties': {
            'command': {'type': 'string'},
            'timeout': {'type': 'number', 'description': 'Seconds'},
        },
        'required': ['command'],
        'additionalProperties': False,
    },
)

runtime_file_read_tool = Tool(
    name='file_read',
    description='Read a text file from the runtime workspace',
    input_schema={
        'type': 'object',
        'properties': {
            'path': {'type': 'string'},
            'view_range': {
                'type': 'array',
                'items': {'type': 'integer'},
                'minItems': 2,
                'maxItems': 2,
            },
        },
        'required': ['path'],
        'additionalProperties': False,
    },
)

runtime_file_write_tool = Tool(
    name='file_write',
    description='Write text to a file in the runtime workspace (overwrites)',
    input_schema={
        'type': 'object',
        'properties': {
            'path': {'type': 'string'},
            'content': {'type': 'string'},
        },
        'required': ['path', 'content'],
        'additionalProperties': False,
    },
)
