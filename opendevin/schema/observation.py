from pydantic import BaseModel, Field

__all__ = [
    'ObservationType'
]


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

    RECALL: str = Field(default='recall')
    """The result of a search
    """

    CHAT: str = Field(default='chat')
    """A message from the user
    """

    NULL: str = Field(default='null')

    MESSAGE: str = Field(default="message")

    ERROR: str = Field(default="error")


ObservationType = ObservationTypeSchema()
