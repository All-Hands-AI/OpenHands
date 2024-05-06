from enum import Enum


class AgentState(str, Enum):
    LOADING = 'loading'
    """The agent is loading.
    """

    INIT = 'init'
    """The agent is initialized.
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

    ERROR = 'error'
    """An error occurred during the task.
    """
