"""Validation functions for OpenHands CLI settings."""

from typing import Optional
from pydantic import SecretStr

from .constants import SUPPORTED_MODELS, SUPPORTED_AGENTS


def validate_model(model: str) -> str:
    """Validate LLM model name."""
    if model not in SUPPORTED_MODELS:
        raise ValueError(f"Unsupported model: {model}. Must be one of: {', '.join(SUPPORTED_MODELS)}")
    return model


def validate_agent_type(agent_type: str) -> str:
    """Validate agent type."""
    if agent_type not in SUPPORTED_AGENTS:
        raise ValueError(f"Unsupported agent type: {agent_type}. Must be one of: {', '.join(SUPPORTED_AGENTS)}")
    return agent_type


def validate_api_key(api_key: Optional[str]) -> Optional[SecretStr]:
    """Validate API key format."""
    if api_key is None:
        return None
    
    # Basic validation - ensure non-empty string
    if not api_key.strip():
        return None
    
    return SecretStr(api_key.strip())


def validate_base_url(base_url: Optional[str]) -> Optional[str]:
    """Validate base URL format."""
    if base_url is None:
        return None
    
    # Basic validation - ensure non-empty string
    base_url = base_url.strip()
    if not base_url:
        return None
    
    # Remove trailing slash for consistency
    if base_url.endswith('/'):
        base_url = base_url[:-1]
    
    return base_url