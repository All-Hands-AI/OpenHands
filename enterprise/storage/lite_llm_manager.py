"""
Store class for managing organizational settings.
"""

import functools
import os
from typing import Any, Awaitable, Callable

import httpx
from pydantic import SecretStr
from openhands.enterprise.server.auth.token_manager import TokenManager
from openhands.enterprise.server.constants import (
    DEFAULT_INITIAL_BUDGET,
    LITE_LLM_API_KEY,
    LITE_LLM_API_URL,
    LITE_LLM_TEAM_ID,
    ORG_SETTINGS_VERSION,
    get_default_litellm_model,
)
from openhands.enterprise.server.logger import logger
from openhands.enterprise.storage.user_settings import UserSettings

from openhands.storage.data_models.settings import Settings


class LiteLlmManager:
    """Manage LiteLLM interactions."""

    @staticmethod
    async def create_entries(
        org_id: str,
        keycloak_user_id: str,
        oss_settings: Settings,
    ) -> Settings | None:
        logger.info(
            'SettingsStore:update_settings_with_litellm_default:start',
            extra={'org_id': org_id, 'user_id': keycloak_user_id},
        )
        if LITE_LLM_API_KEY is None or LITE_LLM_API_URL is None:
            logger.warning('LiteLLM API configuration not found')
            return None
        local_deploy = os.environ.get('LOCAL_DEPLOYMENT', None)
        key = LITE_LLM_API_KEY
        if not local_deploy:
            # Get user info to add to litellm
            token_manager = TokenManager()
            keycloak_user_info = (
                await token_manager.get_user_info_from_user_id(keycloak_user_id) or {}
            )

            # Create team in LiteLLM
            await LiteLlmManager.create_team(
                team_id=org_id,
                team_alias=keycloak_user_info.get('preferred_username', 'Unknown'),
                max_budget=DEFAULT_INITIAL_BUDGET,
            )

            # Create user in LiteLLM
            key = await LiteLlmManager.create_user(
                user_id=keycloak_user_id,
                user_email=keycloak_user_info.get('email', 'unknown@example.com'),
                team_id=org_id,
            )

        if key:
            oss_settings.llm_api_key = key
            oss_settings.llm_model = get_default_litellm_model()

        return oss_settings

    @staticmethod
    async def migrate_entries(
        org_id: str,
        keycloak_user_id: str,
        user_settings: UserSettings,
    ) -> None:
        """Migrate existing user settings to org structure."""
        if LITE_LLM_API_KEY is None or LITE_LLM_API_URL is None:
            logger.warning('LiteLLM API configuration not found')
            return

        local_deploy = os.environ.get('LOCAL_DEPLOYMENT', None)
        if not local_deploy:
            # Get user info
            token_manager = TokenManager()
            keycloak_user_info = (
                await token_manager.get_user_info_from_user_id(keycloak_user_id) or {}
            )

            # Create team in LiteLLM
            await LiteLlmManager.create_team(
                team_id=org_id,
                team_alias=keycloak_user_info.get('preferred_username', 'Unknown'),
                max_budget=DEFAULT_INITIAL_BUDGET,
            )

            # Migrate user to team
            await LiteLlmManager.update_user_team(
                user_id=keycloak_user_id,
                team_id=org_id,
            )

    @staticmethod
    async def create_team(
        team_id: str,
        team_alias: str,
        max_budget: float,
    ) -> bool:
        """Create a team in LiteLLM."""
        if LITE_LLM_API_KEY is None or LITE_LLM_API_URL is None:
            return False

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f'{LITE_LLM_API_URL}/team/new',
                    headers={'Authorization': f'Bearer {LITE_LLM_API_KEY}'},
                    json={
                        'team_id': team_id,
                        'team_alias': team_alias,
                        'max_budget': max_budget,
                    },
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f'Failed to create team: {e}')
            return False

    @staticmethod
    async def update_team(
        team_id: str,
        team_alias: str | None = None,
        max_budget: float | None = None,
    ) -> bool:
        """Update a team in LiteLLM."""
        if LITE_LLM_API_KEY is None or LITE_LLM_API_URL is None:
            return False

        try:
            async with httpx.AsyncClient() as client:
                data = {'team_id': team_id}
                if team_alias is not None:
                    data['team_alias'] = team_alias
                if max_budget is not None:
                    data['max_budget'] = max_budget

                response = await client.post(
                    f'{LITE_LLM_API_URL}/team/update',
                    headers={'Authorization': f'Bearer {LITE_LLM_API_KEY}'},
                    json=data,
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f'Failed to update team: {e}')
            return False

    @staticmethod
    async def create_user(
        user_id: str,
        user_email: str,
        team_id: str,
    ) -> str | None:
        """Create a user in LiteLLM and return their API key."""
        if LITE_LLM_API_KEY is None or LITE_LLM_API_URL is None:
            return None

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f'{LITE_LLM_API_URL}/user/new',
                    headers={'Authorization': f'Bearer {LITE_LLM_API_KEY}'},
                    json={
                        'user_id': user_id,
                        'user_email': user_email,
                        'team_id': team_id,
                    },
                )
                if response.status_code == 200:
                    data = response.json()
                    return data.get('key')
        except Exception as e:
            logger.error(f'Failed to create user: {e}')
        return None

    @staticmethod
    async def update_user_team(
        user_id: str,
        team_id: str,
    ) -> bool:
        """Update a user's team in LiteLLM."""
        if LITE_LLM_API_KEY is None or LITE_LLM_API_URL is None:
            return False

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f'{LITE_LLM_API_URL}/user/update',
                    headers={'Authorization': f'Bearer {LITE_LLM_API_KEY}'},
                    json={
                        'user_id': user_id,
                        'team_id': team_id,
                    },
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f'Failed to update user team: {e}')
            return False