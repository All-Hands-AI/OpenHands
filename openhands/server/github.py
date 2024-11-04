import os

import httpx

from openhands.core.logger import openhands_logger as logger
from openhands.server.sheets_client import GoogleSheetsClient

GITHUB_CLIENT_ID = os.getenv('GITHUB_CLIENT_ID', '').strip()
GITHUB_CLIENT_SECRET = os.getenv('GITHUB_CLIENT_SECRET', '').strip()


class UserVerifier:
    def __init__(self) -> None:
        logger.info('Initializing UserVerifier')
        self.file_users: list[str] | None = None
        self.sheets_client: GoogleSheetsClient | None = None
        self.spreadsheet_id: str | None = None

        # Initialize from environment variables
        self._init_file_users()
        self._init_sheets_client()

    def _init_file_users(self) -> None:
        """Load users from text file if configured"""
        waitlist = os.getenv('GITHUB_USER_LIST_FILE')
        if not waitlist:
            logger.info('GITHUB_USER_LIST_FILE not configured')
            return

        if not os.path.exists(waitlist):
            logger.error(f'User list file not found: {waitlist}')
            raise FileNotFoundError(f'User list file not found: {waitlist}')

        try:
            with open(waitlist, 'r') as f:
                self.file_users = [line.strip() for line in f if line.strip()]
            logger.info(
                f'Successfully loaded {len(self.file_users)} users from {waitlist}'
            )
        except Exception as e:
            logger.error(f'Error reading user list file {waitlist}: {str(e)}')

    def _init_sheets_client(self) -> None:
        """Initialize Google Sheets client if configured"""
        sheet_id = os.getenv('GITHUB_USERS_SHEET_ID')

        if not sheet_id:
            logger.info('GITHUB_USERS_SHEET_ID not configured')
            return

        logger.info('Initializing Google Sheets integration')
        self.sheets_client = GoogleSheetsClient()
        self.spreadsheet_id = sheet_id

    def is_active(self) -> bool:
        return bool(self.file_users or (self.sheets_client and self.spreadsheet_id))

    def is_user_allowed(self, username: str) -> bool:
        """Check if user is allowed based on file and/or sheet configuration"""
        if not self.is_active():
            return True

        logger.info(f'Checking if GitHub user {username} is allowed')
        if self.file_users:
            if username in self.file_users:
                logger.info(f'User {username} found in text file allowlist')
                return True
            logger.debug(f'User {username} not found in text file allowlist')

        if self.sheets_client and self.spreadsheet_id:
            sheet_users = self.sheets_client.get_usernames(self.spreadsheet_id)
            if username in sheet_users:
                logger.info(f'User {username} found in Google Sheets allowlist')
                return True
            logger.debug(f'User {username} not found in Google Sheets allowlist')

        logger.info(f'User {username} not found in any allowlist')
        return False


async def authenticate_github_user(auth_token) -> bool:
    user_verifier = UserVerifier()

    if not user_verifier.is_active():
        logger.info('No user verification sources configured - allowing all users')
        return True

    logger.info('Checking GitHub token')

    if not auth_token:
        logger.warning('No GitHub token provided')
        return False

    login = await get_github_user(auth_token)

    if not user_verifier.is_user_allowed(login):
        logger.warning(f'GitHub user {login} not in allow list')
        return False

    logger.info(f'GitHub user {login} authenticated')
    return True


async def get_github_user(token: str) -> str:
    """Get GitHub user info from token.

    Args:
        token: GitHub access token

    Returns:
        Tuple of (login, error_message)
        If successful, error_message is None
        If failed, login is None and error_message contains the error
    """
    logger.info('Fetching GitHub user info from token')
    headers = {
        'Accept': 'application/vnd.github+json',
        'Authorization': f'Bearer {token}',
        'X-GitHub-Api-Version': '2022-11-28',
    }
    async with httpx.AsyncClient() as client:
        logger.debug('Making request to GitHub API')
        response = await client.get('https://api.github.com/user', headers=headers)
        response.raise_for_status()
        user_data = response.json()
        login = user_data.get('login')
        logger.info(f'Successfully retrieved GitHub user: {login}')
        return login
