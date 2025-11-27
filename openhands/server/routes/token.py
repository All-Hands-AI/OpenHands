import uuid
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError

from openhands.core.logger import openhands_logger as logger
from openhands.server.dependencies import get_dependencies
from openhands.server.user_auth import get_user_settings_store
from openhands.server.shared import server_config
from openhands.server.services.lumio_service import LumioService
from openhands.storage.data_models.settings import AuthWallet, Settings
from openhands.storage.settings.settings_store import SettingsStore

app = APIRouter(prefix='/api/token', dependencies=get_dependencies())


def get_lumio_service() -> LumioService:
    """Get configured LumioService instance."""
    return LumioService(
        rpc_url=server_config.lumio_rpc_url,
        contract_address=server_config.vibe_balance_contract,
    )


class SignToken(BaseModel):
    address: str | None = None
    application: str | None = None
    chainId: int | None = None
    fullMessage: str | None = None
    nonce: str | None = None
    prefix: str | None = None
    message: str | None = None
    signature: list[int] | None = None


def verify_ed25519_signature(
    message: str,
    signature: list[int],
    public_key_hex: str,
) -> bool:
    """Verify ed25519 signature from Pontem wallet.

    Args:
        message: The full message that was signed
        signature: The signature as list of bytes
        public_key_hex: The public key in hex format (with or without 0x prefix)

    Returns:
        True if signature is valid, False otherwise
    """
    try:
        # Convert signature list to bytes
        signature_bytes = bytes(signature)

        # Remove 0x prefix if present and convert to bytes
        if public_key_hex.startswith('0x'):
            public_key_hex = public_key_hex[2:]
        public_key_bytes = bytes.fromhex(public_key_hex)

        # Create verify key and verify
        verify_key = VerifyKey(public_key_bytes)
        verify_key.verify(message.encode('utf-8'), signature_bytes)
        return True
    except BadSignatureError:
        logger.warning('Invalid signature')
        return False
    except Exception as e:
        logger.error(f'Error verifying signature: {e}')
        return False


@app.post('/new')
async def new_token(
    token: AuthWallet,
    user_settings_store: SettingsStore = Depends(get_user_settings_store),
) -> AuthWallet:
    """Create a new authentication token for wallet."""
    user_setting: Settings | None = await user_settings_store.load()
    if user_setting is None:
        raise HTTPException(status_code=500, detail='Settings not found')

    if not token.account:
        raise HTTPException(status_code=400, detail='Account address is required')

    # Check whitelist
    lumio_service = get_lumio_service()
    is_whitelisted = await lumio_service.is_whitelisted(token.account)
    if not is_whitelisted:
        raise HTTPException(status_code=403, detail='Account is not whitelisted')

    user_setting.wallet = AuthWallet()
    user_setting.wallet.account = token.account
    user_setting.wallet.token = str(uuid.uuid4())
    await user_settings_store.store(user_setting)

    return user_setting.wallet


@app.post('/verify')
async def verify_token(
    sign_token: SignToken,
    user_settings_store: SettingsStore = Depends(get_user_settings_store),
) -> AuthWallet:
    """Verify the signed token from wallet."""
    if sign_token.message is None:
        raise HTTPException(status_code=400, detail='Message is required')

    if sign_token.signature is None:
        raise HTTPException(status_code=400, detail='Signature is required')

    if sign_token.address is None:
        raise HTTPException(status_code=400, detail='Address is required')

    input_token = AuthWallet.model_validate_json(sign_token.message)
    user_setting: Settings | None = await user_settings_store.load()
    if user_setting is None:
        raise HTTPException(status_code=500, detail='Settings not found')

    # Verify token matches stored token
    if user_setting.wallet.token is None or user_setting.wallet != input_token:
        input_token.verified_token = False
        return input_token

    # Verify signature
    full_message = sign_token.fullMessage or sign_token.message
    if not verify_ed25519_signature(
        message=full_message,
        signature=sign_token.signature,
        public_key_hex=sign_token.address,
    ):
        logger.warning(f'Signature verification failed for address: {sign_token.address}')
        input_token.verified_token = False
        return input_token

    user_setting.wallet.verified_token = True
    await user_settings_store.store(user_setting)

    return user_setting.wallet


@app.post('/status')
async def status_token(
    input_token: AuthWallet,
    user_settings_store: SettingsStore = Depends(get_user_settings_store),
) -> AuthWallet:
    """Check the status of an authentication token."""
    user_setting: Settings | None = await user_settings_store.load()
    if user_setting is None:
        raise HTTPException(status_code=500, detail='Settings not found')

    if user_setting.wallet != input_token:
        input_token.verified_token = False
        return input_token

    return user_setting.wallet


@app.delete('')
async def delete_token(
    user_settings_store: SettingsStore = Depends(get_user_settings_store),
) -> bool:
    """Delete the current authentication token."""
    user_setting: Settings | None = await user_settings_store.load()

    if user_setting is None:
        raise HTTPException(status_code=500, detail='Settings not found')

    user_setting.wallet = AuthWallet()
    await user_settings_store.store(user_setting)

    return True
