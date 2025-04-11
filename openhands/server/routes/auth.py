import hashlib
import hmac
import os
from datetime import datetime

# timedelta
import jwt
from eth_account.messages import encode_defunct
from fastapi import APIRouter, HTTPException, Request
from hdwallet import BIP44HDWallet
from hdwallet.cryptocurrencies import EthereumMainnet
from mnemonic import Mnemonic
from pydantic import BaseModel
from solders.keypair import Keypair
from sqlalchemy import select
from web3 import Web3

from openhands.server.auth import get_user_id
from openhands.server.db import database
from openhands.server.models import User
from openhands.server.utils.crypto import generate_mnemonic

app = APIRouter(prefix='/api/auth')


# TODO: implement get nonce for signing message later
# Message that users will sign with their wallet
AUTH_MESSAGE = 'Sign to confirm account access to Thesis'

# JWT settings
JWT_SECRET = os.getenv('JWT_SECRET')

JWT_ALGORITHM = 'HS256'
JWT_EXPIRES_IN = None  # Token never expires


class SignupRequest(BaseModel):
    publicAddress: str
    signature: str


class SignupResponse(BaseModel):
    token: str
    user: dict


def create_jwt_token(user_id: str) -> str:
    """Create a JWT token for the user."""
    payload = {
        'sub': user_id,
        'iat': datetime.utcnow(),
    }

    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_ethereum_signature(public_address: str, signature: str) -> bool:
    """Verify that the signature was signed by the public address."""
    try:
        w3 = Web3()
        message = encode_defunct(text=AUTH_MESSAGE)
        recovered_address = w3.eth.account.recover_message(message, signature=signature)
        return recovered_address.lower() == public_address.lower()
    except Exception:
        return False


@app.post('/signup', response_model=SignupResponse)
async def signup(request: SignupRequest) -> SignupResponse:
    """Sign up with Ethereum wallet."""
    # Verify the signature
    if not verify_ethereum_signature(request.publicAddress, request.signature):
        raise HTTPException(status_code=400, detail='Invalid signature')

    # Check if user already exists
    query = select(User).where(User.c.public_key == request.publicAddress.lower())
    existing_user = await database.fetch_one(query)
    if existing_user:
        # If user exists, just return current token
        return SignupResponse(
            token=existing_user['jwt'],
            user={
                'id': existing_user['public_key'],
                'publicAddress': existing_user['public_key'],
            },
        )

    user_data = {
        'public_key': request.publicAddress.lower(),
        'mnemonic': generate_mnemonic(),
        'jwt': create_jwt_token(request.publicAddress.lower()),
    }

    await database.execute(User.insert().values(user_data))

    return SignupResponse(
        token=user_data['jwt'],
        user={'id': user_data['public_key'], 'publicAddress': user_data['public_key']},
    )


@app.get('/address-by-network/{network_id}')
async def get_address_by_network(network_id: str, request: Request) -> str:
    """Generate wallet address for the given network from user's mnemonic."""
    # Get user_id from request state (set by middleware)
    user_id = get_user_id(request)
    if not user_id:
        raise HTTPException(status_code=401, detail='Unauthorized')

    # Get user's mnemonic from database
    query = select(User).where(User.c.public_key == user_id.lower())
    user = await database.fetch_one(query)
    if not user:
        raise HTTPException(status_code=404, detail='User not found')

    mnemonic = user['mnemonic']

    # Generate address based on network type
    try:
        if network_id.lower() == 'solana':
            # Generate Solana address using BIP44 derivation path m/44'/501'/0'/0'
            seed = Mnemonic('english').to_seed(mnemonic)

            # Derive the Solana private key using BIP44 path
            path = "m/44'/501'/0'/0'"

            # Implement BIP32 derivation for Solana
            def derive_solana_private_key(seed: bytes, path: str) -> bytes:
                # Start with master key
                masterKey = hmac.new(b'ed25519 seed', seed, hashlib.sha512).digest()
                master_private_key = masterKey[:32]
                master_chain_code = masterKey[32:]

                # Parse path
                path_components = path.split('/')
                if path_components[0] != 'm':
                    raise ValueError('Invalid path')

                current_private_key = master_private_key
                current_chain_code = master_chain_code

                # Derive through path
                for component in path_components[1:]:
                    if not component:
                        continue

                    hardened = component.endswith("'")
                    index = int(component[:-1] if hardened else component)

                    if hardened:
                        index = index + 0x80000000

                    # Data to derive from
                    if hardened:
                        data = b'\x00' + current_private_key + index.to_bytes(4, 'big')
                    else:
                        # Note: For ed25519, we only use hardened derivation
                        raise ValueError('Ed25519 only supports hardened derivation')

                    # Derive new key
                    masterKey = hmac.new(
                        current_chain_code, data, hashlib.sha512
                    ).digest()
                    current_private_key = masterKey[:32]
                    current_chain_code = masterKey[32:]

                return masterKey  # Return the full 64 bytes (private key + chain code)

            # Get the full 64-byte seed
            derived_bytes = derive_solana_private_key(seed, path)
            # Create keypair from the first 32 bytes (private key)
            keypair = Keypair.from_seed(derived_bytes[:32])

            return str(keypair.pubkey())
        else:
            # Assume EVM compatible chain
            # Initialize BIP44 wallet with Ethereum mainnet
            bip44_hdwallet = BIP44HDWallet(cryptocurrency=EthereumMainnet)
            bip44_hdwallet.from_mnemonic(mnemonic)
            bip44_hdwallet.clean_derivation()

            # Derive path for Ethereum m/44'/60'/0'/0/0
            path = "m/44'/60'/0'/0/0"  # Standard Ethereum path
            bip44_hdwallet.from_path(path)

            address = bip44_hdwallet.address()
            # Clean derivation indexes/paths
            bip44_hdwallet.clean_derivation()

            return address
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f'Error generating address: {str(e)}'
        )
