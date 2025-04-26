import os
import time
from enum import IntEnum

import httpx
from fastapi import HTTPException, status
from pydantic import BaseModel

from openhands.core.logger import openhands_logger as logger


class UserStatus(IntEnum):
    INACTIVE = 0
    ACTIVE = 1
    WHITELISTED = 1
    BLACKLISTED = 0


class ThesisUser(BaseModel):
    status: UserStatus
    whitelisted: int
    publicAddress: str
    mnemonic: str
    solanaThesisAddress: str | None = None
    ethThesisAddress: str | None = None
    # Add other fields as needed


thesis_auth_client = httpx.AsyncClient(
    timeout=30.0,
    base_url=os.getenv('THESIS_AUTH_SERVER_URL'),
    headers={'Content-Type': 'application/json'},
)


async def get_user_detail_from_thesis_auth_server(
    bearer_token: str,
    x_device_id: str | None = None,
) -> ThesisUser | None:
    # TODO: bypass auth server for dev mode
    if os.getenv('RUN_MODE') == 'DEV':
        return ThesisUser(
            status=UserStatus.ACTIVE,
            whitelisted=1,
            publicAddress='0x25bE302C3954b4DF9F67AFD6BfDD8c39f4Dc98Dc',
            mnemonic='test test test test test test test test test test test junk',
            solanaThesisAddress='0x25bE302C3954b4DF9F67AFD6BfDD8c39f4Dc98Dc',
            ethThesisAddress='0x25bE302C3954b4DF9F67AFD6BfDD8c39f4Dc98Dc',
        )

    url = '/api/users/detail'
    headers = {'Content-Type': 'application/json', 'Authorization': bearer_token}
    if x_device_id:
        headers['x-device-id'] = x_device_id
    try:
        start_time = time.time()
        response = await thesis_auth_client.get(url, headers=headers)
        end_time = time.time()
        logger.info(f'Time taken to get user detail: {end_time - start_time} seconds')
    except httpx.RequestError as exc:
        logger.error(f'Request error while getting user detail: {exc}')
        raise HTTPException(status_code=500, detail='Unable to reach auth server')

    if response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR:
        logger.error(
            f'Failed to get user detail: {response.status_code} - {response.text}'
        )
        raise HTTPException(
            status_code=response.status_code,
            detail=response.json().get('error', 'Unknown error'),
        )

    if response.status_code == status.HTTP_401_UNAUTHORIZED:
        logger.error(
            f'Failed to get user detail: {response.status_code} - {response.text}'
        )
        raise HTTPException(
            status_code=response.status_code,
            detail=response.json().get('error', f'Unauthorized : {response.text}'),
        )
    user_data = response.json().get('user')
    if not user_data:
        return None

    return ThesisUser(**user_data)


async def add_invite_code_to_user(code: str, bearer_token: str) -> dict | None:
    url = '/api/users/add-invite-code'
    payload = {'code': code}
    headers = {'Content-Type': 'application/json', 'Authorization': bearer_token}

    try:
        response = await thesis_auth_client.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            logger.error(
                f'Failed to add invite code: {response.status_code} - {response.text}'
            )
            raise HTTPException(
                status_code=response.status_code,
                detail=response.json().get('error', 'Unknown error'),
            )

        return response.json()

    except httpx.RequestError as exc:
        logger.error(f'Request error while adding invite code: {str(exc)}')
        raise HTTPException(status_code=500, detail='Could not connect to auth server')
    except Exception as e:
        logger.exception('Unexpected error while adding invite code')
        raise HTTPException(status_code=500, detail=str(e))


async def handle_thesis_auth_request(
    method: str,
    endpoint: str,
    bearer_token: str,
    payload: dict | None = None,
    params: dict | None = None,
) -> dict:
    url = f'{endpoint}'
    headers = {'Content-Type': 'application/json', 'Authorization': bearer_token}

    try:
        response = await thesis_auth_client.request(
            method=method.upper(),
            url=url,
            headers=headers,
            json=payload,  # use json= instead of data=
            params=params,
        )

        if response.status_code >= 400:
            logger.error(
                f'Thesis_auth request failed: {method} {endpoint} {response.status_code} - {response.text}'
            )
            raise HTTPException(
                status_code=response.status_code,
                detail=response.json().get('error', 'Internal server error'),
            )

        return response.json()

    except httpx.RequestError as exc:
        logger.error(
            f'Connection error in Thesis_auth request: {method} {endpoint} {str(exc)}'
        )
        raise HTTPException(status_code=500, detail='Unable to connect to auth server')

    except Exception as e:
        logger.exception(
            f'Unexpected error in Thesis_auth request: {method} {endpoint}'
        )
        raise HTTPException(
            status_code=500, detail=str(getattr(e, 'detail', 'Internal server error'))
        )


def check_access_token_in_header(request):
    authorization = request.headers.get('Authorization')
    if not authorization:
        logger.error('Access token not found in request headers')
        raise HTTPException(
            status_code=401, detail='Unauthorized: Access token is required'
        )

    parts = authorization.split()

    if len(parts) != 2 or parts[0].lower() != 'bearer':
        logger.error("Invalid authorization format. Expected 'Bearer <token>'")
        raise HTTPException(
            status_code=401, detail='Unauthorized: Invalid token format'
        )
