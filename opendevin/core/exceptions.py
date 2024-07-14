class AgentNoInstructionError(Exception):
    def __init__(self, message='Instruction must be provided'):
        super().__init__(message)


class AgentEventTypeError(Exception):
    def __init__(self, message='Event must be a dictionary'):
        super().__init__(message)


class AgentAlreadyRegisteredError(Exception):
    def __init__(self, name=None):
        if name is not None:
            message = f"Agent class already registered under '{name}'"
        else:
            message = 'Agent class already registered'
        super().__init__(message)


class AgentNotRegisteredError(Exception):
    def __init__(self, name=None):
        if name is not None:
            message = f"No agent class registered under '{name}'"
        else:
            message = 'No agent class registered'
        super().__init__(message)


class TaskInvalidStateError(Exception):
    def __init__(self, state=None):
        if state is not None:
            message = f'Invalid state {state}'
        else:
            message = 'Invalid state'
        super().__init__(message)


class BrowserInitException(Exception):
    def __init__(self, message='Failed to initialize browser environment'):
        super().__init__(message)


class BrowserUnavailableException(Exception):
    def __init__(
        self,
        message='Browser environment is not available, please check if has been initialized',
    ):
        super().__init__(message)


# This exception gets sent back to the LLM
# It might be malformed JSON
class LLMMalformedActionError(Exception):
    def __init__(self, message='Malformed response'):
        super().__init__(message)


# This exception gets sent back to the LLM
# For some reason, the agent did not return an action
class LLMNoActionError(Exception):
    def __init__(self, message='Agent must return an action'):
        super().__init__(message)


# This exception gets sent back to the LLM
# The LLM output did not include an action, or the action was not the expected type
class LLMResponseError(Exception):
    def __init__(self, message='Failed to retrieve action from LLM response'):
        super().__init__(message)


class TokenLimitExceededError(Exception):
    """Exception raised when the user-defined max_input_tokens limit is exceeded."""

    def __init__(self, message='User-defined token limit exceeded. Condensing memory.'):
        super().__init__(message)


class ContextWindowLimitExceededError(Exception):
    def __init__(
        self, message='Context window limit exceeded. Unable to condense memory.'
    ):
        super().__init__(message)


class SummarizeError(Exception):
    """Exception raised when message can't be Summarized."""

    def __init__(self, message='Error Summarizing The Memory'):
        super().__init__(message)


class InvalidSummaryResponseError(Exception):
    def __init__(self, message='Invalid summary response'):
        super().__init__(message)
