import json
import os
from enum import IntEnum

import requests
from fastapi import HTTPException
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


def get_user_detail_from_thesis_auth_server(bearer_token: str) -> ThesisUser | None:
    url = f"{os.getenv('THESIS_AUTH_SERVER_URL')}/api/users/detail"

    payload = {}
    headers = {'content-type': 'application/json', 'Authorization': f'{bearer_token}'}

    response = requests.request('GET', url, headers=headers, data=payload)
    if response.status_code != 200:
        logger.error(
            f'Failed to get user detail: {response.status_code} - {response.text}'
        )
        raise HTTPException(
            status_code=response.status_code, detail=f"{response.json().get('error')}"
        )
    user_data = response.json()['user']
    if not user_data:
        return None
    return ThesisUser(**user_data)


def add_invite_code_to_user(code: str, bearer_token: str) -> dict | None:
    try:
        url = f"{os.getenv('THESIS_AUTH_SERVER_URL')}/api/users/add-invite-code"
        payload = json.dumps({'code': code})
        headers = {'content-type': 'application/json', 'Authorization': bearer_token}

        response = requests.request('POST', url, headers=headers, data=payload)

        # Check if request was successful
        if response.status_code != 200:
            logger.error(
                f'Failed to add invite code: {response.status_code} - {response.text}'
            )
            raise HTTPException(
                status_code=response.status_code,
                detail=f"{response.json().get('error')}",
            )

        return response.json()
    except Exception as e:
        logger.error(f'Unexpected error while adding invite code: {str(e)}')
        raise HTTPException(status_code=500, detail=f'{e.detail}')
