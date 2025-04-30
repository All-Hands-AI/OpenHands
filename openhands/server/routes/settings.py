from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from pydantic import SecretStr

from openhands.core.logger import openhands_logger as logger
from openhands.integrations.provider import (
    PROVIDER_TOKEN_TYPE,
    ProviderToken,
    ProviderType,
    SecretStore,
)
from openhands.integrations.utils import validate_provider_token
from openhands.server.settings import (
    GETSettingsCustomSecrets,
    GETSettingsModel,
    POSTSettingsCustomSecrets,
    POSTSettingsModel,
)
from openhands.server.shared import config
from openhands.storage.data_models.settings import Settings
from openhands.server.user_auth import (
    get_provider_tokens,
    get_user_id,
    get_user_settings,
    get_user_settings_store,
)
from openhands.storage.settings.settings_store import SettingsStore

app = APIRouter(prefix='/api')


@app.get('/settings', response_model=GETSettingsModel)
async def load_settings(
    user_id: str | None = Depends(get_user_id),
    provider_tokens: PROVIDER_TOKEN_TYPE | None = Depends(get_provider_tokens),
    settings: Settings | None = Depends(get_user_settings),
) -> GETSettingsModel | JSONResponse:
    try:
        if not settings:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={'error': 'Settings not found'},
            )

        provider_tokens_set = {}

        if bool(user_id):
            provider_tokens_set[ProviderType.GITHUB.value] = True

        if provider_tokens:
            all_provider_types = [provider.value for provider in ProviderType]
            provider_tokens_types = [provider.value for provider in provider_tokens]
            for provider_type in all_provider_types:
                if provider_type in provider_tokens_types:
                    provider_tokens_set[provider_type] = True
                else:
                    provider_tokens_set[provider_type] = False

        settings_with_token_data = GETSettingsModel(
            **settings.model_dump(exclude='secrets_store'),
            llm_api_key_set=settings.llm_api_key is not None
            and bool(settings.llm_api_key),
            provider_tokens_set=provider_tokens_set,
        )
        settings_with_token_data.llm_api_key = None
        return settings_with_token_data
    except Exception as e:
        logger.warning(f'Invalid token: {e}')
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={'error': 'Invalid token'},
        )


@app.get('/secrets', response_model=GETSettingsCustomSecrets)
async def load_custom_secrets_names(
    settings: Settings | None = Depends(get_user_settings),
) -> GETSettingsCustomSecrets | JSONResponse:
    try:
        if not settings:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={'error': 'Settings not found'},
            )

        custom_secrets = []
        if settings.secrets_store.custom_secrets:
            for secret_name, _ in settings.secrets_store.custom_secrets.items():
                custom_secrets.append(secret_name)

        secret_names = GETSettingsCustomSecrets(custom_secrets=custom_secrets)
        return secret_names

    except Exception as e:
        logger.warning(f'Invalid token: {e}')
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={'error': 'Invalid token'},
        )


@app.post('/secrets', response_model=dict[str, str])
async def add_custom_secret(
    incoming_secrets: POSTSettingsCustomSecrets,
    settings_store: SettingsStore = Depends(get_user_settings_store),
) -> JSONResponse:
    try:
        existing_settings = await settings_store.load()
        if existing_settings:
            for (
                secret_name,
                secret_value,
            ) in existing_settings.secrets_store.custom_secrets.items():
                if (
                    secret_name not in incoming_secrets.custom_secrets
                ):  # Allow incoming values to override existing ones
                    incoming_secrets.custom_secrets[secret_name] = secret_value

            # Create a new SecretStore that preserves provider tokens
            updated_secret_store = SecretStore(
                custom_secrets=incoming_secrets.custom_secrets,
                provider_tokens=existing_settings.secrets_store.provider_tokens,
            )

            # Only update SecretStore in Settings
            updated_settings = existing_settings.model_copy(
                update={'secrets_store': updated_secret_store}
            )

            await settings_store.store(updated_settings)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={'message': 'Settings stored'},
        )
    except Exception as e:
        logger.warning(f'Something went wrong storing settings: {e}')
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={'error': 'Something went wrong storing settings'},
        )


@app.delete('/secrets/{secret_id}')
async def delete_custom_secret(
    secret_id: str,
    settings_store: SettingsStore = Depends(get_user_settings_store),
) -> JSONResponse:
    try:
        existing_settings: Settings | None = await settings_store.load()
        custom_secrets = {}
        if existing_settings:
            for (
                secret_name,
                secret_value,
            ) in existing_settings.secrets_store.custom_secrets.items():
                if secret_name != secret_id:
                    custom_secrets[secret_name] = secret_value

            # Create a new SecretStore that preserves provider tokens
            updated_secret_store = SecretStore(
                custom_secrets=custom_secrets,
                provider_tokens=existing_settings.secrets_store.provider_tokens,
            )

            updated_settings = existing_settings.model_copy(
                update={'secrets_store': updated_secret_store}
            )

            await settings_store.store(updated_settings)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={'message': 'Settings stored'},
        )
    except Exception as e:
        logger.warning(f'Something went wrong storing settings: {e}')
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={'error': 'Something went wrong storing settings'},
        )


