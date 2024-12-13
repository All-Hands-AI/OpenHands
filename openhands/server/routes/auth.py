import time
import warnings

import requests

from openhands.server.github_utils import (
    GITHUB_CLIENT_ID,
    GITHUB_CLIENT_SECRET,
    authenticate_github_user,
)

with warnings.catch_warnings():
    warnings.simplefilter('ignore')

from fastapi import (
    APIRouter,
    Request,
    status,
)
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from openhands.core.logger import openhands_logger as logger
from openhands.server.auth import sign_token
from openhands.server.shared import config

app = APIRouter(prefix='/api')


class AuthCode(BaseModel):
    code: str


@app.post('/github/callback')
def github_callback(auth_code: AuthCode):
    # Prepare data for the token exchange request
    data = {
        'client_id': GITHUB_CLIENT_ID,
        'client_secret': GITHUB_CLIENT_SECRET,
        'code': auth_code.code,
    }

    logger.debug('Exchanging code for GitHub token')

    headers = {'Accept': 'application/json'}
    response = requests.post(
        'https://github.com/login/oauth/access_token', data=data, headers=headers
    )

    if response.status_code != 200:
        logger.error(f'Failed to exchange code for token: {response.text}')
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={'error': 'Failed to exchange code for token'},
        )

    token_response = response.json()

    if 'access_token' not in token_response:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={'error': 'No access token in response'},
        )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={'access_token': token_response['access_token']},
    )


@app.post('/authenticate')
async def authenticate(request: Request):
    token = request.headers.get('X-GitHub-Token')
    if not await authenticate_github_user(token):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={'error': 'Not authorized via GitHub waitlist'},
        )

    # Create a signed JWT token with 1-hour expiration
    cookie_data = {
        'github_token': token,
        'exp': int(time.time()) + 3600,  # 1 hour expiration
    }
    signed_token = sign_token(cookie_data, config.jwt_secret)

    response = JSONResponse(
        status_code=status.HTTP_200_OK, content={'message': 'User authenticated'}
    )

    # Set secure cookie with signed token
    response.set_cookie(
        key='github_auth',
        value=signed_token,
        max_age=3600,  # 1 hour in seconds
        httponly=True,
        secure=True,
        samesite='strict',
    )
    return response
