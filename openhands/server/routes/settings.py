from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from pydantic import SecretStr

from openhands.core.logger import openhands_logger as logger
from openhands.integrations.provider import ProviderType
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

        token_is_set = bool(user_id) or bool(get_provider_tokens)
        settings_with_token_data = GETSettingsModel(
            **settings.model_dump(),
            token_is_set=token_is_set,
        )
        settings_with_token_data.llm_api_key = settings.llm_api_key

        del settings_with_token_data.provider_tokens
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
        for token_type in settings.provider_tokens:
            if token_type not in provider_types:
                del settings.provider_tokens[token_type]

        # Determine whether tokens are valid
        for token_type, token_value in settings.provider_tokens.items():
            confirmed_token_type = await determine_token_type(SecretStr(token_value))
            if confirmed_token_type != token_type:
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

        if existing_settings:
            # LLM key isn't on the frontend, so we need to keep it if unset
            if settings.llm_api_key is None:
                settings.llm_api_key = existing_settings.llm_api_key

            # Updating any existing provider tokens with new ones
            if settings.provider_tokens:
                existing_settings.provider_tokens.update(settings.provider_tokens)

            settings.provider_tokens = existing_settings.provider_tokens


            if settings.user_consents_to_analytics is None:
                settings.user_consents_to_analytics = (
                    existing_settings.user_consents_to_analytics
                )

        response = JSONResponse(
            status_code=status.HTTP_200_OK,
            content={'message': 'Settings stored'},
        )

        if settings.unset_token:
            settings.provider_tokens = {}

        # Update sandbox config with new settings
        if settings.remote_runtime_resource_factor is not None:
            config.sandbox.remote_runtime_resource_factor = (
                settings.remote_runtime_resource_factor
            )

        settings = convert_to_settings(settings)

        await settings_store.store(settings)
        return response
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

    # Convert the `llm_api_key` and `github_token` to a `SecretStr` instance
    filtered_settings_data['llm_api_key'] = settings_with_token_data.llm_api_key
    filtered_settings_data['provider_tokens'] = settings_with_token_data.provider_tokens

    return Settings(**filtered_settings_data)
