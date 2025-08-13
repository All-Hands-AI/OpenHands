from pydantic import BaseModel, Field


class CLIConfig(BaseModel):
    """Configuration for CLI-specific settings."""

    vi_mode: bool = Field(default=False)

    model_config = {'extra': 'forbid'}
