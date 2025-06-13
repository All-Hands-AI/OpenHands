import os
from typing import Optional

import httpx
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from openhands.core.logger import openhands_logger as logger

load_dotenv()

app = APIRouter(prefix='/api/auth')

# JWT settings
JWT_SECRET = os.getenv('JWT_SECRET')
JWT_ALGORITHM = 'HS256'


class SignupRequest(BaseModel):
    publicAddress: str
    signature: str
    publicKey: Optional[str] = None  # public key of the user
    deviceId: Optional[str] = None  # device id of the user


class SignupResponse(BaseModel):
    token: str
    user: dict


@app.post('/signup', response_model=SignupResponse)
async def signup(request: SignupRequest) -> SignupResponse:
    """Sign up with Ethereum wallet."""
    url = f"{os.getenv('THESIS_AUTH_SERVER_URL')}/api/users/login"
    payload = {
        'signature': request.signature,
        'publicAddress': request.publicAddress,
        'publicKey': request.publicKey,
        'deviceId': request.deviceId,
    }

    headers = {'Content-Type': 'application/json'}

    # TODO: bypass auth server for dev mode
    if os.getenv('RUN_MODE') == 'DEV':
        return SignupResponse(
            token='jwt_token',
            user={
                'id': '0x25bE302C3954b4DF9F67AFD6BfDD8c39f4Dc98Dc',
                'publicAddress': '0x25bE302C3954b4DF9F67AFD6BfDD8c39f4Dc98Dc',
            },
        )

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
        logger.error(f'Error signing up: {str(e)}')
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
