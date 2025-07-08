from typing import Any

from litellm.exceptions import (  # type: ignore[import-untyped]
    APIConnectionError,
    APIError,
    AuthenticationError,
    BadRequestError,
    ContentPolicyViolationError,
    ContextWindowExceededError,
    InternalServerError,
    NotFoundError,
    RateLimitError,
    ServiceUnavailableError,
    Timeout,
)

from openhands.core.exceptions import (
    AgentStuckInLoopError,
    FunctionCallNotExistsError,
    FunctionCallValidationError,
    LLMContextWindowExceedError,
    LLMMalformedActionError,
    LLMNoActionError,
    LLMResponseError,
)


def summarize_error(error: Exception | str, context: dict[str, Any] | None = None) -> str:
    """
    Generates a user-friendly summary for a given error.

    Args:
        error: The exception object or error message string.
        context: Optional dictionary providing additional context about the error.
                 E.g., {'command': 'ls -l', 'file_path': '/path/to/file'}

    Returns:
        A user-friendly error summary.
    """
    if context is None:
        context = {}

    error_type = type(error).__name__
    error_message = str(error)

    # LiteLLM Errors
    if isinstance(error, AuthenticationError):
        return "There's an issue with your LLM API key. Please check if it's correct and has enough credits."
    if isinstance(error, RateLimitError):
        return "The LLM API is rate limiting requests. Please wait a moment and try again. If the problem persists, check your API plan limits."
    if isinstance(error, ServiceUnavailableError):
        return "The LLM API service is currently unavailable. Please try again later."
    if isinstance(error, APIConnectionError):
        return "Could not connect to the LLM API. Please check your internet connection and API endpoint."
    if isinstance(error, Timeout):
        return "The request to the LLM API timed out. Please try again."
    if isinstance(error, ContextWindowExceededError) or isinstance(error, LLMContextWindowExceedError):
        return "The conversation history is too long for the LLM to process. The agent will attempt to condense the history. If this error persists, you may need to start a new task or use a model with a larger context window."
    if isinstance(error, BadRequestError):
        if "ExceededBudget" in error_message: # Specific check for LiteLLM managed budgets
            return "The LLM operation could not be completed because it would exceed the allocated budget for this task."
        if "ContentPolicyViolationError" in error_message: # some providers throw this as BadRequestError
             return "The request to the LLM was blocked due to a content policy violation. Please modify your request or task."
        return f"The LLM API received a bad request. Details: {error_message}"
    if isinstance(error, NotFoundError):
        return f"The LLM API endpoint was not found. Please check the API configuration. Details: {error_message}"
    if isinstance(error, InternalServerError):
        return f"The LLM API encountered an internal server error. Please try again later. Details: {error_message}"
    if isinstance(error, ContentPolicyViolationError):
        return "The request to the LLM was blocked due to a contentPolicyViolation. Please modify your request or task."
    if isinstance(error, APIError): # Generic LiteLLM API error
        return f"An LLM API error occurred: {error_message}"


    # OpenHands Core LLM Errors
    if isinstance(error, LLMMalformedActionError):
        return f"The LLM tried to perform an action but the format was incorrect. Details: {error_message}"
    if isinstance(error, LLMNoActionError):
        return "The LLM did not specify an action to perform. It might need more context or a clearer instruction."
    if isinstance(error, LLMResponseError):
        return f"The LLM's response was not as expected. Details: {error_message}"
    if isinstance(error, FunctionCallNotExistsError):
        return f"The LLM tried to use a tool or function that doesn't exist: {error_message}"
    if isinstance(error, FunctionCallValidationError):
        return f"The LLM tried to use a tool or function with invalid parameters: {error_message}"


    # OpenHands Agent Errors
    if isinstance(error, AgentStuckInLoopError):
        return "The agent appears to be stuck in a loop and cannot make progress. You might need to modify the task or provide more specific instructions."

    # Generic Python Errors (Examples)
    if isinstance(error, FileNotFoundError):
        file_path = context.get('file_path', error_message.split("'")[-2] if "'" in error_message else 'unknown file')
        return f"File not found: '{file_path}'. Please ensure the file exists at the correct location."
    if isinstance(error, PermissionError):
        return f"Permission denied. The agent does not have the necessary permissions to perform an operation. Details: {error_message}"
    if isinstance(error, ConnectionError):
        return f"A network connection error occurred. Please check your internet connection. Details: {error_message}"
    if isinstance(error, ValueError):
        return f"A value error occurred: {error_message}."
    if isinstance(error, TypeError):
        return f"A type error occurred: {error_message}."
    if isinstance(error, KeyError):
        key = context.get('key', error_message.split("'")[-2] if "'" in error_message else 'unknown key')
        return f"Missing key: '{key}'. A required piece of data was not found."
    if isinstance(error, AttributeError):
        return f"Attribute error: {error_message}. This might indicate an issue with the agent's internal state or code."
    if isinstance(error, NotImplementedError):
        return "This feature or action is not yet implemented."


    # Default summary if no specific handler
    return f"An unexpected error occurred: {error_type} - {error_message}. Please check the logs for more details."

