import os
from typing import List, Optional

import httpx

from openhands.core.logger import openhands_logger as logger
from openhands.server.sheets_client import GoogleSheetsClient

GITHUB_CLIENT_ID = os.getenv('GITHUB_CLIENT_ID', '').strip()
GITHUB_CLIENT_SECRET = os.getenv('GITHUB_CLIENT_SECRET', '').strip()

class UserVerifier:
    def __init__(self):
        logger.info('Initializing UserVerifier')
        self.file_users: Optional[List[str]] = None
        self.sheets_client: Optional[GoogleSheetsClient] = None
        self.spreadsheet_id: Optional[str] = None
        
        # Initialize from environment variables
        self._init_file_users()
        self._init_sheets_client()
        
        # Log initialization status
        if self.file_users:
            logger.info(f'Text file verification enabled with {len(self.file_users)} users')
        if self.sheets_client and self.spreadsheet_id:
            logger.info(f'Google Sheets verification enabled with sheet ID: {self.spreadsheet_id}')
        if not self.file_users and not self.sheets_client:
            logger.warning('No verification sources configured - all users will be allowed')
    
    def _init_file_users(self):
        """Load users from text file if configured"""
        waitlist = os.getenv('GITHUB_USER_LIST_FILE')
        if not waitlist:
            logger.info('GITHUB_USER_LIST_FILE not configured')
            return
            
        if not os.path.exists(waitlist):
            logger.warning(f'User list file not found: {waitlist}')
            return
            
        try:
            with open(waitlist, 'r') as f:
                self.file_users = [line.strip() for line in f if line.strip()]
            logger.info(f'Successfully loaded {len(self.file_users)} users from {waitlist}')
        except Exception as e:
            logger.error(f'Error reading user list file {waitlist}: {str(e)}')
    
    def _init_sheets_client(self):
        """Initialize Google Sheets client if configured"""
        sheet_id = os.getenv('GITHUB_USERS_SHEET_ID')
        
        if not sheet_id:
            logger.info('GITHUB_USERS_SHEET_ID not configured')
            return
            
        logger.info('Initializing Google Sheets integration')
        self.sheets_client = GoogleSheetsClient()
        self.spreadsheet_id = sheet_id
    
    def is_user_allowed(self, username: str) -> bool:
        """Check if user is allowed based on file and/or sheet configuration"""
        logger.info(f'Checking if user {username} is allowed')
        
        # If no verification sources are configured, allow all users
        if not self.file_users and not self.sheets_client:
            logger.info('No verification sources configured - allowing all users')
            return True
            
        # Check file-based users
        if self.file_users:
            if username in self.file_users:
                logger.info(f'User {username} found in text file allowlist')
                return True
            logger.debug(f'User {username} not found in text file allowlist')
            
        # Check Google Sheets users
        if self.sheets_client and self.spreadsheet_id:
            sheet_users = self.sheets_client.get_usernames(self.spreadsheet_id)
            if username in sheet_users:
                logger.info(f'User {username} found in Google Sheets allowlist')
                return True
            logger.debug(f'User {username} not found in Google Sheets allowlist')
                
        logger.info(f'User {username} not found in any allowlist')
        return False

# Global instance of user verifier
user_verifier = UserVerifier()


async def authenticate_github_user(auth_token) -> bool:
    logger.info('Checking GitHub token')
    
    if not auth_token:
        logger.warning('No GitHub token provided')
        return False

    login, error = await get_github_user(auth_token)
    if error:
        logger.warning(f'Invalid GitHub token: {error}')
        return False
        
    if not user_verifier.is_user_allowed(login):
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
    logger.info('Fetching GitHub user info from token')
    headers = {
        'Accept': 'application/vnd.github+json',
        'Authorization': f'Bearer {token}',
        'X-GitHub-Api-Version': '2022-11-28',
    }
    try:
        async with httpx.AsyncClient() as client:
            logger.debug('Making request to GitHub API')
            response = await client.get('https://api.github.com/user', headers=headers)
            
            if response.status_code == 200:
                user_data = response.json()
                login = user_data.get('login')
                logger.info(f'Successfully retrieved GitHub user: {login}')
                return login, None
            else:
                error = f'GitHub API error: {response.status_code} - {response.text}'
                logger.error(error)
                return None, error
                
    except Exception as e:
        error = f'Error connecting to GitHub: {str(e)}'
        logger.error(error)
        return None, error
