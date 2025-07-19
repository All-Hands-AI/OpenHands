"""Browser tool for OpenHands web browsing capabilities."""

from typing import Any, Dict

from litellm import ChatCompletionToolParam, ChatCompletionToolParamFunctionChunk


from openhands.llm.tool_names import BROWSER_TOOL_NAME

from .base import Tool, ToolValidationError


class BrowserTool(Tool):
    """Tool for web browsing and interaction."""
    
    def __init__(self):
        super().__init__(
            name=BROWSER_TOOL_NAME,
            description="Browse the web and interact with web pages"
        )
    
    def get_schema(self, use_short_description: bool = False) -> ChatCompletionToolParam:
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
                        'action': {
                            'type': 'string',
                            'description': 'The browser action to perform',
                            'enum': ['goto', 'click', 'type', 'scroll', 'wait', 'screenshot'],
                        },
                        'url': {
                            'type': 'string',
                            'description': 'URL to navigate to (required for goto action)',
                        },
                        'coordinate': {
                            'type': 'array',
                            'items': {'type': 'number'},
                            'description': 'Coordinate [x, y] for click action',
                        },
                        'text': {
                            'type': 'string',
                            'description': 'Text to type (required for type action)',
                        },
                        'direction': {
                            'type': 'string',
                            'description': 'Scroll direction (up/down) for scroll action',
                            'enum': ['up', 'down'],
                        },
                        'amount': {
                            'type': 'number',
                            'description': 'Amount to scroll (pixels)',
                        },
                        'timeout': {
                            'type': 'number',
                            'description': 'Timeout in seconds for wait action',
                        },
                    },
                    'required': ['action'],
                },
            ),
        )
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize browser tool parameters."""
        if 'action' not in parameters:
            raise ToolValidationError("Missing required parameter 'action'")
        
        action = parameters['action']
        valid_actions = ['goto', 'click', 'type', 'scroll', 'wait', 'screenshot']
        if action not in valid_actions:
            raise ToolValidationError(f"Invalid action '{action}'. Must be one of: {valid_actions}")
        
        validated = {'action': action}
        
        # Validate action-specific parameters
        if action == 'goto':
            if 'url' not in parameters:
                raise ToolValidationError("'goto' action requires 'url' parameter")
            validated['url'] = str(parameters['url'])
        
        elif action == 'click':
            if 'coordinate' not in parameters:
                raise ToolValidationError("'click' action requires 'coordinate' parameter")
            coordinate = parameters['coordinate']
            if not isinstance(coordinate, list) or len(coordinate) != 2:
                raise ToolValidationError("'coordinate' must be a list of two numbers [x, y]")
            try:
                validated['coordinate'] = [float(coordinate[0]), float(coordinate[1])]
            except (ValueError, TypeError):
                raise ToolValidationError("'coordinate' must contain valid numbers")
        
        elif action == 'type':
            if 'text' not in parameters:
                raise ToolValidationError("'type' action requires 'text' parameter")
            validated['text'] = str(parameters['text'])
        
        elif action == 'scroll':
            if 'direction' in parameters:
                direction = parameters['direction']
                if direction not in ['up', 'down']:
                    raise ToolValidationError("'direction' must be 'up' or 'down'")
                validated['direction'] = direction
            
            if 'amount' in parameters:
                try:
                    validated['amount'] = float(parameters['amount'])
                except (ValueError, TypeError):
                    raise ToolValidationError("'amount' must be a valid number")
        
        elif action == 'wait':
            if 'timeout' in parameters:
                try:
                    timeout = float(parameters['timeout'])
                    if timeout <= 0:
                        raise ToolValidationError("'timeout' must be positive")
                    validated['timeout'] = timeout
                except (ValueError, TypeError):
                    raise ToolValidationError("'timeout' must be a valid number")
        
        return validated
    

    
    def _get_description(self, use_short_description: bool) -> str:
        """Get description for the tool."""
        if use_short_description:
            return """Browse the web and interact with web pages. Supports navigation, clicking, typing, scrolling, and taking screenshots."""
        else:
            return """Browse the web and interact with web pages.

Available actions:
- goto: Navigate to a URL
- click: Click at specific coordinates
- type: Type text into the current element
- scroll: Scroll the page up or down
- wait: Wait for a specified timeout
- screenshot: Take a screenshot of the current page

The browser maintains state between actions, allowing for complex interactions with web pages."""