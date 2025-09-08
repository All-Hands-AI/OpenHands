"""Snowcode authentication module for token management and API validation."""

import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Dict, Optional
from openhands.cli.snowcode_config import get_llm_config


import requests


class SnowcodeAuth:
    """Handles Snowcode authentication and token management."""

    def __init__(self):
        self.api_endpoint = 'https://api.snowcell.io/auth/validate'
        self.auth_file_path = Path.home() / '.snowcode' / 'auth.json'

    def validate_token_with_api(self, token: str) -> bool:
        """Validate Snowcode token with the API endpoint.

        Args:
            token: The authentication token to validate

        Returns:
            bool: True if token is valid, False otherwise
        """
        try:
            headers = {'x-api-token': token, 'Content-Type': 'application/json'}

            response = requests.get(self.api_endpoint, headers=headers, timeout=10)

            if response.status_code == 200:
                try:
                    data = response.json()
                    return data.get('status') == 'success'
                except ValueError:
                    return False

            return False
        except (requests.RequestException, Exception):
            return False

    def store_token(self, token: str) -> bool:
        """Store Snowcode authentication token after API validation.

        Args:
            token: The authentication token to store

        Returns:
            bool: True if token was stored successfully, False otherwise
        """
        try:
            # First validate the token with the API
            if not self.validate_token_with_api(token):
                return False

            # Ensure the directory exists
            self.auth_file_path.parent.mkdir(parents=True, exist_ok=True)

            # Create auth data with timestamp and actual token
            auth_data = {
                'token': token,
                'token_hash': hashlib.sha256(token.encode()).hexdigest(),
                'timestamp': time.time(),
                'status': 'active',
            }

            with open(self.auth_file_path, 'w') as f:
                json.dump(auth_data, f, indent=2)

            return True
        except Exception:
            return False

    def load_token(self) -> Optional[Dict]:
        """Load stored Snowcode authentication token.

        Returns:
            dict or None: Auth data dictionary if valid, None otherwise
        """
        try:
            if not self.auth_file_path.exists():
                return None

            with open(self.auth_file_path, 'r') as f:
                auth_data = json.load(f)

            required_fields = ['token', 'timestamp', 'status']
            if not all(key in auth_data for key in required_fields):
                return None

            if auth_data.get('status') != 'active':
                return None

            return auth_data
        except Exception:
            return None

    def is_authenticated(self) -> bool:
        """Check if user is authenticated with Snowcode.

        Returns:
            bool: True if authenticated and token is valid, False otherwise
        """
        auth_data = self.load_token()
        if not auth_data:
            return False

        # Re-validate with API to ensure token is still valid
        return self.validate_token_with_api(auth_data['token'])

    def logout(self) -> bool:
        """Logout from Snowcode by removing stored token.

        Returns:
            bool: True if logout was successful, False otherwise
        """
        try:
            if self.auth_file_path.exists():
                self.auth_file_path.unlink()
            return True
        except Exception:
            return False

    def get_login_time(self) -> Optional[str]:
        """Get formatted login timestamp.

        Returns:
            str or None: Formatted login time string, None if not authenticated
        """
        auth_data = self.load_token()
        if not auth_data:
            return None

        timestamp = auth_data.get('timestamp', 0)
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))

    def setup_environment(self) -> bool:
        """Setup environment for Snowcode usage.

        Returns:
            bool: True if setup was successful, False otherwise
        """
        if not self.is_authenticated():
            return False

        return True

    async def ensure_default_config_exists(self) -> bool:
        """Ensure default Snowcode configuration exists if user is authenticated.

        This is called automatically when CLI starts to ensure configuration is ready.

        Returns:
            bool: True if config exists or was created, False otherwise
        """
        try:
            if not self.is_authenticated():
                return False

            from openhands.core.config import load_openhands_config
            from openhands.storage.settings.file_settings_store import FileSettingsStore

            config = load_openhands_config()
            settings_store = await FileSettingsStore.get_instance(config, None)
            settings = await settings_store.load()

            expected_llm_model, _ = get_llm_config()

            # If no settings exist, or if Snowcode model is not configured, set it up
            if (
                not settings
                or not settings.llm_model
                or settings.llm_model != expected_llm_model
            ):

                return await self.setup_default_snowcode_config()

            # Configuration already exists
            return True

        except Exception:
            return False

    async def setup_default_snowcode_config(self) -> bool:
        """Automatically setup default Snowcode configuration in .openhands/settings.json .

        This function creates the default configuration so users don't need to configure
        anything except login with their token.

        Returns:
            bool: True if setup was successful, False otherwise
        """
        try:
            from openhands.core.config import load_openhands_config
            from openhands.storage.data_models.settings import Settings
            from openhands.storage.settings.file_settings_store import FileSettingsStore
            from pydantic import SecretStr

            auth_data = self.load_token()
            if not auth_data or not auth_data.get('token'):
                return False

            user_token = auth_data['token']

            llm_model, llm_base_url = get_llm_config()

            config = load_openhands_config()
            settings_store = await FileSettingsStore.get_instance(config, None)
            settings = await settings_store.load()

            if not settings:
                settings = Settings()

            settings.llm_model = llm_model
            settings.llm_base_url = llm_base_url
            settings.llm_api_key = SecretStr(user_token)
            settings.agent = 'CodeActAgent'
            settings.confirmation_mode = True
            settings.enable_default_condenser = True

            await settings_store.store(settings)

            return True

        except Exception as e:
            print(f"Warning: Could not setup default configuration: {e}")
            return False

    def create_default_config(self) -> Dict:
        """Create default configuration for Snowcode.

        Returns:
            dict: Default configuration dictionary
        """
        auth_data = self.load_token()
        if not auth_data:
            return {}

        llm_model, llm_base_url = get_llm_config()

        return {
            'model': llm_model,
            'base_url': llm_base_url,
            'api_key': auth_data['token'],
            'agent': 'CodeActAgent',
            'confirmation_mode': True,
            'memory_condensation': True,
        }


