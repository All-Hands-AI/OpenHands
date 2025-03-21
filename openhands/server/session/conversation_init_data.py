from types import MappingProxyType
from pydantic import Field

from openhands.integrations.provider import CUSTOM_SECRETS_TYPE
from openhands.integrations.provider import PROVIDER_TOKEN_TYPE
from openhands.server.settings import Settings


class ConversationInitData(Settings):
    """
    Session initialization data for the web environment - a deep copy of the global config is made and then overridden with this data.
    """

    custom_secrets: CUSTOM_SECRETS_TYPE | None = Field(default=None, frozen=True)
    git_provider_tokens: PROVIDER_TOKEN_TYPE | None = Field(default=None, frozen=True)
    selected_repository: str | None = Field(default=None)
    selected_branch: str | None = Field(default=None)

    model_config = {
        'arbitrary_types_allowed': True,
    }