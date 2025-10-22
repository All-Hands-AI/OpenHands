"""Utility functions for UserSettings operations."""

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session
from storage.database import session_maker
from storage.user_settings import UserSettings

from openhands.utils.async_utils import call_sync_from_async


def get_user_settings_by_keycloak_id(
    keycloak_user_id: str, session: Optional[Session] = None
) -> Optional[UserSettings]:
    """
    Get UserSettings by keycloak_user_id.
    
    Args:
        keycloak_user_id: The keycloak user ID to search for
        session: Optional existing database session. If not provided, creates a new one.
        
    Returns:
        UserSettings object if found, None otherwise
    """
    if not keycloak_user_id:
        return None
        
    def _get_settings():
        if session:
            # Use provided session
            return (
                session.query(UserSettings)
                .filter(UserSettings.keycloak_user_id == keycloak_user_id)
                .first()
            )
        else:
            # Create new session
            with session_maker() as new_session:
                return (
                    new_session.query(UserSettings)
                    .filter(UserSettings.keycloak_user_id == keycloak_user_id)
                    .first()
                )
    
    return _get_settings()


async def get_user_settings_by_keycloak_id_async(
    keycloak_user_id: str, session: Optional[Session] = None
) -> Optional[UserSettings]:
    """
    Async version of get_user_settings_by_keycloak_id.
    
    Args:
        keycloak_user_id: The keycloak user ID to search for
        session: Optional existing database session. If not provided, creates a new one.
        
    Returns:
        UserSettings object if found, None otherwise
    """
    return await call_sync_from_async(
        get_user_settings_by_keycloak_id, keycloak_user_id, session
    )


def get_or_create_user_settings(
    keycloak_user_id: str, 
    session: Optional[Session] = None,
    **default_values
) -> UserSettings:
    """
    Get UserSettings by keycloak_user_id, creating it if it doesn't exist.
    
    Args:
        keycloak_user_id: The keycloak user ID to search for
        session: Optional existing database session. If not provided, creates a new one.
        **default_values: Default values to use when creating new UserSettings
        
    Returns:
        UserSettings object (existing or newly created)
    """
    if not keycloak_user_id:
        raise ValueError("keycloak_user_id cannot be empty")
        
    def _get_or_create():
        if session:
            # Use provided session
            settings = (
                session.query(UserSettings)
                .filter(UserSettings.keycloak_user_id == keycloak_user_id)
                .first()
            )
            if not settings:
                settings = UserSettings(
                    keycloak_user_id=keycloak_user_id,
                    **default_values
                )
                session.add(settings)
                session.flush()  # Flush to get the ID but don't commit
            return settings
        else:
            # Create new session
            with session_maker() as new_session:
                settings = (
                    new_session.query(UserSettings)
                    .filter(UserSettings.keycloak_user_id == keycloak_user_id)
                    .first()
                )
                if not settings:
                    settings = UserSettings(
                        keycloak_user_id=keycloak_user_id,
                        **default_values
                    )
                    new_session.add(settings)
                    new_session.commit()
                return settings
    
    return _get_or_create()


async def get_or_create_user_settings_async(
    keycloak_user_id: str, 
    session: Optional[Session] = None,
    **default_values
) -> UserSettings:
    """
    Async version of get_or_create_user_settings.
    
    Args:
        keycloak_user_id: The keycloak user ID to search for
        session: Optional existing database session. If not provided, creates a new one.
        **default_values: Default values to use when creating new UserSettings
        
    Returns:
        UserSettings object (existing or newly created)
    """
    return await call_sync_from_async(
        get_or_create_user_settings, keycloak_user_id, session, **default_values
    )