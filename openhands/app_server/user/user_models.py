from uuid import uuid4

from pydantic import Field

from openhands.integrations.provider import PROVIDER_TOKEN_TYPE
from openhands.storage.data_models.settings import Settings


class UserInfo(Settings):
    """Model for user settings including the current user id."""

    id: str = Field(default_factory=lambda: uuid4().hex)


class ProviderTokenPage:
    items: list[PROVIDER_TOKEN_TYPE]
    next_page_id: str | None = None
