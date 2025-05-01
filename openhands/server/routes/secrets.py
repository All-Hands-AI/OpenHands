from fastapi import APIRouter, Depends
from pydantic import SecretStr

from openhands.integrations.service_types import ProviderType
from openhands.integrations.utils import validate_provider_token
from openhands.server.settings import POSTProviderModel
from openhands.server.user_auth import get_user_secret_store
from openhands.storage.data_models.settings import Settings
from openhands.storage.data_models.user_secrets import UserSecrets
from openhands.storage.settings.secret_store import SecretsStore
from openhands.storage.settings.settings_store import SettingsStore


app = APIRouter(prefix='/api')


async def invalidate_legacy_secrets_store(
    settings_store: SettingsStore, 
    settings: Settings | None,
    secrets_store: SecretsStore):

    if settings and len(settings.secrets_store.provider_tokens.items()) > 0:
        user_secrets = UserSecrets(provider_tokens=settings.secrets_store.provider_tokens)
        await secrets_store.store(user_secrets)

        # Invalidate old tokens via settings store serializer
        await settings_store.store(settings)



async def check_provider_tokens(provider_info: POSTProviderModel) -> str:
    if provider_info.provider_tokens:
        # Determine whether tokens are valid
        for token_type, token_value in provider_info.provider_tokens.items():
            if token_value:
                confirmed_token_type = await validate_provider_token(
                    SecretStr(token_value)
                )
                if not confirmed_token_type or confirmed_token_type != token_type:
                    return f'Invalid token. Please make sure it is a valid {token_type.value} token.'

    return ''


@app.post('/set_tokens', response_model=dict[str, str])
async def store_provider_tokens(
    provider_info: POSTProviderModel, 
    settings_store: SettingsStore,
    existing_user_secrets: UserSecrets = Depends(get_user_secret_store)
):
    existing_settings = await settings_store.load()



    if existing_user_secrets:
        if provider_info.provider_tokens:
            if existing_settings.secrets_store:
                existing_providers = [
                    provider.value
                    for provider in existing_settings.secrets_store.provider_tokens
                ]

                # Merge incoming settings store with the existing one
                for provider, token_value in list(existing_user_secrets.provider_tokens.items()):
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
            existing_user_secrets.provider_tokens = {
                provider.value: data.token.get_secret_value() if data.token else None
                for provider, data in provider_tokens.items()
            }

    return settings