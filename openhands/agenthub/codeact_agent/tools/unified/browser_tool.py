"""Browser tool for OpenHands web browsing capabilities."""

from typing import Any

from litellm import ChatCompletionToolParam, ChatCompletionToolParamFunctionChunk

from openhands.llm.tool_names import BROWSER_TOOL_NAME

from .base import Tool, ToolValidationError


class BrowserTool(Tool):
    """Tool for web browsing and interaction."""

    def __init__(self):
        super().__init__(
            name=BROWSER_TOOL_NAME,
            description='Interact with the browser using Python code. Use it ONLY when you need to interact with a webpage.',
        )

    def get_schema(
        self, use_short_description: bool = False
    ) -> ChatCompletionToolParam:
        """Get the tool schema for function calling."""
        description = self._get_description(use_short_description)

        return ChatCompletionToolParam(
            type='function',
            function=ChatCompletionToolParamFunctionChunk(
                name=self.name,
                description=description,
                parameters={
                    'type': 'object',
                    'properties': {
                        'code': {
                            'type': 'string',
                            'description': 'The Python code that interacts with the browser.',
                        },
                    },
                    'required': ['code'],
                },
            ),
        )

    def validate_parameters(self, parameters: dict[str, Any]) -> dict[str, Any]:
        """Validate and normalize browser tool parameters."""
        if 'code' not in parameters:
            raise ToolValidationError("Missing required parameter 'code'")

        code = parameters['code']
        if not isinstance(code, str):
            raise ToolValidationError("Parameter 'code' must be a string")

        if not code.strip():
            raise ToolValidationError("Parameter 'code' cannot be empty")

        return {'code': code}

    def _get_description(self, use_short_description: bool) -> str:
        """Get description for the tool."""
        if use_short_description:
            return 'Interact with the browser using Python code. Use it ONLY when you need to interact with a webpage.'
        else:
            return """Interact with the browser using Python code. Use it ONLY when you need to interact with a webpage.

See the description of "code" parameter for more details.

Multiple actions can be provided at once, but will be executed sequentially without any feedback from the page.
More than 2-3 actions usually leads to failure or unexpected behavior. Example:
fill('a12', 'example with "quotes"')
click('a51')
click('48', button='middle', modifiers=['Shift'])

You can also use the browser to view pdf, png, jpg files.
You should first check the content of /tmp/oh-server-url to get the server url, and then use it to view the file by `goto("{server_url}/view?path={absolute_file_path}")`.
For example: `goto("http://localhost:8000/view?path=/workspace/test_document.pdf")`
Note: The file should be downloaded to the local machine first before using the browser to view it."""
