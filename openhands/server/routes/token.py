import uuid
from fastapi import APIRouter, Depends
from groq import BaseModel
from openhands.server.dependencies import get_dependencies
from openhands.server.user_auth import get_user_settings_store
from openhands.storage.data_models.settings import AuthWallet, Settings
from openhands.storage.settings.settings_store import SettingsStore

app = APIRouter(prefix='/api/token', dependencies=get_dependencies())

class SignToken(BaseModel):
    address: str | None = None
    application:str | None = None
    chainId: int | None = None
    fullMessage: str | None = None
    nonce: str | None = None
    prefix: str | None = None
    message: str | None = None
    signature: list[int] | None = None


# new token
@app.post('/new')
async def new_token(
    token: AuthWallet,
    user_settings_store: SettingsStore = Depends(get_user_settings_store),
) -> AuthWallet:
    user_setting: Settings | None = await user_settings_store.load()
    if user_setting is None:
        # placeholder for error handling
        raise ValueError('Settings not found')

    user_setting.wallet=AuthWallet()
    user_setting.wallet.account=token.account # account address
    user_setting.wallet.token = str(uuid.uuid4()) # new token
    await user_settings_store.store(user_setting) # save

    return user_setting.wallet

# verify token
@app.post('/verify')
async def verify_token(
    sign_token: SignToken,
    user_settings_store: SettingsStore = Depends(get_user_settings_store)
) -> AuthWallet:
    if sign_token.message is None:
        raise ValueError('Incorrect SignToken')

    input_token = AuthWallet.model_validate_json(sign_token.message)
    user_setting: Settings | None = await user_settings_store.load()
    if user_setting is None:
        # placeholder for error handling
        raise ValueError('Settings not found')

    if (sign_token.signature is None) or (user_setting.wallet.token is None) or (user_setting.wallet!=input_token):
        input_token.verified_token=False
        return input_token

    # @todo check signature

    user_setting.wallet.verified_token=True
    await user_settings_store.store(user_setting) # save

    return user_setting.wallet

# check status
@app.post('/status')
async def status_token(
    input_token: AuthWallet,
    user_settings_store: SettingsStore = Depends(get_user_settings_store)
) -> AuthWallet:
    user_setting: Settings | None = await user_settings_store.load()
    if user_setting is None:
        # placeholder for error handling
        raise ValueError('Settings not found')

    if (user_setting.wallet!=input_token):
        input_token.verified_token=False
        return input_token

    return user_setting.wallet


# delete token
@app.delete('/token')
async def delete_token(user_settings_store: SettingsStore = Depends(get_user_settings_store))->bool:
    user_setting: Settings | None = await user_settings_store.load()

    if user_setting is None:
        # placeholder for error handling
        raise ValueError('Settings not found')

    user_setting.wallet = AuthWallet()
    await user_settings_store.store(user_setting) # save

    return True





