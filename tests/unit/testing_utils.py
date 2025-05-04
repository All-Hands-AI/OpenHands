"""Utility functions for tests."""

from openhands.events.tool import ToolCallMetadata


def create_tool_call_metadata(
    tool_call_id: str = 'tool_call_0',
    function_name: str = 'str_replace_editor',
    model_response_id: str = 'model_response_0',
    total_calls_in_response: int = 1,
) -> ToolCallMetadata:
    """
    Create a properly structured ToolCallMetadata object for testing.

    This function creates a ToolCallMetadata object with a properly structured
    model_response dictionary that includes the necessary nested objects.

    Args:
        tool_call_id: The ID of the tool call
        function_name: The name of the function being called
        model_response_id: The ID of the model response
        total_calls_in_response: The total number of calls in the response

    Returns:
        A properly structured ToolCallMetadata object
    """
    # Create a dictionary representation of the model response
    model_response = {
        'id': model_response_id,
        'choices': [
            {
                'message': {
                    'role': 'assistant',
                    'content': '',
                    'tool_calls': [
                        {
                            'id': tool_call_id,
                            'type': 'function',
                            'function': {
                                'name': function_name,
                                'arguments': '{}',  # Empty JSON object as string
                            },
                        }
                    ],
                }
            }
        ],
    }

    return ToolCallMetadata(
        tool_call_id=tool_call_id,
        function_name=function_name,
        model_response=model_response,
        total_calls_in_response=total_calls_in_response,
    )
