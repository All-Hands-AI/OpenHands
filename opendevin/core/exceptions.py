class MaxCharsExceedError(Exception):
    def __init__(self, num_of_chars=None, max_chars_limit=None):
        if num_of_chars is not None and max_chars_limit is not None:
            message = f'Number of characters {num_of_chars} exceeds MAX_CHARS limit: {max_chars_limit}'
        else:
            message = 'Number of characters exceeds MAX_CHARS limit'
        super().__init__(message)


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


class LLMOutputError(Exception):
    def __init__(self, message):
        super().__init__(message)


class SandboxInvalidBackgroundCommandError(Exception):
    def __init__(self, id=None):
        if id is not None:
            message = f'Invalid background command id {id}'
        else:
            message = 'Invalid background command id'
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


# These exceptions get sent back to the LLM
class AgentMalformedActionError(Exception):
    def __init__(self, message='Malformed response'):
        super().__init__(message)


class AgentNoActionError(Exception):
    def __init__(self, message='Agent must return an action'):
        super().__init__(message)