@app.post('/unset-settings-tokens', response_model=dict[str, str])
async def unset_settings_tokens(
    settings_store: SettingsStore = Depends(get_user_settings_store),
) -> JSONResponse:
    try:
        existing_settings = await settings_store.load()
        if existing_settings:
            settings = existing_settings.model_copy(
                update={'secrets_store': SecretStore()}
            )
            await settings_store.store(settings)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={'message': 'Settings stored'},
        )

    except Exception as e:
        logger.warning(f'Something went wrong unsetting tokens: {e}')
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={'error': 'Something went wrong unsetting tokens'},
        )


@app.post('/reset-settings', response_model=dict[str, str])
async def reset_settings() -> JSONResponse:
    """
    Resets user settings. (Deprecated)
    """
    logger.warning('Deprecated endpoint /api/reset-settings called by user')
    return JSONResponse(
        status_code=status.HTTP_410_GONE,
        content={'error': 'Reset settings functionality has been removed.'},
    )


async def check_provider_tokens(settings: POSTSettingsModel) -> str:
    if settings.provider_tokens:
        # Remove extraneous token types
        provider_types = [provider.value for provider in ProviderType]
        settings.provider_tokens = {
            k: v for k, v in settings.provider_tokens.items() if k in provider_types
        }

        # Determine whether tokens are valid
        for token_type, token_value in settings.provider_tokens.items():
            if token_value:
                confirmed_token_type = await validate_provider_token(
                    SecretStr(token_value)
                )
                if not confirmed_token_type or confirmed_token_type.value != token_type:
                    return f'Invalid token. Please make sure it is a valid {token_type} token.'

    return ''


async def store_provider_tokens(
    settings: POSTSettingsModel, settings_store: SettingsStore
):
    existing_settings = await settings_store.load()
    if existing_settings:
        if settings.provider_tokens:
            if existing_settings.secrets_store:
                existing_providers = [
                    provider.value
                    for provider in existing_settings.secrets_store.provider_tokens
                ]

                # Merge incoming settings store with the existing one
                for provider, token_value in list(settings.provider_tokens.items()):
                    if provider in existing_providers and not token_value:
                        provider_type = ProviderType(provider)
                        existing_token = (
                            existing_settings.secrets_store.provider_tokens.get(
                                provider_type
                            )
                        )
                        if existing_token and existing_token.token:
                            settings.provider_tokens[provider] = (
                                existing_token.token.get_secret_value()
                            )
        else:  # nothing passed in means keep current settings
            provider_tokens = existing_settings.secrets_store.provider_tokens
            settings.provider_tokens = {
                provider.value: data.token.get_secret_value() if data.token else None
                for provider, data in provider_tokens.items()
            }

    return settings


async def store_llm_settings(
    settings: POSTSettingsModel, settings_store: SettingsStore
) -> POSTSettingsModel:
    existing_settings = await settings_store.load()

    # Convert to Settings model and merge with existing settings
    if existing_settings:
        # Keep existing LLM settings if not provided
        if settings.llm_api_key is None:
            settings.llm_api_key = existing_settings.llm_api_key
        if settings.llm_model is None:
            settings.llm_model = existing_settings.llm_model
        if settings.llm_base_url is None:
            settings.llm_base_url = existing_settings.llm_base_url

    return settings


@app.post('/settings', response_model=dict[str, str])
async def store_settings(
    settings: POSTSettingsModel,
    settings_store: SettingsStore = Depends(get_user_settings_store),
) -> JSONResponse:
    # Check provider tokens are valid
    provider_err_msg = await check_provider_tokens(settings)
    if provider_err_msg:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={'error': provider_err_msg},
        )

    try:
        existing_settings = await settings_store.load()

        # Convert to Settings model and merge with existing settings
        if existing_settings:
            settings = await store_llm_settings(settings, settings_store)

            # Keep existing analytics consent if not provided
            if settings.user_consents_to_analytics is None:
                settings.user_consents_to_analytics = (
                    existing_settings.user_consents_to_analytics
                )

            settings = await store_provider_tokens(settings, settings_store)

        # Update sandbox config with new settings
        if settings.remote_runtime_resource_factor is not None:
            config.sandbox.remote_runtime_resource_factor = (
                settings.remote_runtime_resource_factor
            )

        settings = convert_to_settings(settings)
        await settings_store.store(settings)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={'message': 'Settings stored'},
        )
    except Exception as e:
        logger.warning(f'Something went wrong storing settings: {e}')
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={'error': 'Something went wrong storing settings'},
        )


def convert_to_settings(settings_with_token_data: POSTSettingsModel) -> Settings:
    settings_data = settings_with_token_data.model_dump()

    # Filter out additional fields from `SettingsWithTokenData`
    filtered_settings_data = {
        key: value
        for key, value in settings_data.items()
        if key in Settings.model_fields  # Ensures only `Settings` fields are included
    }

    # Convert the `llm_api_key` to a `SecretStr` instance
    filtered_settings_data['llm_api_key'] = settings_with_token_data.llm_api_key

    # Create a new Settings instance with empty SecretStore
    settings = Settings(**filtered_settings_data)

    # Create new provider tokens immutably
    if settings_with_token_data.provider_tokens:
        tokens = {}
        for token_type, token_value in settings_with_token_data.provider_tokens.items():
            if token_value:
                provider = ProviderType(token_type)
                tokens[provider] = ProviderToken(
                    token=SecretStr(token_value), user_id=None
                )

        # Create new SecretStore with tokens
        settings = settings.model_copy(
            update={'secrets_store': SecretStore(provider_tokens=tokens)}
        )

    return settings
