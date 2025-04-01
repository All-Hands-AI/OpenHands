from litellm import ChatCompletionToolParam, ChatCompletionToolParamFunctionChunk

_MCP_CALL_DESCRIPTION = """Custom tool to call other tools exposed by MCP (Model Context Protocol) servers.

For example, if you see a tool in the format: \
"Tool(name='tool_name', description='Tool description', inputSchema={'type': 'object', 'properties':
{'param1': {'type': 'string'}}})"

You can call it by setting `tool_name` to `tool_name` and `kwargs` to \
`{'param1': 'value'}`. \
"""

MCPCallTool = ChatCompletionToolParam(
    type='function',
    function=ChatCompletionToolParamFunctionChunk(
        name='mcp_call_tool',
        description=_MCP_CALL_DESCRIPTION,
        parameters={
            'type': 'object',
            'properties': {
                'tool_name': {
                    'type': 'string',
                    'description': 'The name of the tool to call.',
                },
                'kwargs': {
                    'type': 'object',
                    'description': 'The optional arguments dict to pass to the tool call.',
                },
            },
            'required': ['tool_name'],
        },
    ),
)
