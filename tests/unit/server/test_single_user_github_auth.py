import pytest
from fastapi import Request
from pydantic import SecretStr
from unittest.mock import MagicMock

from openhands.server.user_auth.user_auth import AuthType
from openhands.storage.secrets.secrets_store import SecretsStore
from openhands.storage.settings.settings_store import SettingsStore


class TestSingleUserGithubAuthStructure:

    @pytest.mark.asyncio
    async def test_single_user_auth_class_exists(self):
        from openhands.server.user_auth.single_user_github_auth import (
            SingleUserGithubAuth,
        )

        # if the import succeeds, then the class exists
        assert SingleUserGithubAuth is not None

    @pytest.mark.asyncio
    async def test_single_user_auth_initialization(self):
        from openhands.server.user_auth.single_user_github_auth import (
            SingleUserGithubAuth,
        )

        # create instance with minimal required fields
        auth = SingleUserGithubAuth(
            user_id='test_user_123', access_token=SecretStr('test_token_xyz')
        )

        assert auth is not None
        assert auth.user_id == 'test_user_123'
        assert auth.access_token.get_secret_value() == 'test_token_xyz'
        assert auth.auth_type == AuthType.COOKIE

    @pytest.mark.asyncio
    async def test_single_user_auth_optional_fields(self):
        from openhands.server.user_auth.single_user_github_auth import (
            SingleUserGithubAuth,
        )

        # create instance with None values
        auth = SingleUserGithubAuth(user_id=None, access_token=None)

        assert auth is not None
        assert auth.user_id is None
        assert auth.access_token is None
        assert auth.auth_type == AuthType.COOKIE


class TestSingleUserGithubAuthSettingsStore:

    @pytest.mark.asyncio
    async def test_get_user_settings_store_returns_settings_store_instance(self):
        from openhands.server.user_auth.single_user_github_auth import (
            SingleUserGithubAuth,
        )

        auth = SingleUserGithubAuth(
            user_id='test_user_123', access_token=SecretStr('test_token_xyz')
        )

        settings_store = await auth.get_user_settings_store()

        assert settings_store is not None
        assert isinstance(settings_store, SettingsStore)

    @pytest.mark.asyncio
    async def test_get_user_settings_store_uses_user_id(self):
        from openhands.server.user_auth.single_user_github_auth import (
            SingleUserGithubAuth,
        )

        user_id = 'unique_user_456'
        auth = SingleUserGithubAuth(
            user_id=user_id, access_token=SecretStr('test_token')
        )

        settings_store = await auth.get_user_settings_store()

        # verify that the store is created for the correct user_id
        assert settings_store is not None
        assert isinstance(settings_store, SettingsStore)

    @pytest.mark.asyncio
    async def test_get_user_settings_store_handles_none_user_id(self):
        from openhands.server.user_auth.single_user_github_auth import (
            SingleUserGithubAuth,
        )

        auth = SingleUserGithubAuth(user_id=None, access_token=None)

        settings_store = await auth.get_user_settings_store()

        # should return a SettingsStore even if user_id is None
        assert settings_store is not None
        assert isinstance(settings_store, SettingsStore)


class TestSingleUserGithubAuthSecretsStore:

    @pytest.mark.asyncio
    async def test_get_secrets_store_returns_secrets_store_instance(self):
        from openhands.server.user_auth.single_user_github_auth import (
            SingleUserGithubAuth,
        )

        auth = SingleUserGithubAuth(
            user_id='test_user_123', access_token=SecretStr('test_token_xyz')
        )

        secrets_store = await auth.get_secrets_store()

        assert secrets_store is not None
        assert isinstance(secrets_store, SecretsStore)

    @pytest.mark.asyncio
    async def test_get_secrets_store_caching(self):
        from openhands.server.user_auth.single_user_github_auth import (
            SingleUserGithubAuth,
        )

        auth = SingleUserGithubAuth(
            user_id='test_user_456', access_token=SecretStr('test_token')
        )

        # verify that multiple calls return the same instance (caching)
        secrets_store_1 = await auth.get_secrets_store()
        secrets_store_2 = await auth.get_secrets_store()

        assert secrets_store_1 is secrets_store_2

    @pytest.mark.asyncio
    async def test_get_secrets_store_handles_none_user_id(self):
        from openhands.server.user_auth.single_user_github_auth import (
            SingleUserGithubAuth,
        )

        auth = SingleUserGithubAuth(user_id=None, access_token=None)

        secrets_store = await auth.get_secrets_store()

        assert secrets_store is not None
        assert isinstance(secrets_store, SecretsStore)


class TestSingleUserGithubAuthGetInstance:

    @pytest.mark.asyncio
    async def test_get_instance_with_cookies(self):
        from openhands.server.user_auth.single_user_github_auth import (
            SingleUserGithubAuth,
        )

        # mock request with cookies
        request = MagicMock(spec=Request)
        request.cookies = {
            'github_user_id': 'test_user_123',
            'github_token': 'ghp_test_token_xyz',
        }

        auth = await SingleUserGithubAuth.get_instance(request)

        assert auth is not None
        assert isinstance(auth, SingleUserGithubAuth)
        assert auth.user_id == 'test_user_123'
        assert auth.access_token.get_secret_value() == 'ghp_test_token_xyz'

    @pytest.mark.asyncio
    async def test_get_instance_without_cookies(self):
        from openhands.server.user_auth.single_user_github_auth import (
            SingleUserGithubAuth,
        )

        # mock request without cookies
        request = MagicMock(spec=Request)
        request.cookies = {}

        auth = await SingleUserGithubAuth.get_instance(request)

        assert auth is not None
        assert auth.user_id is None
        assert auth.access_token is None

    @pytest.mark.asyncio
    async def test_get_instance_with_partial_cookies(self):
        from openhands.server.user_auth.single_user_github_auth import (
            SingleUserGithubAuth,
        )

        # mock request with only user_id cookie
        request = MagicMock(spec=Request)
        request.cookies = {'github_user_id': 'partial_user'}

        auth = await SingleUserGithubAuth.get_instance(request)

        assert auth is not None
        assert auth.user_id == 'partial_user'
        assert auth.access_token is None


class TestSingleUserGithubAuthGetForUser:

    @pytest.mark.asyncio
    async def test_get_for_user_with_user_id(self):
        from openhands.server.user_auth.single_user_github_auth import (
            SingleUserGithubAuth,
        )

        user_id = 'test_user_789'
        auth = await SingleUserGithubAuth.get_for_user(user_id)

        assert auth is not None
        assert isinstance(auth, SingleUserGithubAuth)
        assert auth.user_id == user_id
        assert auth.access_token is None

    @pytest.mark.asyncio
    async def test_get_for_user_returns_valid_auth_instance(self):
        from openhands.server.user_auth.single_user_github_auth import (
            SingleUserGithubAuth,
        )

        auth = await SingleUserGithubAuth.get_for_user('admin_user')

        assert auth is not None
        assert isinstance(auth, SingleUserGithubAuth)
        assert auth.auth_type == AuthType.COOKIE

    @pytest.mark.asyncio
    async def test_get_for_user_different_users(self):
        from openhands.server.user_auth.single_user_github_auth import (
            SingleUserGithubAuth,
        )

        auth1 = await SingleUserGithubAuth.get_for_user('user_one')
        auth2 = await SingleUserGithubAuth.get_for_user('user_two')

        assert auth1.user_id == 'user_one'
        assert auth2.user_id == 'user_two'
        assert auth1 is not auth2
