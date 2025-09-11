"""Validation utilities for settings configuration."""

from typing import Any, Callable, Optional, TypeVar, Union
from pydantic import SecretStr, ValidationError

from openhands.core.config.llm_config import LLMConfig


T = TypeVar('T')
ValidatorFunc = Callable[[Any], bool]


class ValidationError(Exception):
    """Validation error with message."""

    def __init__(self, message: str):
        """Initialize validation error."""
        self.message = message
        super().__init__(message)


def validate_float_range(
    value: Union[float, str],
    min_value: float,
    max_value: float,
    name: str
) -> float:
    """Validate float value within range."""
    try:
        float_value = float(value)
    except (ValueError, TypeError):
        raise ValidationError(
            f'{name} must be a number between {min_value} and {max_value}'
        )

    if not min_value <= float_value <= max_value:
        raise ValidationError(
            f'{name} must be between {min_value} and {max_value}'
        )

    return float_value


def validate_int_range(
    value: Union[int, str],
    min_value: int,
    max_value: Optional[int] = None,
    name: str = 'Value'
) -> int:
    """Validate integer value within range."""
    try:
        int_value = int(value)
    except (ValueError, TypeError):
        raise ValidationError(f'{name} must be a whole number')

    if min_value is not None and int_value < min_value:
        raise ValidationError(f'{name} must be at least {min_value}')

    if max_value is not None and int_value > max_value:
        raise ValidationError(f'{name} must be at most {max_value}')

    return int_value


def validate_non_empty(value: str, name: str = 'Value') -> str:
    """Validate non-empty string."""
    if not value or not value.strip():
        raise ValidationError(f'{name} cannot be empty')
    return value.strip()


def validate_url(value: str) -> str:
    """Validate URL format."""
    # Basic URL validation - could be made more sophisticated
    value = value.strip()
    if not value:
        return value

    if not (
        value.startswith('http://') or
        value.startswith('https://') or
        value.startswith('ws://') or
        value.startswith('wss://')
    ):
        raise ValidationError('URL must start with http://, https://, ws://, or wss://')

    return value


def validate_temperature(value: Union[float, str]) -> float:
    """Validate temperature value."""
    return validate_float_range(value, 0.0, 1.0, 'Temperature')


def validate_top_p(value: Union[float, str]) -> float:
    """Validate top p value."""
    return validate_float_range(value, 0.0, 1.0, 'Top P')


def validate_max_tokens(value: Union[int, str, None]) -> Optional[int]:
    """Validate max tokens value."""
    if not value:
        return None
    return validate_int_range(value, 1, name='Max tokens')


def validate_model_name(value: str) -> str:
    """Validate model name."""
    return validate_non_empty(value, 'Model name')


def validate_api_key(value: Optional[str]) -> Optional[str]:
    """Validate API key."""
    if value is None:
        return None
    return validate_non_empty(value, 'API key')


def validate_llm_config(config: LLMConfig) -> None:
    """Validate complete LLM configuration."""
    try:
        validate_model_name(config.model)
        validate_api_key(
            config.api_key.get_secret_value() if config.api_key else None
        )
        if config.base_url:
            validate_url(config.base_url)
        validate_temperature(config.temperature)
        validate_top_p(config.top_p)
        if config.max_output_tokens is not None:
            validate_max_tokens(config.max_output_tokens)
    except ValidationError as e:
        raise ValidationError(f'Invalid LLM configuration: {e.message}')