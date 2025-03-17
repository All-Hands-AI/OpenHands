from pydantic import Field

from openhands.integrations.provider import PROVIDER_TOKEN_TYPE
from openhands.server.settings import Settings


class ConversationInitData(Settings):
    """
    Session initialization data for the web environment - a deep copy of the global config is made and then overridden with this data.
    """

    provider_tokens: PROVIDER_TOKEN_TYPE | None = Field(default=None)
    selected_repository: str | None = Field(default=None)
    selected_branch: str | None = Field(default=None)