# Create a global instance for easy access
snowcode_auth = SnowcodeAuth()


# CLI handler functions for backward compatibility
async def handle_snow_login(token: str) -> None:
    """Handle Snowcode login with token and setup default configuration."""
    print('Authenticating with Snowcode...')

    if snowcode_auth.store_token(token):
        print('✅ Authentication successful!')

        # Setup default configuration automatically
        print('⚙️  Setting up default configuration...')
        config_success = await snowcode_auth.setup_default_snowcode_config()

        if config_success:
            print('✅ Default configuration applied!')
        else:
            print('⚠️  Could not setup default configuration automatically')
            print('💡 You can configure manually using settings menu')

        print('🚀 You can now use "snow" to start a chat session.')
    else:
        print('❌ Authentication failed. Please check your token and try again.')
        sys.exit(1)


def handle_snow_status() -> None:
    """Handle Snowcode authentication status check."""
    if snowcode_auth.is_authenticated():
        login_time = snowcode_auth.get_login_time()
        print('✅ Authenticated with Snowcode')
        if login_time:
            print(f'🕒 Logged in at: {login_time}')
    else:
        print('❌ Not authenticated with Snowcode')
        print('💡 Use "snow --token YOUR_TOKEN" to login')


def handle_snow_logout() -> None:
    """Handle Snowcode logout."""
    if snowcode_auth.logout():
        print('✅ Successfully logged out from Snowcode')
    else:
        print('❌ Logout failed or already logged out')


# Legacy function aliases for backward compatibility
def validate_snow_token_with_api(token: str) -> bool:
    """Legacy function - use snowcode_auth.validate_token_with_api() instead."""
    return snowcode_auth.validate_token_with_api(token)


def store_snow_token(token: str) -> bool:
    """Legacy function - use snowcode_auth.store_token() instead."""
    return snowcode_auth.store_token(token)


def load_snow_token() -> Optional[Dict]:
    """Legacy function - use snowcode_auth.load_token() instead."""
    return snowcode_auth.load_token()


def is_snow_authenticated() -> bool:
    """Legacy function - use snowcode_auth.is_authenticated() instead."""
    return snowcode_auth.is_authenticated()


def logout_snow() -> bool:
    """Legacy function - use snowcode_auth.logout() instead."""
    return snowcode_auth.logout()
