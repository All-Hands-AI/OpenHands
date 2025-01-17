from pydantic import Field

from openhands.server.settings import Settings


class ConversationInitData(Settings):
    """
    Session initialization data for the web environment - a deep copy of the global config is made and then overridden with this data.
    """

    github_token: str | None = Field(default=None)
    selected_repository: str | None = Field(default=None)
