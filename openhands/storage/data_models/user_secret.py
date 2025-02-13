from datetime import datetime, timezone

from pydantic import BaseModel, Field, SecretStr


class UserSecret(BaseModel):
    """
    A secret value for a user (e.g.: An API key) Keys are unique within the context of a user.
    """

    id: str
    key: str
    user_id: str | None
    value: SecretStr
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
