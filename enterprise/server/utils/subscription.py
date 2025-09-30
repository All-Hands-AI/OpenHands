"""
Enterprise subscription and LLM settings validation utilities.

This module contains utility functions for checking PRO user status and validating
LLM settings access in SaaS mode.
"""

from datetime import UTC, datetime

from openhands.core.logger import openhands_logger as logger
from openhands.storage.data_models.settings import Settings

from storage.database import session_maker
from storage.subscription_access import SubscriptionAccess


class ProSubscriptionRequiredError(Exception):
    """
    Exception raised when a non-PRO user attempts to modify LLM settings in SaaS mode.

    This exception is specifically designed to be caught by middleware to return
    appropriate HTTP 403 responses.
    """

    def __init__(self, changed_settings: list[str], user_id: str | None = None):
        self.changed_settings = changed_settings
        self.user_id = user_id

        settings_list = ", ".join(changed_settings)
        message = (
            f'PRO subscription required to modify LLM settings in SaaS mode. '
            f'Upgrade your account to access these features: {settings_list}'
        )
        super().__init__(message)


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


def validate_llm_settings_changes(settings_dict: dict, current_settings: dict | None = None) -> list[str]:
    """
    Check which LLM settings are being changed from their current values.

    Args:
        settings_dict: Dictionary of settings being requested
        current_settings: Dictionary of user's current settings (optional)

    Returns:
        List of LLM setting names that are being changed
    """
    changed_llm_settings = []
    
    # If no current settings provided, compare against defaults
    if current_settings is None:
        current_settings = Settings().model_dump()

    for setting in settings_dict.keys():
        if setting in LLM_ONLY_SETTINGS:
            # Check if this LLM setting is being changed from current value
            new_value = settings_dict.get(setting)
            current_value = current_settings.get(setting)

            if new_value != current_value:
                changed_llm_settings.append(setting)
                logger.debug(
                    f'LLM setting "{setting}" detected as being changed: '
                    f'current={current_value} -> new={new_value}'
                )

    return changed_llm_settings
