from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from pydantic import SecretStr

from openhands.core.logger import openhands_logger as logger
from openhands.integrations.provider import ProviderToken, ProviderType
from openhands.integrations.utils import determine_token_type
from openhands.server.auth import get_user_id, get_provider_tokens
from openhands.server.settings import GETSettingsModel, POSTSettingsModel, Settings
from openhands.server.shared import SettingsStoreImpl, config


app = APIRouter(prefix='/api')


@app.get('/settings', response_model=GETSettingsModel)
async def load_settings(request: Request) -> GETSettingsModel | JSONResponse:
    try:
        user_id = get_user_id(request)
        settings_store = await SettingsStoreImpl.get_instance(config, user_id)
        settings = await settings_store.load()
        if not settings:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={'error': 'Settings not found'},
            )

        provider_tokens_set = {}
        
        if bool(user_id):
            provider_tokens_set[ProviderType.GITHUB.value] = True
        
        provider_tokens = get_provider_tokens(request)
        if provider_tokens:
            all_provider_types = [provider.value for provider in ProviderType]
            provider_tokens_types = [provider.value for provider in provider_tokens]
            for provider_type in all_provider_types:
                if provider_type in provider_tokens_types:
                    provider_tokens_set[provider_type] = True
                else:
                    provider_tokens_set[provider_type] = False

        settings_with_token_data = GETSettingsModel(
            **settings.model_dump(),
            provider_tokens_set=provider_tokens_set,
        )
        settings_with_token_data.llm_api_key = settings.llm_api_key

        del settings_with_token_data.secrets_store
        return settings_with_token_data
    except Exception as e:
        logger.warning(f'Invalid token: {e}')
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={'error': 'Invalid token'},
        )


@app.post('/settings', response_model=dict[str, str])
async def store_settings(
    request: Request,
    settings: POSTSettingsModel,
) -> JSONResponse:
    # Check provider tokens are valid
    if settings.provider_tokens:
        # Remove extraneous token types
        provider_types = [provider.value for provider in ProviderType]
        settings.provider_tokens = {
            k: v for k, v in settings.provider_tokens.items() if k in provider_types
        }

        # Determine whether tokens are valid
        for token_type, token_value in settings.provider_tokens.items():
            if token_value:
                confirmed_token_type = await determine_token_type(
                    SecretStr(token_value)
                )
                if not confirmed_token_type or confirmed_token_type.value != token_type:
                    return JSONResponse(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        content={
                            'error': f'Invalid token. Please make sure it is a valid {token_type} token.'
                        },
                    )

    try:
        settings_store = await SettingsStoreImpl.get_instance(
            config, get_user_id(request)
        )
        existing_settings = await settings_store.load()

        # Convert to Settings model and merge with existing settings
        if existing_settings:
            # Keep existing LLM key if not provided
            if settings.llm_api_key is None:
                settings.llm_api_key = existing_settings.llm_api_key

            # Keep existing analytics consent if not provided
            if settings.user_consents_to_analytics is None:
                settings.user_consents_to_analytics = (
                    existing_settings.user_consents_to_analytics
                )

            if existing_settings.secrets_store:
                existing_providers = [provider.value for provider in existing_settings.secrets_store.provider_tokens]

                # Merge incoming settings store with the existing one
                for (
                    provider,
                    provider_token
                ) in settings.provider_tokens.items():
                    if provider in existing_providers and not provider_token:
                        settings.provider_tokens[provider] = existing_settings.secrets_store.provider_tokens[ProviderType(provider)].token.get_secret_value()

            # Merge provider tokens with existing ones
            if settings.unset_tokens:  # Only merge if not unsetting tokens
                settings.secrets_store.provider_tokens = {}
                settings.provider_tokens = {}

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

    # Create a new Settings instance without provider tokens
    settings = Settings(**filtered_settings_data)

    # Update provider tokens if any are provided
    if settings_with_token_data.provider_tokens:
        for token_type, token_value in settings_with_token_data.provider_tokens.items():
            if token_value:
                provider = ProviderType(token_type)
                settings.secrets_store.provider_tokens[provider] = ProviderToken(
                    token=SecretStr(token_value), user_id=None
                )

    return settings
