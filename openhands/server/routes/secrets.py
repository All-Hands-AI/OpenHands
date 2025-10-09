import os
import re
import subprocess
from typing import Any

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from openhands.core.logger import openhands_logger as logger
from openhands.integrations.provider import PROVIDER_TOKEN_TYPE, CustomSecret
from openhands.integrations.service_types import ProviderType
from openhands.integrations.utils import validate_provider_token
from openhands.server.dependencies import get_dependencies
from openhands.server.settings import (
    CustomSecretModel,
    CustomSecretWithoutValueModel,
    GETCustomSecrets,
    POSTProviderModel,
)
from openhands.server.user_auth import (
    get_provider_tokens,
    get_secrets_store,
    get_user_secrets,
)
from openhands.storage.data_models.settings import Settings
from openhands.storage.data_models.user_secrets import UserSecrets
from openhands.storage.secrets.secrets_store import SecretsStore
from openhands.storage.settings.settings_store import SettingsStore

app = APIRouter(prefix='/api', dependencies=get_dependencies())


# =================================================
# SECTION: Git URL update helpers
# =================================================


def get_provider_from_url(url: str) -> ProviderType | None:
    """Extract provider type from git URL."""
    if 'github.com' in url:
        return ProviderType.GITHUB
    elif 'gitlab.com' in url:
        return ProviderType.GITLAB
    elif 'bitbucket.org' in url:
        return ProviderType.BITBUCKET
    return None


def update_url_with_token(old_url: str, provider: ProviderType, new_token: str) -> str:
    """Replace token in git URL with new token."""
    if provider == ProviderType.GITHUB:
        # Pattern: https://TOKEN@github.com/... or https://x-access-token:TOKEN@github.com/...
        # Replace with: https://TOKEN@github.com/...
        url = re.sub(
            r'https://[^@]+@github\.com',
            f'https://{new_token}@github.com',
            old_url,
        )
        return url
    elif provider == ProviderType.GITLAB:
        # Pattern: https://oauth2:TOKEN@gitlab.com/...
        url = re.sub(
            r'https://oauth2:[^@]+@gitlab\.com',
            f'https://oauth2:{new_token}@gitlab.com',
            old_url,
        )
        return url
    elif provider == ProviderType.BITBUCKET:
        # Pattern: https://x-token-auth:TOKEN@bitbucket.org/...
        url = re.sub(
            r'https://x-token-auth:[^@]+@bitbucket\.org',
            f'https://x-token-auth:{new_token}@bitbucket.org',
            old_url,
        )
        return url
    return old_url


async def update_git_remote_urls_with_new_tokens(
    provider_tokens: dict[ProviderType, Any],
) -> None:
    """Update all git remote URLs in workspace with fresh tokens.

    This ensures that when tokens are refreshed on resume, git operations
    (push, pull, fetch) will use the new valid tokens instead of expired ones.
    """
    workspace_root = os.getenv('WORKSPACE_MOUNT_PATH_IN_SANDBOX', '/workspace')

    if not os.path.exists(workspace_root):
        logger.debug(
            f'Workspace root {workspace_root} does not exist, skipping git URL update'
        )
        return

    # Find all git repos in the workspace
    for root, dirs, files in os.walk(workspace_root):
        if '.git' not in dirs:
            continue

        try:
            # Get current remote URL
            result = subprocess.run(
                ['git', '-C', root, 'remote', 'get-url', 'origin'],
                capture_output=True,
                text=True,
                check=True,
                timeout=5,
            )
            old_url = result.stdout.strip()

            if not old_url:
                continue

            # Determine which provider this repo uses
            provider = get_provider_from_url(old_url)

            if not provider or provider not in provider_tokens:
                continue

            # Get the token for this provider
            token_info = provider_tokens[provider]
            if (
                not token_info
                or not hasattr(token_info, 'token')
                or not token_info.token
            ):
                continue

            new_token = token_info.token.get_secret_value()

            # Build new URL with fresh token
            new_url = update_url_with_token(old_url, provider, new_token)

            if new_url != old_url:
                subprocess.run(
                    ['git', '-C', root, 'remote', 'set-url', 'origin', new_url],
                    check=True,
                    capture_output=True,
                    timeout=5,
                )
                logger.info(
                    f'Updated git remote URL in {root} for provider {provider.value}'
                )

        except subprocess.TimeoutExpired:
            logger.warning(f'Timeout while updating git URL in {root}')
            continue
        except subprocess.CalledProcessError as e:
            logger.debug(f'Failed to update git URL in {root}: {e}')
            continue
        except Exception as e:
            logger.warning(f'Unexpected error updating git URL in {root}: {e}')
            continue


# =================================================
# SECTION: Handle git provider tokens
# =================================================


