from pydantic import BaseModel, Field

__all__ = ['ObservationType']


class ObservationTypeSchema(BaseModel):
    READ: str = Field(default='read')
    """The content of a file
    """

    WRITE: str = Field(default='write')

    BROWSE: str = Field(default='browse')
    """The HTML content of a URL
    """

    RUN: str = Field(default='run')
    """The output of a command
    """

    RUN_IPYTHON: str = Field(default='run_ipython')
    """Runs a IPython cell.
    """

    RECALL: str = Field(default='recall')
    """The result of a search
    """

    CHAT: str = Field(default='chat')
    """A message from the user
    """

    DELEGATE: str = Field(default='delegate')
    """The result of a task delegated to another agent
    """

    MESSAGE: str = Field(default='message')

    ERROR: str = Field(default='error')

    SUCCESS: str = Field(default='success')

    NULL: str = Field(default='null')

    AGENT_STATE_CHANGED: str = Field(default='agent_state_changed')


ObservationType = ObservationTypeSchema()
