import hashlib
import hmac
import json
import os
from datetime import datetime

# timedelta
import requests
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
    url = f"{os.getenv('THESIS_AUTH_SERVER_URL')}/api/users/login"
    payload = json.dumps({
        "signature": request.signature,
        "publicAddress": request.publicAddress
    })
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)

    return SignupResponse(
        token=response.json()['token'],
        user=response.json()['user']
    )


@app.get('/address-by-network/{network_id}')
async def get_address_by_network(network_id: str, request: Request) -> str:
    try:
        url = f"{os.getenv('THESIS_AUTH_SERVER_URL')}/api/users/detail"
        payload = {}
        headers = {
            'content-type': 'application/json',
            'Authorization': f'{request.headers.get("Authorization")}'
        }
        print("headers", headers)

        response = requests.request("GET", url, headers=headers, data=payload)
        print("response", response.json())
        if network_id.lower() == 'solana':
            return response.json()['user']['solanaThesisAddress']
        elif network_id.lower() == 'evm':
            return response.json()['user']['ethThesisAddress']
        else:
            raise HTTPException(status_code=400, detail='Invalid network id')
    except Exception as e:
        print("error", e)
        raise HTTPException(
            status_code=500, detail=f'Error generating address: {str(e)}'
        )
