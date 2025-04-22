from __future__ import annotations

from types import MappingProxyType
from typing import Any

from pydantic import SecretStr

from openhands.integrations.provider import ProviderToken, ProviderType, SecretStore


class TestSecretStore:
    def test_adding_only_provider_tokens(self):
        """Test adding only provider tokens to the SecretStore."""
        # Create provider tokens
        github_token = ProviderToken(
            token=SecretStr('github-token-123'), user_id='user1'
        )
        gitlab_token = ProviderToken(
            token=SecretStr('gitlab-token-456'), user_id='user2'
        )

        # Create a store with only provider tokens
        provider_tokens = {
            ProviderType.GITHUB: github_token,
            ProviderType.GITLAB: gitlab_token,
        }

        # Initialize the store with a dict that will be converted to MappingProxyType
        store = SecretStore(provider_tokens=provider_tokens)

        # Verify the tokens were added correctly
        assert isinstance(store.provider_tokens, MappingProxyType)
        assert len(store.provider_tokens) == 2
        assert (
            store.provider_tokens[ProviderType.GITHUB].token.get_secret_value()
            == 'github-token-123'
        )
        assert store.provider_tokens[ProviderType.GITHUB].user_id == 'user1'
        assert (
            store.provider_tokens[ProviderType.GITLAB].token.get_secret_value()
            == 'gitlab-token-456'
        )
        assert store.provider_tokens[ProviderType.GITLAB].user_id == 'user2'

        # Verify custom_secrets is empty
        assert isinstance(store.custom_secrets, MappingProxyType)
        assert len(store.custom_secrets) == 0

    def test_adding_only_custom_secrets(self):
        """Test adding only custom secrets to the SecretStore."""
        # Create custom secrets
        custom_secrets = {
            'API_KEY': 'api-key-123',
            'DATABASE_PASSWORD': 'db-pass-456',
        }

        # Initialize the store with custom secrets
        store = SecretStore(custom_secrets=custom_secrets)

        # Verify the custom secrets were added correctly
        assert isinstance(store.custom_secrets, MappingProxyType)
        assert len(store.custom_secrets) == 2
        assert store.custom_secrets['API_KEY'].get_secret_value() == 'api-key-123'
        assert (
            store.custom_secrets['DATABASE_PASSWORD'].get_secret_value()
            == 'db-pass-456'
        )

        # Verify provider_tokens is empty
        assert isinstance(store.provider_tokens, MappingProxyType)
        assert len(store.provider_tokens) == 0

    def test_initializing_with_mixed_types(self):
        """Test initializing the store with mixed types (dict and MappingProxyType)."""
        # Create provider tokens as a dict
        provider_tokens_dict = {
            ProviderType.GITHUB: {'token': 'github-token-123', 'user_id': 'user1'},
        }

        # Create custom secrets as a MappingProxyType
        custom_secrets_dict = {'API_KEY': 'api-key-123'}
        custom_secrets_proxy = MappingProxyType(
            {key: SecretStr(value) for key, value in custom_secrets_dict.items()}
        )

        # Test with dict for provider_tokens and MappingProxyType for custom_secrets
        store1 = SecretStore(
            provider_tokens=provider_tokens_dict, custom_secrets=custom_secrets_proxy
        )

        assert isinstance(store1.provider_tokens, MappingProxyType)
        assert isinstance(store1.custom_secrets, MappingProxyType)
        assert (
            store1.provider_tokens[ProviderType.GITHUB].token.get_secret_value()
            == 'github-token-123'
        )
        assert store1.custom_secrets['API_KEY'].get_secret_value() == 'api-key-123'

        # Test with MappingProxyType for provider_tokens and dict for custom_secrets
        provider_token = ProviderToken(
            token=SecretStr('gitlab-token-456'), user_id='user2'
        )
        provider_tokens_proxy = MappingProxyType({ProviderType.GITLAB: provider_token})

        store2 = SecretStore(
            provider_tokens=provider_tokens_proxy, custom_secrets=custom_secrets_dict
        )

        assert isinstance(store2.provider_tokens, MappingProxyType)
        assert isinstance(store2.custom_secrets, MappingProxyType)
        assert (
            store2.provider_tokens[ProviderType.GITLAB].token.get_secret_value()
            == 'gitlab-token-456'
        )
        assert store2.custom_secrets['API_KEY'].get_secret_value() == 'api-key-123'

    def test_model_copy_update_fields(self):
        """Test using model_copy to update fields without affecting other fields."""
        # Create initial store
        github_token = ProviderToken(
            token=SecretStr('github-token-123'), user_id='user1'
        )
        custom_secret = {'API_KEY': SecretStr('api-key-123')}

        initial_store = SecretStore(
            provider_tokens=MappingProxyType({ProviderType.GITHUB: github_token}),
            custom_secrets=MappingProxyType(custom_secret),
        )

        # Update only provider_tokens
        gitlab_token = ProviderToken(
            token=SecretStr('gitlab-token-456'), user_id='user2'
        )
        updated_provider_tokens = MappingProxyType(
            {ProviderType.GITHUB: github_token, ProviderType.GITLAB: gitlab_token}
        )

        updated_store1 = initial_store.model_copy(
            update={'provider_tokens': updated_provider_tokens}
        )

        # Verify provider_tokens was updated but custom_secrets remains the same
        assert len(updated_store1.provider_tokens) == 2
        assert (
            updated_store1.provider_tokens[ProviderType.GITHUB].token.get_secret_value()
            == 'github-token-123'
        )
        assert (
            updated_store1.provider_tokens[ProviderType.GITLAB].token.get_secret_value()
            == 'gitlab-token-456'
        )
        assert len(updated_store1.custom_secrets) == 1
        assert (
            updated_store1.custom_secrets['API_KEY'].get_secret_value() == 'api-key-123'
        )

        # Update only custom_secrets
        updated_custom_secrets = MappingProxyType(
            {
                'API_KEY': SecretStr('api-key-123'),
                'DATABASE_PASSWORD': SecretStr('db-pass-456'),
            }
        )

        updated_store2 = initial_store.model_copy(
            update={'custom_secrets': updated_custom_secrets}
        )

        # Verify custom_secrets was updated but provider_tokens remains the same
        assert len(updated_store2.provider_tokens) == 1
        assert (
            updated_store2.provider_tokens[ProviderType.GITHUB].token.get_secret_value()
            == 'github-token-123'
        )
        assert len(updated_store2.custom_secrets) == 2
        assert (
            updated_store2.custom_secrets['API_KEY'].get_secret_value() == 'api-key-123'
        )
        assert (
            updated_store2.custom_secrets['DATABASE_PASSWORD'].get_secret_value()
            == 'db-pass-456'
        )

    def test_serialization_with_expose_secrets(self):
        """Test serializing the SecretStore with expose_secrets=True."""
        # Create a store with both provider tokens and custom secrets
        github_token = ProviderToken(
            token=SecretStr('github-token-123'), user_id='user1'
        )
        custom_secrets = {'API_KEY': SecretStr('api-key-123')}

        store = SecretStore(
            provider_tokens=MappingProxyType({ProviderType.GITHUB: github_token}),
            custom_secrets=MappingProxyType(custom_secrets),
        )

        # Test serialization with expose_secrets=True
        serialized_provider_tokens = store.provider_tokens_serializer(
            store.provider_tokens, SerializationInfo(context={'expose_secrets': True})
        )

        serialized_custom_secrets = store.custom_secrets_serializer(
            store.custom_secrets, SerializationInfo(context={'expose_secrets': True})
        )

        # Verify provider tokens are exposed
        assert serialized_provider_tokens['github']['token'] == 'github-token-123'
        assert serialized_provider_tokens['github']['user_id'] == 'user1'

        # Verify custom secrets are exposed
        assert serialized_custom_secrets['API_KEY'] == 'api-key-123'

        # Test serialization with expose_secrets=False (default)
        hidden_provider_tokens = store.provider_tokens_serializer(
            store.provider_tokens, SerializationInfo(context={'expose_secrets': False})
        )

        hidden_custom_secrets = store.custom_secrets_serializer(
            store.custom_secrets, SerializationInfo(context={'expose_secrets': False})
        )

        # Verify provider tokens are hidden
        assert hidden_provider_tokens['github']['token'] != 'github-token-123'
        assert '**' in hidden_provider_tokens['github']['token']

        # Verify custom secrets are hidden
        assert hidden_custom_secrets['API_KEY'] != 'api-key-123'
        assert '**' in hidden_custom_secrets['API_KEY']

    def test_initializing_provider_tokens_with_mixed_value_types(self):
        """Test initializing provider tokens with both plain strings and SecretStr objects."""
        # Create provider tokens with mixed value types
        # Note: The ProviderToken.from_value method only accepts plain strings in the token field
        # when passed as a dictionary, not SecretStr objects
        provider_tokens_dict = {
            ProviderType.GITHUB: {
                'token': 'github-token-123',  # Plain string
                'user_id': 'user1',
            },
            ProviderType.GITLAB: {
                'token': 'gitlab-token-456',  # Also using plain string
                'user_id': 'user2',
            },
        }

        # For the second provider, create a ProviderToken directly
        gitlab_token = ProviderToken(
            token=SecretStr('gitlab-token-456'), user_id='user2'
        )

        # Create a mixed dictionary with both a dict and a ProviderToken object
        mixed_provider_tokens = {
            ProviderType.GITHUB: provider_tokens_dict[ProviderType.GITHUB],  # Dict
            ProviderType.GITLAB: gitlab_token,  # ProviderToken object
        }

        # Initialize the store
        store = SecretStore(provider_tokens=mixed_provider_tokens)

        # Verify all tokens are converted to SecretStr
        assert isinstance(store.provider_tokens, MappingProxyType)
        assert len(store.provider_tokens) == 2

        # Check GitHub token (was plain string in a dict)
        github_token = store.provider_tokens[ProviderType.GITHUB]
        assert isinstance(github_token.token, SecretStr)
        assert github_token.token.get_secret_value() == 'github-token-123'
        assert github_token.user_id == 'user1'

        # Check GitLab token (was a ProviderToken object)
        gitlab_token_result = store.provider_tokens[ProviderType.GITLAB]
        assert isinstance(gitlab_token_result.token, SecretStr)
        assert gitlab_token_result.token.get_secret_value() == 'gitlab-token-456'
        assert gitlab_token_result.user_id == 'user2'

    def test_initializing_custom_secrets_with_mixed_value_types(self):
        """Test initializing custom secrets with both plain strings and SecretStr objects."""
        # Create custom secrets with mixed value types
        custom_secrets_dict = {
            'API_KEY': 'api-key-123',  # Plain string
            'DATABASE_PASSWORD': SecretStr('db-pass-456'),  # SecretStr
        }

        # Initialize the store
        store = SecretStore(custom_secrets=custom_secrets_dict)

        # Verify all secrets are converted to SecretStr
        assert isinstance(store.custom_secrets, MappingProxyType)
        assert len(store.custom_secrets) == 2

        # Check API_KEY (was plain string)
        assert isinstance(store.custom_secrets['API_KEY'], SecretStr)
        assert store.custom_secrets['API_KEY'].get_secret_value() == 'api-key-123'

        # Check DATABASE_PASSWORD (was SecretStr)
        assert isinstance(store.custom_secrets['DATABASE_PASSWORD'], SecretStr)
        assert (
            store.custom_secrets['DATABASE_PASSWORD'].get_secret_value()
            == 'db-pass-456'
        )


# Mock class for SerializationInfo since it's not directly importable
class SerializationInfo:
    def __init__(self, context: dict[str, Any] | None = None):
        self.context = context or {}
