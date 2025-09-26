"""Settings validation utilities for LLM settings access control."""

from pydantic import SecretStr

from openhands.core.logger import openhands_logger as logger
from openhands.server.shared import server_config
from openhands.server.types import AppMode
from openhands.storage.data_models.settings import Settings


def _is_llm_setting_changing(setting_name: str, new_value, existing_settings) -> bool:
    """Check if a specific LLM setting is being changed from its existing value.

    Args:
        setting_name: Name of the setting to check
        new_value: New value being set
        existing_settings: Existing settings object (can be None)

    Returns:
        bool: True if the setting is being changed, False otherwise
    """
    if new_value is None:
        return False

    # Handle special case for enable_default_condenser with default value
    if setting_name == 'enable_default_condenser':
        if not existing_settings:
            # First time setting - only validate if setting to non-default value
            return not new_value
        else:
            # Changing existing value
            return new_value != existing_settings.enable_default_condenser

    # For other settings, validate if explicitly provided and different from existing
    if not existing_settings:
        return True

    existing_value = getattr(existing_settings, setting_name, None)
    return new_value != existing_value


def check_llm_settings_changes(settings: Settings, existing_settings) -> bool:
    """Check if any LLM-related settings are being changed.

    Validates both core LLM settings (model, API key, base URL) and advanced settings
    shown to SaaS users (confirmation mode, security analyzer, memory condenser settings).

    Args:
        settings: New settings being applied
        existing_settings: Current settings (can be None)

    Returns:
        bool: True if any LLM settings are being changed, False otherwise
    """

    # Core LLM settings - validate only if actually changing compared to existing
    # Handle SecretStr safely by comparing raw values if both present
    def _secret_equals(a: SecretStr | None, b: SecretStr | None) -> bool:
        if a is None and b is None:
            return True
        if a is None or b is None:
            return False
        try:
            return a.get_secret_value() == b.get_secret_value()
        except Exception:
            # If any issue, fall back to object equality (best effort)
            return a == b

    existing_model = (
        getattr(existing_settings, 'llm_model', None) if existing_settings else None
    )
    existing_base_url = (
        getattr(existing_settings, 'llm_base_url', None) if existing_settings else None
    )
    existing_api_key = (
        getattr(existing_settings, 'llm_api_key', None) if existing_settings else None
    )

    core_llm_changes = False
    if settings.llm_model is not None:
        core_llm_changes = core_llm_changes or (settings.llm_model != existing_model)
    if settings.llm_base_url is not None:
        core_llm_changes = core_llm_changes or (
            settings.llm_base_url != existing_base_url
        )
    if settings.llm_api_key is not None:
        core_llm_changes = core_llm_changes or (
            not _secret_equals(settings.llm_api_key, existing_api_key)
        )

    if core_llm_changes:
        return True

    # Additional LLM settings shown to SaaS users - validate if actually changing
    advanced_llm_changes = any(
        [
            _is_llm_setting_changing(
                'confirmation_mode', settings.confirmation_mode, existing_settings
            ),
            _is_llm_setting_changing(
                'security_analyzer', settings.security_analyzer, existing_settings
            ),
            _is_llm_setting_changing(
                'enable_default_condenser',
                settings.enable_default_condenser,
                existing_settings,
            ),
            _is_llm_setting_changing(
                'condenser_max_size', settings.condenser_max_size, existing_settings
            ),
        ]
    )

    return advanced_llm_changes


async def validate_llm_settings_access(user_id: str) -> bool:
    """Validate if user has access to modify LLM settings in SaaS mode.

    In SaaS mode, only pro users with active subscriptions can modify LLM settings.

    Args:
        user_id: The user ID to check subscription for

    Returns:
        bool: True if user can modify LLM settings, False otherwise
    """
    # Skip validation in non-SaaS mode
    if server_config.app_mode != AppMode.SAAS:
        return True

    # In SaaS mode, check for active subscription for ANY LLM settings changes
    try:
        # Import here to avoid circular imports and handle enterprise mode gracefully
        from enterprise.server.routes.billing import get_subscription_access

        subscription = await get_subscription_access(user_id)
        # The get_subscription_access function already filters for ACTIVE status,
        # so if we get a subscription back, it means it's active
        return subscription is not None
    except ImportError:
        # Enterprise billing module not available - in SaaS mode, this means
        # we can't validate subscriptions, so deny access to be safe
        logger.warning(
            'Enterprise billing module not available in SaaS mode, denying LLM settings access'
        )
        return False
    except Exception as e:
        # On error, deny access to be safe
        logger.warning(f'Error checking subscription access for user {user_id}: {e}')
        return False
