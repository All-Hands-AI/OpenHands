import os
from datetime import datetime

# timedelta
import httpx
import jwt
from eth_account.messages import encode_defunct
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from web3 import Web3

app = APIRouter(prefix='/api/auth')


# TODO: implement get nonce for signing message later
# Message that users will sign with their wallet
AUTH_MESSAGE = 'Sign to confirm account access to Thesis'

# JWT settings
JWT_SECRET = os.getenv('JWT_SECRET')

JWT_ALGORITHM = 'HS256'


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
    payload = {'signature': request.signature, 'publicAddress': request.publicAddress}
    headers = {'Content-Type': 'application/json'}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, headers=headers, json=payload)

        if response.status_code >= 400:
            raise HTTPException(
                status_code=response.status_code,
                detail=response.json().get('error', 'Authentication failed'),
            )

        res_json = response.json()

        return SignupResponse(
            token=res_json['token'],
            user={
                'id': res_json['user']['publicAddress'],
                'publicAddress': res_json['user']['publicAddress'],
            },
        )

    except httpx.RequestError as exc:
        raise HTTPException(status_code=500, detail=f'Connection error: {str(exc)}')

    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error signing up: {str(e)}')


@app.get('/address-by-network/{network_id}')
async def get_address_by_network(network_id: str, request: Request) -> str:
    try:
        user = request.state.user

        if network_id.lower() == 'solana':
            return user.solanaThesisAddress
        elif network_id.lower() == 'evm':
            return user.ethThesisAddress
        else:
            raise HTTPException(status_code=400, detail='Invalid network id')
    except Exception as e:
        print('error', e)
        raise HTTPException(
            status_code=500, detail=f'Error generating address: {str(e)}'
        )
