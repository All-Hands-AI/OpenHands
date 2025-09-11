"""Data models for OpenHands CLI settings."""

from typing import Optional
from pydantic import BaseModel, SecretStr, Field

from .constants import DEFAULT_MODEL, DEFAULT_AGENT_TYPE, DEFAULT_CONFIRMATION_MODE
from .validators import validate_model, validate_agent_type, validate_api_key, validate_base_url


class LLMSettings(BaseModel):
    """Settings for LLM configuration."""
    model: str = Field(default=DEFAULT_MODEL)
    api_key: Optional[SecretStr] = None
    base_url: Optional[str] = None

    _validate_model = validate_model
    _validate_api_key = validate_api_key
    _validate_base_url = validate_base_url


class AgentSettings(BaseModel):
    """Settings for agent configuration."""
    agent_type: str = Field(default=DEFAULT_AGENT_TYPE)
    confirmation_mode: bool = Field(default=DEFAULT_CONFIRMATION_MODE)

    _validate_agent_type = validate_agent_type


class OptionalSettings(BaseModel):
    """Optional feature settings."""
    search_api_key: Optional[SecretStr] = None

    _validate_search_api_key = validate_api_key


class CLISettings(BaseModel):
    """Main settings model for OpenHands CLI."""
    llm: LLMSettings = Field(default_factory=LLMSettings)
    agent: AgentSettings = Field(default_factory=AgentSettings)
    optional: OptionalSettings = Field(default_factory=OptionalSettings)

    class Config:
        validate_assignment = True