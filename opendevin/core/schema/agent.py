from enum import Enum


class AgentState(str, Enum):
    INIT = 'init'
    """Initial state of the task.
    """

    RUNNING = 'running'
    """The task is running.
    """

    AWAITING_USER_INPUT = 'awaiting_user_input'
    """The task is awaiting user input.
    """

    PAUSED = 'paused'
    """The task is paused.
    """

    STOPPED = 'stopped'
    """The task is stopped.
    """

    FINISHED = 'finished'
    """The task is finished.
    """

    ERROR = 'error'
    """An error occurred during the task.
    """
