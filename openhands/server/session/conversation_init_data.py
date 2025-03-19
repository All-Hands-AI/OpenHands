from pydantic import Field, SecretStr

from openhands.integrations.provider import CUSTOM_SECRETS_TYPE
from openhands.server.settings import Settings


class ConversationInitData(Settings):
    """
    Session initialization data for the web environment - a deep copy of the global config is made and then overridden with this data.
    """

    provider_token: SecretStr | None = Field(default=None)
    custom_secrets: CUSTOM_SECRETS_TYPE | None = Field(default=None, frozen=True)
    selected_repository: str | None = Field(default=None)
    selected_branch: str | None = Field(default=None)
