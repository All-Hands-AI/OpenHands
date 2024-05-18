import requests

from opendevin.core.config import config


def auth_github(code: str) -> dict:
    client_id = config.github_client_id
    client_secret = config.github_client_secret
    if client_id is None or client_secret is None:
        raise Exception('GitHub OAuth not configured')

    # Exchange the code with GitHub for an access token
    response = requests.post(
        'https://github.com/login/oauth/access_token',
        headers={'Accept': 'application/json'},
        data={
            'client_id': client_id,
            'client_secret': client_secret,
            'code': code,
        },
    )

    if response.status_code != 200:
        raise Exception('Invalid code')

    access_token = response.json().get('access_token')
    if access_token is None:
        raise Exception('Invalid code')

    user_response = requests.get(
        'https://api.github.com/user',
        headers={'Authorization': f'token {access_token}'},
    )

    if user_response.status_code != 200:
        raise Exception('Invalid access token')

    return user_response.json()


def auth_google(code: str) -> dict:
    client_id = config.google_client_id
    client_secret = config.google_client_secret
    redirect_uri = config.google_redirect_uri
    if client_id is None or client_secret is None:
        raise Exception('Google OAuth not configured')

    # Exchange the code with Google for an access token
    response = requests.post(
        'https://oauth2.googleapis.com/token',
        headers={'Accept': 'application/json'},
        data={
            'client_id': client_id,
            'client_secret': client_secret,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': redirect_uri,
        },
    )

    if response.status_code != 200:
        raise Exception('Invalid code')

    access_token = response.json().get('access_token')
    if access_token is None:
        raise Exception('Invalid code')

    user_response = requests.get(
        'https://www.googleapis.com/oauth2/v1/userinfo',
        headers={'Authorization': f'Bearer {access_token}'},
    )

    if user_response.status_code != 200:
        raise Exception('Invalid access token')

    return user_response.json()
