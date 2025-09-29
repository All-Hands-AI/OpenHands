"""
Enterprise utilities for subscription and pro user validation.

This module handles the conditional imports of enterprise modules and provides
utilities for checking pro user status and validating LLM settings access.
"""

from datetime import UTC, datetime

from fastapi import HTTPException

from openhands.core.logger import openhands_logger as logger
from openhands.server.shared import server_config
from openhands.server.types import AppMode
from openhands.storage.data_models.settings import Settings

# Enterprise imports - conditionally import based on environment
try:
    from enterprise.storage.database import session_maker
    from enterprise.storage.subscription_access import SubscriptionAccess

    ENTERPRISE_AVAILABLE = True
except ImportError as e:
    # In development environments, enterprise modules may not be available
    # Log at debug level instead of warning to reduce noise in development
    logger.debug(
        f'Enterprise modules not available: {e}. '
        'This is expected in development environments without Google Cloud SQL dependencies.'
    )
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
            is_pro = subscription_access is not None
            logger.warning(
                f'Subscription check for user {user_id}: is_pro={is_pro}, '
                f'subscription_found={subscription_access is not None}'
            )
            return is_pro

    except Exception as e:
        # Log the error for debugging but don't fail
        logger.warning(f'Could not check subscription status for user {user_id}: {e}')

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

    logger.warning(
        f'Validating LLM settings access for non-PRO user {user_id}. '
        f'App mode: {server_config.app_mode}, '
        f'Settings in request: {list(settings_dict.keys())}, '
        f'Has existing settings: {existing_settings is not None}'
    )

    if existing_settings:
        # Compare against existing settings to find what's actually being changed
        # Use regular model_dump() to include default values for proper comparison
        existing_dict = existing_settings.model_dump()
        changed_llm_settings = []

        for setting in settings_dict.keys():
            if setting in LLM_ONLY_SETTINGS:
                # Check if this LLM setting is actually being changed
                new_value = settings_dict.get(setting)
                existing_value = existing_dict.get(setting)

                # Log detailed comparison for debugging
                logger.warning(
                    f'Comparing LLM setting "{setting}" for user {user_id}: '
                    f'new_value={new_value} (type: {type(new_value)}), '
                    f'existing_value={existing_value} (type: {type(existing_value)}), '
                    f'are_equal={new_value == existing_value}'
                )

                # Consider it changed if:
                # 1. The values are different
                # 2. The setting didn't exist before (new setting)
                # BUT: If existing value is None and new value is the default, don't treat as change
                if new_value != existing_value:
                    # Check if this is just setting a default value when existing was None
                    if existing_value is None:
                        # Get the default value for this setting
                        default_settings = Settings()
                        default_dict = default_settings.model_dump()
                        default_value = default_dict.get(setting)

                        if new_value == default_value:
                            logger.warning(
                                f'LLM setting "{setting}" for user {user_id}: '
                                f'existing=None, new={new_value}, default={default_value} - '
                                f'treating as unchanged (setting to default)'
                            )
                            continue  # Skip this setting, don't treat as changed

                    changed_llm_settings.append(setting)
                    logger.warning(
                        f'LLM setting "{setting}" detected as changed for user {user_id}: '
                        f'{existing_value} -> {new_value}'
                    )
    else:
        # No existing settings to compare against - compare against default values
        default_settings = Settings()
        default_dict = default_settings.model_dump()
        changed_llm_settings = []

        for setting in settings_dict.keys():
            if setting in LLM_ONLY_SETTINGS:
                # Check if this LLM setting is different from the default
                new_value = settings_dict.get(setting)
                default_value = default_dict.get(setting)

                # Log detailed comparison for debugging
                logger.warning(
                    f'Comparing LLM setting "{setting}" against default for user {user_id}: '
                    f'new_value={new_value} (type: {type(new_value)}), '
                    f'default_value={default_value} (type: {type(default_value)}), '
                    f'are_equal={new_value == default_value}'
                )

                if new_value != default_value:
                    changed_llm_settings.append(setting)
                    logger.warning(
                        f'LLM setting "{setting}" detected as different from default for user {user_id}: '
                        f'default={default_value} -> new={new_value}'
                    )

    if changed_llm_settings:
        logger.warning(
            f'Non-PRO user {user_id} attempted to modify LLM settings in SaaS mode: {changed_llm_settings}'
        )
        raise HTTPException(
            status_code=403,
            detail=f'PRO subscription required to modify LLM settings in SaaS mode. '
            f'Upgrade your account to access these features: {", ".join(changed_llm_settings)}',
        )
