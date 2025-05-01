from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import SecretStr

from openhands.integrations.service_types import ProviderType
from openhands.integrations.utils import validate_provider_token
from openhands.server.settings import POSTProviderModel, POSTSettingsCustomSecrets
from openhands.server.user_auth import get_user_settings_store
from openhands.storage.data_models.settings import Settings
from openhands.storage.settings.settings_store import SettingsStore


app = APIRouter(prefix='/api')


def load_legacy_secrets(settings_store: SettingsStore, settings: Settings):
    provider_tokens = settings.secrets_store.provider_tokens
    if len(provider_tokens.items()):
        # Invalidate old tokens via settings store serializer
        settings_store.store(settings)

    return provider_tokens



async def check_provider_tokens(settings: POSTProviderModel) -> str:
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
    settings: POSTProviderModel, settings_store: SettingsStore
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