# Example usage (for testing purposes)
if __name__ == '__main__':
    # LiteLLM Errors
    print(f"AuthenticationError: {summarize_error(AuthenticationError('Invalid API Key'))}")
    print(f"RateLimitError: {summarize_error(RateLimitError('Rate limit exceeded'))}")
    print(f"ServiceUnavailableError: {summarize_error(ServiceUnavailableError('Service unavailable'))}")
    print(f"APIConnectionError: {summarize_error(APIConnectionError('Could not connect'))}")
    print(f"Timeout: {summarize_error(Timeout('Request timed out'))}")
    print(f"ContextWindowExceededError: {summarize_error(ContextWindowExceededError('Context window exceeded'))}")
    print(f"LLMContextWindowExceedError: {summarize_error(LLMContextWindowExceedError('Context window exceeded via LLM'))}")
    print(f"BadRequestError (Budget): {summarize_error(BadRequestError('ExceededBudget: Your request would exceed the budget.'))}")
    print(f"BadRequestError (Content Policy): {summarize_error(BadRequestError('ContentPolicyViolationError: Harmful content detected.'))}")
    print(f"BadRequestError (Generic): {summarize_error(BadRequestError('Generic bad request'))}")
    print(f"NotFoundError: {summarize_error(NotFoundError('Endpoint not found'))}")
    print(f"InternalServerError: {summarize_error(InternalServerError('Internal server error'))}")
    print(f"ContentPolicyViolationError: {summarize_error(ContentPolicyViolationError('Violated content policy'))}")
    print(f"APIError: {summarize_error(APIError('Generic API Error'))}")

    # OpenHands Core LLM Errors
    print(f"LLMMalformedActionError: {summarize_error(LLMMalformedActionError('Malformed action'))}")
    print(f"LLMNoActionError: {summarize_error(LLMNoActionError('No action specified'))}")
    print(f"LLMResponseError: {summarize_error(LLMResponseError('Unexpected LLM response'))}")
    print(f"FunctionCallNotExistsError: {summarize_error(FunctionCallNotExistsError('Tool `do_magic` not found'))}")
    print(f"FunctionCallValidationError: {summarize_error(FunctionCallValidationError('Invalid params for `do_stuff`'))}")

    # OpenHands Agent Errors
    print(f"AgentStuckInLoopError: {summarize_error(AgentStuckInLoopError('Agent is stuck'))}")

    # Generic Python Errors
    print(f"FileNotFoundError: {summarize_error(FileNotFoundError('No such file or directory: /test.txt'))}")
    print(f"FileNotFoundError (with context): {summarize_error(FileNotFoundError('No such file or directory'), {'file_path': '/explicit/path.txt'})}")
    print(f"PermissionError: {summarize_error(PermissionError('Operation not permitted'))}")
    print(f"ConnectionError: {summarize_error(ConnectionError('Failed to establish a new connection'))}")
    print(f"ValueError: {summarize_error(ValueError('Invalid value provided'))}")
    print(f"TypeError: {summarize_error(TypeError('Incorrect type for argument'))}")
    print(f"KeyError: {summarize_error(KeyError('my_key'))}")
    print(f"KeyError (with context): {summarize_error(KeyError('random_key'), {'key': 'explicit_key'})}")
    print(f"AttributeError: {summarize_error(AttributeError('object has no attribute `foo`'))}")
    print(f"NotImplementedError: {summarize_error(NotImplementedError('This is not implemented'))}")

    # Default
    print(f"RuntimeError: {summarize_error(RuntimeError('A generic runtime error'))}")
    print(f"String error: {summarize_error('This is a string error message')}")

    # Test with context
    print(f"CmdRun failed (context): {summarize_error(RuntimeError('Command failed with exit code 1'), {'command': 'your_command --arg'})}")

    # Example of how context could be used for a command execution error (not yet implemented in handlers)
    cmd_error = RuntimeError('Command failed')
    cmd_context = {'command': 'grep "thing" file.txt', 'exit_code': 1, 'stdout': '', 'stderr': 'grep: file.txt: No such file or directory'}
    # A more specific handler could use cmd_context to produce:
    # "Command 'grep \"thing\" file.txt' failed. Error: grep: file.txt: No such file or directory"
    # Current default output:
    print(f"Command Execution Error (default): {summarize_error(cmd_error, cmd_context)}")
