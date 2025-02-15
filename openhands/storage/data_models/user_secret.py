from datetime import datetime, timezone

from pydantic import BaseModel, Field, SecretStr, SerializationInfo, field_serializer
from pydantic.json import pydantic_encoder


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

    @field_serializer('value')
    def llm_api_key_serializer(self, value: SecretStr, info: SerializationInfo):
        """Custom serializer for the value

        To serialize the API key instead of ********, set expose_secrets to True in the serialization context.
        """
        context = info.context
        if context and context.get('expose_secrets', False):
            return value.get_secret_value()

        return pydantic_encoder(value)
