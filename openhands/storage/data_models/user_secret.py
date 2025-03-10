from datetime import datetime, timezone
from typing import Annotated, Union

from pydantic import BaseModel, Field

from openhands.storage.data_models.token_factory import ApiKey, GithubToken


class UserSecret(BaseModel):
    """
    A secret value for a user (e.g.: An API key) Keys are unique within the context of a user.
    """

    id: str
    key: str
    user_id: str | None
    token_factory: Annotated[
        Union[ApiKey | GithubToken],
        Field(discriminator='type'),
    ]
    description: str | None = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    '''
    @field_serializer('value')
    def llm_api_key_serializer(self, value: SecretStr, info: SerializationInfo):
        """Custom serializer for the value

        To serialize the API key instead of ********, set expose_secrets to True in the serialization context.
        """
        context = info.context
        if context and context.get('expose_secrets', False):
            return value.get_secret_value()

        return pydantic_encoder(value)
    '''
