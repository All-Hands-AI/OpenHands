from pydantic import BaseModel, ConfigDict, Field


class UserSecrets(BaseModel):
    """Simplified UserSecrets for configuration project.
    
    This is a simplified version that doesn't depend on the complex integration types.
    """
    provider_tokens: dict = Field(default_factory=dict)
    custom_secrets: dict = Field(default_factory=dict)

    model_config = ConfigDict(
        frozen=True,
        validate_assignment=True,
    )