async def invalidate_legacy_secrets_store(
    settings: Settings, settings_store: SettingsStore, secrets_store: SecretsStore
) -> UserSecrets | None:
    """We are moving `secrets_store` (a field from `Settings` object) to its own dedicated store
    This function moves the values from Settings to UserSecrets, and deletes the values in Settings
    While this function in called multiple times, the migration only ever happens once
    """
    if len(settings.secrets_store.provider_tokens.items()) > 0:
        user_secrets = UserSecrets(
            provider_tokens=settings.secrets_store.provider_tokens
        )
        await secrets_store.store(user_secrets)

        # Invalidate old tokens via settings store serializer
        invalidated_secrets_settings = settings.model_copy(
            update={'secrets_store': UserSecrets()}
        )
        await settings_store.store(invalidated_secrets_settings)

        return user_secrets

    return None


def process_token_validation_result(
    confirmed_token_type: ProviderType | None, token_type: ProviderType
) -> str:
    if not confirmed_token_type or confirmed_token_type != token_type:
        return (
            f'Invalid token. Please make sure it is a valid {token_type.value} token.'
        )

    return ''


async def check_provider_tokens(
    incoming_provider_tokens: POSTProviderModel,
    existing_provider_tokens: PROVIDER_TOKEN_TYPE | None,
) -> str:
    msg = ''
    if incoming_provider_tokens.provider_tokens:
        # Determine whether tokens are valid
        for token_type, token_value in incoming_provider_tokens.provider_tokens.items():
            if token_value.token:
                confirmed_token_type = await validate_provider_token(
                    token_value.token, token_value.host
                )  # FE always sends latest host
                msg = process_token_validation_result(confirmed_token_type, token_type)

            existing_token = (
                existing_provider_tokens.get(token_type, None)
                if existing_provider_tokens
                else None
            )
            if (
                existing_token
                and (existing_token.host != token_value.host)
                and existing_token.token
            ):
                confirmed_token_type = await validate_provider_token(
                    existing_token.token, token_value.host
                )  # Host has changed, check it against existing token
                if not confirmed_token_type or confirmed_token_type != token_type:
                    msg = process_token_validation_result(
                        confirmed_token_type, token_type
                    )

    return msg


@app.post('/add-git-providers')
async def store_provider_tokens(
    provider_info: POSTProviderModel,
    secrets_store: SecretsStore = Depends(get_secrets_store),
    provider_tokens: PROVIDER_TOKEN_TYPE | None = Depends(get_provider_tokens),
) -> JSONResponse:
    provider_err_msg = await check_provider_tokens(provider_info, provider_tokens)
    if provider_err_msg:
        # We don't have direct access to user_id here, but we can log the provider info
        logger.info(
            f'Returning 401 Unauthorized - Provider token error: {provider_err_msg}'
        )
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={'error': provider_err_msg},
        )

    try:
        user_secrets = await secrets_store.load()
        if not user_secrets:
            user_secrets = UserSecrets()

        if provider_info.provider_tokens:
            existing_providers = [provider for provider in user_secrets.provider_tokens]

            # Merge incoming settings store with the existing one
            for provider, token_value in list(provider_info.provider_tokens.items()):
                if provider in existing_providers and not token_value.token:
                    existing_token = user_secrets.provider_tokens.get(provider)
                    if existing_token and existing_token.token:
                        provider_info.provider_tokens[provider] = existing_token

                provider_info.provider_tokens[provider] = provider_info.provider_tokens[
                    provider
                ].model_copy(update={'host': token_value.host})

        updated_secrets = user_secrets.model_copy(
            update={'provider_tokens': provider_info.provider_tokens}
        )
        await secrets_store.store(updated_secrets)

        # Update git remote URLs with the new tokens to ensure git operations
        # (push, pull, fetch) use fresh tokens instead of expired ones
        if provider_info.provider_tokens:
            await update_git_remote_urls_with_new_tokens(provider_info.provider_tokens)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={'message': 'Git providers stored'},
        )
    except Exception as e:
        logger.warning(f'Something went wrong storing git providers: {e}')
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={'error': 'Something went wrong storing git providers'},
        )


@app.post('/unset-provider-tokens', response_model=dict[str, str])
async def unset_provider_tokens(
    secrets_store: SecretsStore = Depends(get_secrets_store),
) -> JSONResponse:
    try:
        user_secrets = await secrets_store.load()
        if user_secrets:
            updated_secrets = user_secrets.model_copy(update={'provider_tokens': {}})
            await secrets_store.store(updated_secrets)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={'message': 'Unset Git provider tokens'},
        )

    except Exception as e:
        logger.warning(f'Something went wrong unsetting tokens: {e}')
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={'error': 'Something went wrong unsetting tokens'},
        )


