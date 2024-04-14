from enum import Enum


class ActionType(str, Enum):
    INIT = "initialize"
    """Initializes the agent. Only sent by client.
    """

    START = "start"
    """Starts a new development task. Only sent by the client.
    """

    READ = "read"
    """Reads the content of a file.
    """

    WRITE = "write"
    """Writes the content to a file.
    """

    RUN = "run"
    """Runs a command.
    """

    KILL = "kill"
    """Kills a background command.
    """

    BROWSE = "browse"
    """Opens a web page.
    """

    RECALL = "recall"
    """Searches long-term memory
    """

    THINK = "think"
    """Allows the agent to make a plan, set a goal, or record thoughts
    """

    FINISH = "finish"
    """If you're absolutely certain that you've completed your task and have tested your work, 
    use the finish action to stop working.
    """

    CHAT = "chat"

    SUMMARIZE = "summarize"

    ADD_TASK = "add_task"

    MODIFY_TASK = "modify_task"

    NULL = "null"
