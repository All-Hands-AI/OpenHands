import os

import httpx

from openhands.core.logger import openhands_logger as logger

GITHUB_CLIENT_ID = os.getenv('GITHUB_CLIENT_ID', '').strip()
GITHUB_CLIENT_SECRET = os.getenv('GITHUB_CLIENT_SECRET', '').strip()
GITHUB_USER_LIST = None


def load_github_user_list():
    global GITHUB_USER_LIST
    waitlist = os.getenv('GITHUB_USER_LIST_FILE')
    if waitlist:
        with open(waitlist, 'r') as f:
            GITHUB_USER_LIST = [line.strip() for line in f if line.strip()]


load_github_user_list()


async def authenticate_github_user(auth_token) -> bool:
    logger.info('Checking GitHub token')
    if not GITHUB_USER_LIST:
        return True

    if not auth_token:
        logger.warning('No GitHub token provided')
        return False

    login, error = await get_github_user(auth_token)
    if error:
        logger.warning(f'Invalid GitHub token: {error}')
        return False
    if login not in GITHUB_USER_LIST:
        logger.warning(f'GitHub user {login} not in allow list')
        return False

    logger.info(f'GitHub user {login} authenticated')
    return True


async def get_github_user(token: str) -> tuple[str | None, str | None]:
    """Get GitHub user info from token.

    Args:
        token: GitHub access token

    Returns:
        Tuple of (login, error_message)
        If successful, error_message is None
        If failed, login is None and error_message contains the error
    """
    headers = {
        'Accept': 'application/vnd.github+json',
        'Authorization': f'Bearer {token}',
        'X-GitHub-Api-Version': '2022-11-28',
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get('https://api.github.com/user', headers=headers)
            if response.status_code == 200:
                user_data = response.json()
                return user_data.get('login'), None
            else:
                return (
                    None,
                    f'GitHub API error: {response.status_code} - {response.text}',
                )
    except Exception as e:
        return None, f'Error connecting to GitHub: {str(e)}'
