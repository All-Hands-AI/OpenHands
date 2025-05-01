from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from pydantic import SecretStr

from openhands.integrations.service_types import ProviderType
from openhands.integrations.utils import validate_provider_token
from openhands.server.settings import GETCustomSecrets, POSTCustomSecrets, POSTProviderModel
from openhands.server.user_auth import get_secrets_store, get_user_secrets, get_user_settings_store
from openhands.storage.data_models.settings import Settings
from openhands.storage.data_models.user_secrets import UserSecrets
from openhands.storage.settings.secret_store import SecretsStore
from openhands.storage.settings.settings_store import SettingsStore
from openhands.core.logger import openhands_logger as logger

app = APIRouter(prefix='/api')




# =================================================
# SECTION: Handle git provider tokens
# =================================================


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
    secrets_store: SecretsStore = Depends(get_secrets_store)
):
    user_secrets = await secrets_store.load()

    if user_secrets:
        if provider_info.provider_tokens:
            existing_providers = [
                provider
                for provider in user_secrets.provider_tokens
            ]

            # Merge incoming settings store with the existing one
            for provider, token_value in list(user_secrets.provider_tokens.items()):
                if provider in existing_providers and not token_value:
                    provider_type = ProviderType(provider)
                    existing_token = (
                        user_secrets.provider_tokens.get(
                            provider_type
                        )
                    )
                    if existing_token and existing_token.token:
                        user_secrets.provider_tokens[provider] = (
                            existing_token.token.get_secret_value()
                        )
        else:  # nothing passed in means keep current settings
            pass
        


@app.post('/unset-provider-tokens', response_model=dict[str, str])
async def unset_provider_tokens(
    secrets_store: SecretsStore = Depends(get_secrets_store)
) -> JSONResponse:
    try:
        user_secrets = await secrets_store.load()
        if user_secrets:
            user_secrets = user_secrets.model_copy(
                update={'provider_tokens': {}}
            )
            await secrets_store.store(user_secrets)

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
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={'error': 'User secrets not found'},
            )

        custom_secrets = []
        if user_secrets.custom_secrets:
            for secret_name, secret_value in user_secrets.custom_secrets.items():
                custom_secrets.append(secret_name)

        secret_names = GETCustomSecrets(custom_secrets=custom_secrets)
        return secret_names

    except Exception as e:
        logger.warning(f'Invalid token: {e}')
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={'error': 'Invalid token'},
        )


@app.post('/secrets', response_model=dict[str, str])
async def create_custom_secret(
    incoming_secret: POSTCustomSecrets,
    secrets_store: SecretsStore = Depends(get_secrets_store),
) -> JSONResponse:
    try:
        existing_secrets = await secrets_store.load()
        if existing_secrets:
            custom_secrets = dict(existing_secrets.custom_secrets)

            for secret_name, secret_value in incoming_secret.custom_secrets.items():
                if secret_name in custom_secrets:
                    return JSONResponse(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        content={'message': f'Secret {secret_name} already exists'},
                    )
            
                custom_secrets[secret_name] = secret_value
        
            # Create a new SecretStore that preserves provider tokens
            updated_user_secrets = UserSecrets(
                custom_secrets=custom_secrets,
                provider_tokens=existing_secrets.provider_tokens,
            )

            await secrets_store.store(updated_user_secrets)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
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
    incoming_secret: POSTCustomSecrets, 
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

            custom_secrets = dict(existing_secrets.custom_secrets)
            custom_secrets.pop(secret_id)

            for secret_name, secret_value in incoming_secret.custom_secrets.items():
                custom_secrets[secret_name] = secret_value

            # Create a new SecretStore that preserves provider tokens
            updated_secrets = UserSecrets(
                custom_secrets=custom_secrets,
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

            # Create a new SecretStore that preserves provider tokens
            updated_secrets = UserSecrets(
                custom_secrets=custom_secrets,
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

