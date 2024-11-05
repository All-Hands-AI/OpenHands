import os

import httpx

from openhands.core.logger import openhands_logger as logger
from openhands.server.sheets_client import GoogleSheetsClient

GITHUB_CLIENT_ID = os.getenv('GITHUB_CLIENT_ID', '').strip()
GITHUB_CLIENT_SECRET = os.getenv('GITHUB_CLIENT_SECRET', '').strip()


class UserVerifier:
    """Verifies GitHub users against allowlists.
    
    This class manages user verification through two possible sources:
    1. A local text file containing usernames
    2. A Google Sheets document containing usernames
    
    The verifier can use either or both sources. If no sources are configured,
    all users are allowed by default.
    
    Attributes:
        file_users: List of usernames from file, if configured
        sheets_client: Google Sheets client, if configured
        spreadsheet_id: ID of Google Sheet, if configured
    """
    
    def __init__(self) -> None:
        """Initialize the verifier.
        
        Raises:
            RuntimeError: If initialization fails critically
        """
        logger.info('Initializing UserVerifier')
        self.file_users: list[str] | None = None
        self.sheets_client: GoogleSheetsClient | None = None
        self.spreadsheet_id: str | None = None

        try:
            # Initialize from environment variables
            self._init_file_users()
            self._init_sheets_client()
            
            # Validate initialization
            if not self.is_active():
                logger.warning('No verification sources configured - all users will be allowed')
                
        except Exception as e:
            logger.error(f'Failed to initialize UserVerifier: {str(e)}', exc_info=True)
            raise RuntimeError(f'UserVerifier initialization failed: {str(e)}')

    def _init_file_users(self) -> None:
        """Load users from text file if configured.
        
        This method attempts to load usernames from a file specified by the
        GITHUB_USER_LIST_FILE environment variable.
        
        Raises:
            FileNotFoundError: If the configured file doesn't exist
            IOError: If there are file system errors
            ValueError: If the file format is invalid
        """
        waitlist = os.getenv('GITHUB_USER_LIST_FILE', '').strip()
        if not waitlist:
            logger.info('GITHUB_USER_LIST_FILE not configured')
            return

        if not os.path.exists(waitlist):
            logger.error(f'User list file not found: {waitlist}')
            raise FileNotFoundError(f'User list file not found: {waitlist}')

        try:
            with open(waitlist, 'r', encoding='utf-8') as f:
                # Read and validate usernames
                usernames = []
                for i, line in enumerate(f, 1):
                    username = line.strip()
                    if username:
                        if not self._is_valid_username(username):
                            logger.warning(
                                f'Invalid GitHub username on line {i}: {username}'
                            )
                            continue
                        usernames.append(username)
                        
                self.file_users = usernames
                logger.info(
                    f'Successfully loaded {len(self.file_users)} users from {waitlist}'
                )
                
        except (IOError, OSError) as e:
            logger.error(f'Error reading user list file {waitlist}: {str(e)}')
            raise
        except Exception as e:
            logger.error(f'Unexpected error reading {waitlist}: {str(e)}')
            raise ValueError(f'Invalid user list file format: {str(e)}')

    def _init_sheets_client(self) -> None:
        """Initialize Google Sheets client if configured.
        
        This method attempts to initialize the Google Sheets client if
        GITHUB_USERS_SHEET_ID is configured.
        
        Raises:
            ValueError: If sheet ID is invalid
            RuntimeError: If client initialization fails
        """
        sheet_id = os.getenv('GITHUB_USERS_SHEET_ID', '').strip()
        if not sheet_id:
            logger.info('GITHUB_USERS_SHEET_ID not configured')
            return
            
        if not self._is_valid_sheet_id(sheet_id):
            logger.error(f'Invalid Google Sheet ID: {sheet_id}')
            raise ValueError('Invalid Google Sheet ID format')

        try:
            logger.info('Initializing Google Sheets integration')
            self.sheets_client = GoogleSheetsClient()
            self.spreadsheet_id = sheet_id
            logger.debug('Successfully initialized Google Sheets client')
        except Exception as e:
            logger.error(f'Failed to initialize Google Sheets client: {str(e)}')
            raise RuntimeError(f'Google Sheets initialization failed: {str(e)}')

    def is_active(self) -> bool:
        """Check if any verification source is configured.
        
        Returns:
            bool: True if at least one source is configured
        """
        return bool(self.file_users or (self.sheets_client and self.spreadsheet_id))

    def is_user_allowed(self, username: str) -> bool:
        """Check if a user is allowed.
        
        This method checks the provided username against all configured
        verification sources. If no sources are configured, all users
        are allowed.
        
        Args:
            username: GitHub username to check
            
        Returns:
            bool: True if user is allowed, False otherwise
            
        Raises:
            ValueError: If username is invalid
        """
        # Validate input
        if not username or not isinstance(username, str):
            raise ValueError('Invalid username')
            
        if not self._is_valid_username(username):
            raise ValueError('Invalid GitHub username format')
            
        # If no verification sources, allow all
        if not self.is_active():
            logger.info('No verification sources active - allowing all users')
            return True

        logger.info(f'Checking if GitHub user {username} is allowed')
        
        # Check file allowlist
        if self.file_users:
            if username in self.file_users:
                logger.info(f'User {username} found in text file allowlist')
                return True
            logger.debug(f'User {username} not found in text file allowlist')

        # Check Google Sheets allowlist
        if self.sheets_client and self.spreadsheet_id:
            try:
                sheet_users = self.sheets_client.get_usernames(self.spreadsheet_id)
                if username in sheet_users:
                    logger.info(f'User {username} found in Google Sheets allowlist')
                    return True
                logger.debug(f'User {username} not found in Google Sheets allowlist')
            except Exception as e:
                logger.error(f'Error checking Google Sheets: {str(e)}')
                # Continue with other sources if available

        logger.info(f'User {username} not found in any allowlist')
        return False
        
    @staticmethod
    def _is_valid_username(username: str) -> bool:
        """Validate GitHub username format.
        
        Args:
            username: Username to validate
            
        Returns:
            bool: True if username is valid
        """
        import re
        # GitHub username rules:
        # - Only alphanumeric characters or hyphens
        # - Cannot have multiple consecutive hyphens
        # - Cannot begin or end with a hyphen
        # - Maximum is 39 characters
        pattern = r'^[a-zA-Z0-9](?:[a-zA-Z0-9]|-(?=[a-zA-Z0-9])){0,38}$'
        return bool(re.match(pattern, username))
        
    @staticmethod
    def _is_valid_sheet_id(sheet_id: str) -> bool:
        """Validate Google Sheet ID format.
        
        Args:
            sheet_id: Sheet ID to validate
            
        Returns:
            bool: True if sheet ID is valid
        """
        # Google Sheet IDs are base-58 strings of specific length
        return bool(sheet_id and len(sheet_id) in [44, 51, 52])


