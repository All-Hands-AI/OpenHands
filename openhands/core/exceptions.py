# ============================================
# Agent Exceptions
# ============================================


class AgentError(Exception):
    """Base class for all agent exceptions."""

    pass


class AgentNoInstructionError(AgentError):
    def __init__(self, message='Instruction must be provided'):
        super().__init__(message)


class AgentEventTypeError(AgentError):
    def __init__(self, message='Event must be a dictionary'):
        super().__init__(message)


class AgentAlreadyRegisteredError(AgentError):
    def __init__(self, name=None):
        if name is not None:
            message = f"Agent class already registered under '{name}'"
        else:
            message = 'Agent class already registered'
        super().__init__(message)


class AgentNotRegisteredError(AgentError):
    def __init__(self, name=None):
        if name is not None:
            message = f"No agent class registered under '{name}'"
        else:
            message = 'No agent class registered'
        super().__init__(message)


class AgentStuckInLoopError(AgentError):
    def __init__(self, message='Agent got stuck in a loop'):
        super().__init__(message)


# ============================================
# Agent Controller Exceptions
# ============================================


class TaskInvalidStateError(Exception):
    def __init__(self, state=None):
        if state is not None:
            message = f'Invalid state {state}'
        else:
            message = 'Invalid state'
        super().__init__(message)


# ============================================
# LLM Exceptions
# ============================================


# This exception gets sent back to the LLM
# It might be malformed JSON
class LLMMalformedActionError(Exception):
    def __init__(self, message='Malformed response'):
        self.message = message
        super().__init__(message)

    def __str__(self):
        return self.message


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


class UserCancelledError(Exception):
    def __init__(self, message='User cancelled the request'):
        super().__init__(message)


class MicroAgentValidationError(Exception):
    def __init__(self, message='Micro agent validation failed'):
        super().__init__(message)


class OperationCancelled(Exception):
    """Exception raised when an operation is cancelled (e.g. by a keyboard interrupt)."""

    def __init__(self, message='Operation was cancelled'):
        super().__init__(message)


class CloudFlareBlockageError(Exception):
    """Exception raised when a request is blocked by CloudFlare."""

    pass


# ============================================
# LLM function calling Exceptions
# ============================================


class FunctionCallConversionError(Exception):
    """Exception raised when FunctionCallingConverter failed to convert a non-function call message to a function call message.

    This typically happens when there's a malformed message (e.g., missing <function=...> tags). But not due to LLM output.
    """

    def __init__(self, message):
        super().__init__(message)


class FunctionCallValidationError(Exception):
    """Exception raised when FunctionCallingConverter failed to validate a function call message.

    This typically happens when the LLM outputs unrecognized function call / parameter names / values.
    """

    def __init__(self, message):
        super().__init__(message)


class FunctionCallNotExistsError(Exception):
    """Exception raised when an LLM call a tool that is not registered."""

    def __init__(self, message):
        super().__init__(message)


# ============================================
# Agent Runtime Exceptions
# ============================================


class AgentRuntimeError(Exception):
    """Base class for all agent runtime exceptions."""

    pass


class AgentRuntimeBuildError(AgentRuntimeError):
    """Exception raised when an agent runtime build operation fails."""

    pass


class AgentRuntimeTimeoutError(AgentRuntimeError):
    """Exception raised when an agent runtime operation times out."""

    pass


class AgentRuntimeUnavailableError(AgentRuntimeError):
    """Exception raised when an agent runtime is unavailable."""

    pass


class AgentRuntimeNotReadyError(AgentRuntimeUnavailableError):
    """Exception raised when an agent runtime is not ready."""

    pass


class AgentRuntimeDisconnectedError(AgentRuntimeUnavailableError):
    """Exception raised when an agent runtime is disconnected."""

    pass


class AgentRuntimeNotFoundError(AgentRuntimeUnavailableError):
    """Exception raised when an agent runtime is not found."""

    pass


# ============================================
# Browser Exceptions
# ============================================


class BrowserInitException(Exception):
    def __init__(self, message='Failed to initialize browser environment'):
        super().__init__(message)


class BrowserUnavailableException(Exception):
    def __init__(
        self,
        message='Browser environment is not available, please check if has been initialized',
    ):
        super().__init__(message)
