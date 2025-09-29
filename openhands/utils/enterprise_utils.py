"""
Enterprise utilities for subscription and pro user validation.

This module handles the conditional imports of enterprise modules and provides
utilities for checking pro user status and validating LLM settings access.
"""

from datetime import UTC, datetime

from openhands.core.logger import openhands_logger as logger
from openhands.server.shared import server_config
from openhands.server.types import AppMode
from openhands.storage.data_models.settings import Settings

# Enterprise imports - require Google Cloud SQL dependencies that may not be installed in development environments
try:
    from enterprise.storage.database import session_maker
    from enterprise.storage.subscription_access import SubscriptionAccess

    ENTERPRISE_AVAILABLE = True
except ImportError:
    session_maker = None  # type: ignore
    SubscriptionAccess = None  # type: ignore
    ENTERPRISE_AVAILABLE = False


# LLM-only settings that require PRO subscription in SaaS mode
LLM_ONLY_SETTINGS = {
    'llm_model',
    'llm_api_key',
    'llm_base_url',
    'search_api_key',
    'agent',
    'confirmation_mode',
    'security_analyzer',
    'enable_default_condenser',
    'condenser_max_size',
}


def is_pro_user(user_id: str | None) -> bool:
    """
    Determine if a user is a PRO user by checking their active subscription status.

    This function checks the subscription_access table for an active subscription
    that is currently valid (within start_at and end_at dates).

    Returns False if the user_id is None or if no active subscription is found.
    """
    if not user_id:
        return False

    if not ENTERPRISE_AVAILABLE:
        # Enterprise modules not available, assume non-pro user (safe default)
        logger.debug(
            f'Enterprise modules not available, treating user {user_id} as non-pro'
        )
        return False

    try:
        # Query for active subscription
        with session_maker() as session:
            now = datetime.now(UTC)
            subscription_access = (
                session.query(SubscriptionAccess)
                .filter(SubscriptionAccess.status == 'ACTIVE')
                .filter(SubscriptionAccess.user_id == user_id)
                .filter(SubscriptionAccess.start_at <= now)
                .filter(SubscriptionAccess.end_at >= now)
                .first()
            )
            return subscription_access is not None

    except Exception as e:
        # Log the error for debugging but don't fail
        logger.debug(f'Could not check subscription status for user {user_id}: {e}')

        # If there's an error, assume non-pro user (safe default)
        return False


def validate_llm_settings_access(
    settings: Settings, user_id: str | None, existing_settings: Settings | None = None
) -> None:
    """
    Validate that non-PRO users in SaaS mode cannot modify LLM settings.

    This enforces a strict security policy where non-PRO users in SaaS mode
    are not allowed to change LLM settings. If existing_settings is provided,
    only validates fields that are actually being changed.

    Args:
        settings: The settings object containing the user's requested settings
        user_id: The user ID to check for PRO status
        existing_settings: The current settings to compare against (optional)

    Raises:
        HTTPException: 403 Forbidden if non-PRO user tries to modify LLM settings in SaaS mode
    """
    # Only enforce in SaaS mode
    if server_config.app_mode != AppMode.SAAS:
        return

    # Check if user is PRO
    if is_pro_user(user_id):
        return

    # Non-PRO user in SaaS mode - check which LLM settings are being changed
    settings_dict = settings.model_dump(exclude_unset=True)

    if existing_settings:
        # Compare against existing settings to find what's actually being changed
        existing_dict = existing_settings.model_dump(exclude_unset=True)
        changed_llm_settings = []

        for setting in settings_dict.keys():
            if setting in LLM_ONLY_SETTINGS:
                # Check if this LLM setting is actually being changed
                new_value = settings_dict.get(setting)
                existing_value = existing_dict.get(setting)

                # Consider it changed if:
                # 1. The values are different
                # 2. The setting didn't exist before (new setting)
                if new_value != existing_value:
                    changed_llm_settings.append(setting)
    else:
        # No existing settings to compare against - treat all LLM settings as changes
        changed_llm_settings = [
            setting for setting in settings_dict.keys() if setting in LLM_ONLY_SETTINGS
        ]

    if changed_llm_settings:
        from fastapi import HTTPException

        logger.warning(
            f'Non-PRO user {user_id} attempted to modify LLM settings in SaaS mode: {changed_llm_settings}'
        )
        raise HTTPException(
            status_code=403,
            detail=f'PRO subscription required to modify LLM settings in SaaS mode. '
            f'Upgrade your account to access these features: {", ".join(changed_llm_settings)}',
        )
