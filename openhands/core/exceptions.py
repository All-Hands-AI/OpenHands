class OpenHandsError(Exception):
    """Base class for OpenHands exceptions."""
    def __init__(self, message: str | None = None):
        super().__init__(message or self.default_message)

    @property
    def default_message(self) -> str:
        return 'An error occurred in OpenHands'


class AgentNoInstructionError(OpenHandsError):
    default_message = 'Instruction must be provided'


class AgentEventTypeError(OpenHandsError):
    default_message = 'Event must be a dictionary'


class AgentAlreadyRegisteredError(OpenHandsError):
    def __init__(self, name: str | None = None):
        super().__init__(f"Agent class already registered under '{name}'" if name else 'Agent class already registered')


class AgentNotRegisteredError(OpenHandsError):
    def __init__(self, name: str | None = None):
        super().__init__(f"No agent class registered under '{name}'" if name else 'No agent class registered')


class TaskInvalidStateError(OpenHandsError):
    def __init__(self, state: str | None = None):
        super().__init__(f'Invalid state {state}' if state else 'Invalid state')


class BrowserInitException(OpenHandsError):
    default_message = 'Failed to initialize browser environment'


class BrowserUnavailableException(OpenHandsError):
    default_message = 'Browser environment is not available, please check if has been initialized'


class LLMMalformedActionError(OpenHandsError):
    default_message = 'Malformed response'

    def __str__(self):
        return str(self.args[0]) if self.args else self.default_message


class LLMNoActionError(OpenHandsError):
    default_message = 'Agent must return an action'


class LLMResponseError(OpenHandsError):
    default_message = 'Failed to retrieve action from LLM response'


class UserCancelledError(OpenHandsError):
    default_message = 'User cancelled the request'


class MicroAgentValidationError(OpenHandsError):
    default_message = 'Micro agent validation failed'


class OperationCancelled(OpenHandsError):
    """Exception raised when an operation is cancelled (e.g. by a keyboard interrupt)."""
    default_message = 'Operation was cancelled'


class CloudFlareBlockageError(OpenHandsError):
    """Exception raised when a request is blocked by CloudFlare."""
    default_message = 'Request blocked by CloudFlare'

