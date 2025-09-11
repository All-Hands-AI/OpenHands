"""Actions for validating settings."""

from typing import List, Optional, Tuple
from pydantic import ValidationError

from ...settings.models import CLISettings, LLMSettings, AgentSettings, OptionalSettings
from ...settings.validators import (
    validate_model,
    validate_agent_type,
    validate_api_key,
    validate_base_url
)


class ValidationResult:
    """Result of settings validation."""

    def __init__(self, is_valid: bool, errors: Optional[List[str]] = None):
        """Initialize validation result."""
        self.is_valid = is_valid
        self.errors = errors or []


class SettingsValidator:
    """Validator for settings."""

    @staticmethod
    def validate_llm_settings(settings: LLMSettings) -> ValidationResult:
        """Validate LLM settings."""
        errors = []
        
        try:
            validate_model(settings.model)
        except ValueError as e:
            errors.append(str(e))
        
        if settings.api_key:
            try:
                validate_api_key(settings.api_key.get_secret_value())
            except ValueError as e:
                errors.append(f'Invalid API key: {e}')
        
        if settings.base_url:
            try:
                validate_base_url(settings.base_url)
            except ValueError as e:
                errors.append(f'Invalid base URL: {e}')
        
        return ValidationResult(len(errors) == 0, errors)

    @staticmethod
    def validate_agent_settings(settings: AgentSettings) -> ValidationResult:
        """Validate agent settings."""
        errors = []
        
        try:
            validate_agent_type(settings.agent_type)
        except ValueError as e:
            errors.append(str(e))
        
        return ValidationResult(len(errors) == 0, errors)

    @staticmethod
    def validate_optional_settings(settings: OptionalSettings) -> ValidationResult:
        """Validate optional settings."""
        errors = []
        
        if settings.search_api_key:
            try:
                validate_api_key(settings.search_api_key.get_secret_value())
            except ValueError as e:
                errors.append(f'Invalid search API key: {e}')
        
        return ValidationResult(len(errors) == 0, errors)

    @staticmethod
    def validate_settings(settings: CLISettings) -> ValidationResult:
        """Validate all settings."""
        errors = []
        
        # Validate LLM settings
        llm_result = SettingsValidator.validate_llm_settings(settings.llm)
        if not llm_result.is_valid:
            errors.extend([f'LLM Settings: {e}' for e in llm_result.errors])
        
        # Validate agent settings
        agent_result = SettingsValidator.validate_agent_settings(settings.agent)
        if not agent_result.is_valid:
            errors.extend([f'Agent Settings: {e}' for e in agent_result.errors])
        
        # Validate optional settings
        optional_result = SettingsValidator.validate_optional_settings(settings.optional)
        if not optional_result.is_valid:
            errors.extend([f'Optional Settings: {e}' for e in optional_result.errors])
        
        return ValidationResult(len(errors) == 0, errors)