from enum import Enum


class AgentState(str, Enum):
    LOADING = 'loading'
    """The agent is loading.
    """

    RUNNING = 'running'
    """The agent is running.
    """

    AWAITING_USER_INPUT = 'awaiting_user_input'
    """The agent is awaiting user input.
    """

    PAUSED = 'paused'
    """The agent is paused.
    """

    STOPPED = 'stopped'
    """The agent is stopped.
    """

    FINISHED = 'finished'
    """The agent is finished with the current task.
    """

    REJECTED = 'rejected'
    """The agent rejects the task.
    """

    ERROR = 'error'
    """An error occurred during the task.
    """

    AWAITING_USER_CONFIRMATION = 'awaiting_user_confirmation'
    """The agent is awaiting user confirmation.
    """

    USER_CONFIRMED = 'user_confirmed'
    """The user confirmed the agent's action.
    """

    USER_REJECTED = 'user_rejected'
    """The user rejected the agent's action.
    """

    RATE_LIMITED = 'rate_limited'
    """The agent is rate limited.
    """
