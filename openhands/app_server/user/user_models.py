from uuid import uuid4

from pydantic import Field

from openhands.storage.data_models.settings import Settings


class UserInfo(Settings):
    """Model for user settings including the current user id"""
    id: str = Field(default=lambda: uuid4().hex)
