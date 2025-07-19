"""Finish tool for OpenHands task completion."""

from typing import Any, Dict

from litellm import ChatCompletionToolParam, ChatCompletionToolParamFunctionChunk


from openhands.llm.tool_names import FINISH_TOOL_NAME

from .base import Tool, ToolValidationError


class FinishTool(Tool):
    """Tool for finishing tasks and providing final outputs."""
    
    def __init__(self):
        super().__init__(
            name=FINISH_TOOL_NAME,
            description="Finish the current task and provide final output"
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
                        'outputs': {
                            'type': 'object',
                            'description': 'Final outputs of the task as key-value pairs',
                        },
                        'summary': {
                            'type': 'string',
                            'description': 'Summary of what was accomplished',
                        },
                    },
                    'required': [],
                },
            ),
        )
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize finish tool parameters."""
        validated = {}
        
        if 'outputs' in parameters:
            outputs = parameters['outputs']
            if not isinstance(outputs, dict):
                raise ToolValidationError("'outputs' must be a dictionary")
            validated['outputs'] = outputs
        
        if 'summary' in parameters:
            validated['summary'] = str(parameters['summary'])
        
        return validated
    

    
    def _get_description(self, use_short_description: bool) -> str:
        """Get description for the tool."""
        if use_short_description:
            return "Finish the current task and provide final outputs."
        else:
            return """Finish the current task and provide final outputs.

Use this tool when you have completed the requested task and want to provide
final results or outputs. You can include:
- outputs: A dictionary of key-value pairs representing the final results
- summary: A text summary of what was accomplished

This will signal that the task is complete and no further actions are needed."""