async def authenticate_github_user(auth_token: str | None) -> bool:
    """Authenticate a GitHub user.
    
    This function verifies a GitHub user through the following steps:
    1. Validates the authentication token
    2. Retrieves the user information from GitHub
    3. Checks if the user is in the allowlist (if configured)
    
    Args:
        auth_token: GitHub authentication token
        
    Returns:
        bool: True if authentication succeeds, False otherwise
        
    Raises:
        ValueError: If token format is invalid
        RuntimeError: If authentication process fails
    """
    try:
        # Validate token format
        if not auth_token or not isinstance(auth_token, str):
            logger.warning('Invalid or missing GitHub token')
            return False
            
        # Initialize verifier
        try:
            user_verifier = UserVerifier()
        except Exception as e:
            logger.error(f'Failed to initialize user verifier: {str(e)}')
            raise RuntimeError('User verification system unavailable')

        # Skip verification if no sources configured
        if not user_verifier.is_active():
            logger.info('No user verification sources configured - allowing all users')
            return True

        logger.info('Checking GitHub token')
        
        # Get GitHub user
        try:
            login = await get_github_user(auth_token)
            if not login:
                logger.warning('Failed to get GitHub username from token')
                return False
        except ValueError as e:
            logger.warning(f'Invalid GitHub token: {str(e)}')
            return False
        except Exception as e:
            logger.error(f'Error getting GitHub user: {str(e)}')
            raise RuntimeError(f'GitHub API error: {str(e)}')

        # Check if user is allowed
        try:
            if not user_verifier.is_user_allowed(login):
                logger.warning(f'GitHub user {login} not in allow list')
                return False
        except ValueError as e:
            logger.warning(f'Invalid GitHub username {login}: {str(e)}')
            return False
        except Exception as e:
            logger.error(f'Error checking user allowlist: {str(e)}')
            raise RuntimeError(f'User verification error: {str(e)}')

        logger.info(f'GitHub user {login} authenticated')
        return True
        
    except Exception as e:
        logger.error(f'Unexpected authentication error: {str(e)}', exc_info=True)
        raise


async def get_github_user(token: str) -> str:
    """Get GitHub user info from token.

    This function makes an authenticated request to the GitHub API to retrieve
    user information from an access token.

    Args:
        token: GitHub access token
        
    Returns:
        str: GitHub username (login)
        
    Raises:
        ValueError: If token is invalid or response is malformed
        RuntimeError: If API request fails
        
    Notes:
        - Uses GitHub API v3 with custom media type
        - Requires 'user' scope on token
        - Rate limits may apply
    """
    if not token or not isinstance(token, str):
        raise ValueError('Invalid GitHub token')
        
    logger.info('Fetching GitHub user info from token')
    
    # Prepare request
    headers = {
        'Accept': 'application/vnd.github+json',
        'Authorization': f'Bearer {token}',
        'X-GitHub-Api-Version': '2022-11-28',
    }
    
    try:
        # Make request with timeout
        async with httpx.AsyncClient() as client:
            logger.debug('Making request to GitHub API')
            try:
                response = await client.get(
                    'https://api.github.com/user',
                    headers=headers,
                    timeout=10.0  # 10 second timeout
                )
            except httpx.TimeoutException:
                logger.error('GitHub API request timed out')
                raise RuntimeError('GitHub API timeout')
                
            # Handle response
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    logger.warning('Invalid GitHub token')
                    raise ValueError('Invalid GitHub token')
                elif e.response.status_code == 403:
                    logger.warning('GitHub token lacks required permissions')
                    raise ValueError('Token lacks permissions')
                else:
                    logger.error(f'GitHub API error: {e.response.text}')
                    raise RuntimeError(f'GitHub API error: {str(e)}')
                    
            # Parse response
            try:
                user_data = response.json()
            except ValueError as e:
                logger.error(f'Invalid JSON response from GitHub: {str(e)}')
                raise RuntimeError('Invalid response format from GitHub')
                
            # Extract username
            login = user_data.get('login')
            if not login or not isinstance(login, str):
                logger.error('No username in GitHub response')
                raise RuntimeError('Missing username in GitHub response')
                
            logger.info(f'Successfully retrieved GitHub user: {login}')
            return login
            
    except Exception as e:
        if not isinstance(e, (ValueError, RuntimeError)):
            logger.error(f'Unexpected error getting GitHub user: {str(e)}', exc_info=True)
            raise RuntimeError(f'GitHub API error: {str(e)}')
        raise
