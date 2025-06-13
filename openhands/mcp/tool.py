from abc import ABC, abstractmethod
from typing import Optional

from mcp import ClientSession
from mcp.types import CallToolResult, TextContent, Tool


class BaseTool(ABC, Tool):
    @classmethod
    def postfix(cls) -> str:
        return '_mcp_tool_call'

    class Config:
        arbitrary_types_allowed = True

    @abstractmethod
    async def execute(self, **kwargs) -> CallToolResult:
        """Execute the tool with given parameters."""

    # def to_param(self) -> Dict:
    #     """Convert tool to function call format."""

    #     return {
    #         'type': 'function',
    #         'function': {
    #             'name': self.name + self.postfix(),
    #             'description': self.description,
    #             'parameters': self.inputSchema,
    #             "required": self.input_schema.get("required", [])
    #         },
    #     }
    def to_param(self) -> dict:
        """
        Converts a function description from the input format to OpenAI's function calling format.
        """
        name = self.name + self.postfix()
        description = self.description

        if not description:
            description = f'Gets information for the {name} function'

        input_schema = self.inputSchema
        openai_parameters = {
            'type': 'object',
            'properties': {},
            'required': input_schema.get('required', []),
        }

        properties = input_schema.get('properties', {})
        defs = input_schema.get('$defs', {})

        for prop_name, prop_details in properties.items():
            if '$ref' in prop_details:
                ref_path = prop_details['$ref']
                type_name = ref_path.split('/')[-1]
                if type_name in defs:
                    type_def = defs[type_name]
                    openai_parameters['properties'][prop_name] = {
                        'type': type_def.get('type', 'object'),
                        'properties': {},
                        'required': [],
                    }
                    if 'enum' in type_def:
                        openai_parameters['properties'][prop_name]['enum'] = type_def[
                            'enum'
                        ]
                    if 'default' in type_def:
                        openai_parameters['properties'][prop_name]['default'] = (
                            type_def['default']
                        )
                    if 'description' in type_def:
                        openai_parameters['properties'][prop_name]['description'] = (
                            type_def['description']
                        )
                    if 'title' in type_def:
                        openai_parameters['properties'][prop_name]['title'] = type_def[
                            'title'
                        ]
                    if 'minimum' in type_def:
                        openai_parameters['properties'][prop_name]['minimum'] = (
                            type_def['minimum']
                        )
                    if 'maximum' in type_def:
                        openai_parameters['properties'][prop_name]['maximum'] = (
                            type_def['maximum']
                        )
                    for nested_prop, nested_details in type_def.get(
                        'properties', {}
                    ).items():
                        prop_type = nested_details.get('type')
                        prop_desc = nested_details.get('description', '')
                        openai_parameters['properties'][prop_name]['properties'][
                            nested_prop
                        ] = {'type': prop_type, 'description': prop_desc}
            else:
                # Handle direct properties, including arrays
                prop_type = prop_details.get('type', 'string')
                openai_parameters['properties'][prop_name] = {
                    'type': prop_type,
                    'description': prop_details.get('description', ''),
                }
                # Handle array types
                if prop_type == 'array' and 'items' in prop_details:
                    openai_parameters['properties'][prop_name]['items'] = {
                        'type': prop_details['items'].get('type', 'string'),
                        'description': prop_details['items'].get('description', ''),
                    }

        openai_format = {
            'type': 'function',
            'function': {
                'name': name,
                'description': description,
                'parameters': openai_parameters,
            },
        }

        return openai_format


class MCPClientTool(BaseTool):
    """Represents a tool proxy that can be called on the MCP server from the client side."""

    session: Optional[ClientSession] = None

    async def execute(self, **kwargs) -> CallToolResult:
        """Execute the tool by making a remote call to the MCP server."""
        if not self.session:
            return CallToolResult(
                content=[TextContent(text='Not connected to MCP server', type='text')],
                isError=True,
            )
        try:
            result = await self.session.call_tool(self.name, kwargs)
            return result
        except Exception as e:
            return CallToolResult(
                content=[
                    TextContent(text=f'Error executing tool: {str(e)}', type='text')
                ],
                isError=True,
            )
