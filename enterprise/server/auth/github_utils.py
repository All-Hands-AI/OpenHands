import os

from integrations.github.github_service import SaaSGitHubService
from pydantic import SecretStr
from server.auth.sheets_client import GoogleSheetsClient

from openhands.core.logger import openhands_logger as logger
from openhands.integrations.github.github_types import GitHubUser


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
                self.file_users = [line.strip().lower() for line in f if line.strip()]
            logger.info(
                f'Successfully loaded {len(self.file_users)} users from {waitlist}'
            )
        except Exception:
            logger.error(f'Error reading user list file {waitlist}', exc_info=True)

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
        if os.getenv('DISABLE_WAITLIST', '').lower() == 'true':
            logger.info('Waitlist disabled via DISABLE_WAITLIST env var')
            return False
        return bool(self.file_users or (self.sheets_client and self.spreadsheet_id))

    def is_user_allowed(self, username: str) -> bool:
        """Check if user is allowed based on file and/or sheet configuration"""
        logger.debug(f'Checking if GitHub user {username} is allowed')
        if self.file_users:
            if username.lower() in self.file_users:
                logger.debug(f'User {username} found in text file allowlist')
                return True
            logger.debug(f'User {username} not found in text file allowlist')

        if self.sheets_client and self.spreadsheet_id:
            sheet_users = [
                u.lower() for u in self.sheets_client.get_usernames(self.spreadsheet_id)
            ]
            if username.lower() in sheet_users:
                logger.debug(f'User {username} found in Google Sheets allowlist')
                return True
            logger.debug(f'User {username} not found in Google Sheets allowlist')

        logger.debug(f'User {username} not found in any allowlist')
        return False


user_verifier = UserVerifier()


def is_user_allowed(user_login: str):
    if user_verifier.is_active() and not user_verifier.is_user_allowed(user_login):
        logger.warning(f'GitHub user {user_login} not in allow list')
        return False

    return True


async def authenticate_github_user_id(auth_user_id: str) -> GitHubUser | None:
    logger.debug('Checking auth status for GitHub user')

    if not auth_user_id:
        logger.warning('No GitHub User ID provided')
        return None

    gh_service = SaaSGitHubService(user_id=auth_user_id)
    try:
        user: GitHubUser = await gh_service.get_user()
        if is_user_allowed(user.login):
            return user

        return None
    except:  # noqa: E722
        logger.warning("GitHub user doens't have valid token")
        return None


async def authenticate_github_user_token(access_token: str):
    if not access_token:
        logger.warning('No GitHub User ID provided')
        return None

    gh_service = SaaSGitHubService(token=SecretStr(access_token))
    try:
        user: GitHubUser = await gh_service.get_user()
        if is_user_allowed(user.login):
            return user

        return None
    except:  # noqa: E722
        logger.warning("GitHub user doens't have valid token")
        return None
