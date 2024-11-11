import os

from github import Github
from github.GithubException import GithubException
from tenacity import retry, stop_after_attempt, wait_exponential

from openhands.core.logger import openhands_logger as logger
from openhands.server.sheets_client import GoogleSheetsClient
from openhands.utils.async_utils import call_sync_from_async

GITHUB_CLIENT_ID = os.getenv('GITHUB_CLIENT_ID', '').strip()
GITHUB_CLIENT_SECRET = os.getenv('GITHUB_CLIENT_SECRET', '').strip()


class UserVerifier:
    def __init__(self) -> None:
        logger.debug('Initializing UserVerifier')
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
            logger.debug('GITHUB_USER_LIST_FILE not configured')
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
            logger.debug('GITHUB_USERS_SHEET_ID not configured')
            return

        logger.debug('Initializing Google Sheets integration')
        self.sheets_client = GoogleSheetsClient()
        self.spreadsheet_id = sheet_id

    def is_active(self) -> bool:
        return bool(self.file_users or (self.sheets_client and self.spreadsheet_id))

    def is_user_allowed(self, username: str) -> bool:
        """Check if user is allowed based on file and/or sheet configuration"""
        if not self.is_active():
            return True

        logger.debug(f'Checking if GitHub user {username} is allowed')
        if self.file_users:
            if username in self.file_users:
                logger.debug(f'User {username} found in text file allowlist')
                return True
            logger.debug(f'User {username} not found in text file allowlist')

        if self.sheets_client and self.spreadsheet_id:
            sheet_users = self.sheets_client.get_usernames(self.spreadsheet_id)
            if username in sheet_users:
                logger.debug(f'User {username} found in Google Sheets allowlist')
                return True
            logger.debug(f'User {username} not found in Google Sheets allowlist')

        logger.debug(f'User {username} not found in any allowlist')
        return False


async def authenticate_github_user(auth_token) -> bool:
    user_verifier = UserVerifier()

    if not user_verifier.is_active():
        logger.debug('No user verification sources configured - allowing all users')
        return True

    logger.debug('Checking GitHub token')

    if not auth_token:
        logger.warning('No GitHub token provided')
        return False

    login = await get_github_user(auth_token)

    if not user_verifier.is_user_allowed(login):
        logger.warning(f'GitHub user {login} not in allow list')
        return False

    logger.info(f'GitHub user {login} authenticated')
    return True


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=5))
async def get_github_user(token: str) -> str:
    """Get GitHub user info from token.

    Args:
        token: GitHub access token

    Returns:
        github handle of the user
    """
    logger.debug('Fetching GitHub user info from token')
    try:
        g = Github(token)
        user = await call_sync_from_async(g.get_user)
        login = user.login
        logger.info(f'Successfully retrieved GitHub user: {login}')
        return login
    except GithubException as e:
        logger.error(f'Error making request to GitHub API: {str(e)}')
        logger.error(e)
        raise
