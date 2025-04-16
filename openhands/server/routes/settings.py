from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from pydantic import SecretStr

from openhands.core.logger import openhands_logger as logger
from openhands.integrations.provider import ProviderToken, ProviderType, SecretStore
from openhands.integrations.utils import validate_provider_token
from openhands.server.auth import get_provider_tokens, get_user_id
from openhands.server.settings import GETSettingsModel, POSTSettingsModel, Settings
from openhands.server.shared import SettingsStoreImpl, config, server_config
from openhands.server.types import AppMode

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
            **settings.model_dump(exclude='secrets_store'),
            llm_api_key_set=settings.llm_api_key is not None,
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


@app.post('/unset-settings-tokens', response_model=dict[str, str])
async def unset_settings_tokens(request: Request) -> JSONResponse:
    try:
        settings_store = await SettingsStoreImpl.get_instance(
            config, get_user_id(request)
        )

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
async def reset_settings(request: Request) -> JSONResponse:
    """
    Resets user settings.
    """
    try:
        settings_store = await SettingsStoreImpl.get_instance(
            config, get_user_id(request)
        )

        existing_settings = await settings_store.load()
        settings = Settings(
            language='en',
            agent='CodeActAgent',
            security_analyzer='',
            confirmation_mode=False,
            llm_model='anthropic/claude-3-5-sonnet-20241022',
            llm_api_key='',
            llm_base_url='',
            remote_runtime_resource_factor=1,
            enable_default_condenser=True,
            enable_sound_notifications=False,
            user_consents_to_analytics=existing_settings.user_consents_to_analytics
            if existing_settings
            else False,
        )

        server_config_values = server_config.get_config()
        is_hide_llm_settings_enabled = server_config_values.get(
            'FEATURE_FLAGS', {}
        ).get('HIDE_LLM_SETTINGS', False)
        # We don't want the user to be able to modify these settings in SaaS
        if server_config.app_mode == AppMode.SAAS and is_hide_llm_settings_enabled:
            if existing_settings:
                settings.llm_api_key = existing_settings.llm_api_key
                settings.llm_base_url = existing_settings.llm_base_url
                settings.llm_model = existing_settings.llm_model

        await settings_store.store(settings)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={'message': 'Settings stored'},
        )

    except Exception as e:
        logger.warning(f'Something went wrong resetting settings: {e}')
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={'error': 'Something went wrong resetting settings'},
        )



async def check_provider_tokens(request: Request,
                                settings: POSTSettingsModel) -> str:
    
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
                    return f"Invalid token. Please make sure it is a valid {token_type} token."
                    

    return ""



async def store_provider_tokens(request: Request, settings: POSTSettingsModel):
    settings_store = await SettingsStoreImpl.get_instance(
            config, get_user_id(request)
        )
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
                provider.value: data.token.get_secret_value()
                if data.token
                else None
                for provider, data in provider_tokens.items()
            }

    return settings


async def store_llm_settings(request: Request, settings: POSTSettingsModel) -> POSTSettingsModel:
    settings_store = await SettingsStoreImpl.get_instance(
            config, get_user_id(request)
        )
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
    request: Request,
    settings: POSTSettingsModel,
) -> JSONResponse:
    # Check provider tokens are valid
    provider_err_msg = await check_provider_tokens(request, settings)
    if provider_err_msg:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                'error': provider_err_msg
            },
        )
    

    try:
        settings_store = await SettingsStoreImpl.get_instance(
            config, get_user_id(request)
        )
        existing_settings = await settings_store.load()

        # Convert to Settings model and merge with existing settings
        if existing_settings:
            settings = await store_llm_settings(request, settings)

            # Keep existing analytics consent if not provided
            if settings.user_consents_to_analytics is None:
                settings.user_consents_to_analytics = (
                    existing_settings.user_consents_to_analytics
                )

            settings = await store_provider_tokens(request, settings)
           

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