# =================================================
# SECTION: Handle custom secrets
# =================================================


@app.get('/secrets', response_model=GETCustomSecrets)
async def load_custom_secrets_names(
    user_secrets: UserSecrets | None = Depends(get_user_secrets),
) -> GETCustomSecrets | JSONResponse:
    try:
        if not user_secrets:
            return GETCustomSecrets(custom_secrets=[])

        custom_secrets: list[CustomSecretWithoutValueModel] = []
        if user_secrets.custom_secrets:
            for secret_name, secret_value in user_secrets.custom_secrets.items():
                custom_secret = CustomSecretWithoutValueModel(
                    name=secret_name,
                    description=secret_value.description,
                )
                custom_secrets.append(custom_secret)

        return GETCustomSecrets(custom_secrets=custom_secrets)

    except Exception as e:
        logger.warning(f'Failed to load secret names: {e}')
        logger.info('Returning 401 Unauthorized - Failed to get secret names')
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={'error': 'Failed to get secret names'},
        )


@app.post('/secrets', response_model=dict[str, str])
async def create_custom_secret(
    incoming_secret: CustomSecretModel,
    secrets_store: SecretsStore = Depends(get_secrets_store),
) -> JSONResponse:
    try:
        existing_secrets = await secrets_store.load()
        custom_secrets = (
            dict(existing_secrets.custom_secrets) if existing_secrets else {}
        )

        secret_name = incoming_secret.name
        secret_value = incoming_secret.value
        secret_description = incoming_secret.description

        if secret_name in custom_secrets:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={'message': f'Secret {secret_name} already exists'},
            )

        custom_secrets[secret_name] = CustomSecret(
            secret=secret_value,
            description=secret_description or '',
        )

        # Create a new UserSecrets that preserves provider tokens
        updated_user_secrets = UserSecrets(
            custom_secrets=custom_secrets,  # type: ignore[arg-type]
            provider_tokens=existing_secrets.provider_tokens
            if existing_secrets
            else {},  # type: ignore[arg-type]
        )

        await secrets_store.store(updated_user_secrets)

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={'message': 'Secret created successfully'},
        )
    except Exception as e:
        logger.warning(f'Something went wrong creating secret: {e}')
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={'error': 'Something went wrong creating secret'},
        )


@app.put('/secrets/{secret_id}', response_model=dict[str, str])
async def update_custom_secret(
    secret_id: str,
    incoming_secret: CustomSecretWithoutValueModel,
    secrets_store: SecretsStore = Depends(get_secrets_store),
) -> JSONResponse:
    try:
        existing_secrets = await secrets_store.load()
        if existing_secrets:
            # Check if the secret to update exists
            if secret_id not in existing_secrets.custom_secrets:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={'error': f'Secret with ID {secret_id} not found'},
                )

            secret_name = incoming_secret.name
            secret_description = incoming_secret.description

            custom_secrets = dict(existing_secrets.custom_secrets)
            existing_secret = custom_secrets.pop(secret_id)

            if secret_name != secret_id and secret_name in custom_secrets:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={'message': f'Secret {secret_name} already exists'},
                )

            custom_secrets[secret_name] = CustomSecret(
                secret=existing_secret.secret,
                description=secret_description or '',
            )

            updated_secrets = UserSecrets(
                custom_secrets=custom_secrets,  # type: ignore[arg-type]
                provider_tokens=existing_secrets.provider_tokens,
            )

            await secrets_store.store(updated_secrets)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={'message': 'Secret updated successfully'},
        )
    except Exception as e:
        logger.warning(f'Something went wrong updating secret: {e}')
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={'error': 'Something went wrong updating secret'},
        )


@app.delete('/secrets/{secret_id}')
async def delete_custom_secret(
    secret_id: str,
    secrets_store: SecretsStore = Depends(get_secrets_store),
) -> JSONResponse:
    try:
        existing_secrets = await secrets_store.load()
        if existing_secrets:
            # Get existing custom secrets
            custom_secrets = dict(existing_secrets.custom_secrets)

            # Check if the secret to delete exists
            if secret_id not in custom_secrets:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={'error': f'Secret with ID {secret_id} not found'},
                )

            # Remove the secret
            custom_secrets.pop(secret_id)

            # Create a new UserSecrets that preserves provider tokens and remaining secrets
            updated_secrets = UserSecrets(
                custom_secrets=custom_secrets,  # type: ignore[arg-type]
                provider_tokens=existing_secrets.provider_tokens,
            )

            await secrets_store.store(updated_secrets)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={'message': 'Secret deleted successfully'},
        )
    except Exception as e:
        logger.warning(f'Something went wrong deleting secret: {e}')
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={'error': 'Something went wrong deleting secret'},
        )
