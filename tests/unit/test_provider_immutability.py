from types import MappingProxyType

import pytest
from pydantic import SecretStr, ValidationError

from openhands.integrations.provider import (
    ProviderHandler,
    ProviderToken,
    ProviderType,
    SecretStore,
)
from openhands.server.routes.settings import convert_to_settings
from openhands.server.settings import POSTSettingsModel, Settings


def test_provider_token_immutability():
    """Test that ProviderToken is immutable"""
    token = ProviderToken(token=SecretStr('test'), user_id='user1')

    # Test direct attribute modification
    with pytest.raises(ValidationError):
        token.token = SecretStr('new')

    with pytest.raises(ValidationError):
        token.user_id = 'new_user'

    # Test that __setattr__ is blocked
    with pytest.raises(ValidationError):
        setattr(token, 'token', SecretStr('new'))

    # Verify original values are unchanged
    assert token.token.get_secret_value() == 'test'
    assert token.user_id == 'user1'


def test_secret_store_immutability():
    """Test that SecretStore is immutable"""
    store = SecretStore(
        provider_tokens={ProviderType.GITHUB: ProviderToken(token=SecretStr('test'))}
    )

    # Test direct attribute modification
    with pytest.raises(ValidationError):
        store.provider_tokens = {}

    # Test dictionary mutation attempts
    with pytest.raises((TypeError, AttributeError)):
        store.provider_tokens[ProviderType.GITHUB] = ProviderToken(
            token=SecretStr('new')
        )

    with pytest.raises((TypeError, AttributeError)):
        store.provider_tokens.clear()

    with pytest.raises((TypeError, AttributeError)):
        store.provider_tokens.update(
            {ProviderType.GITLAB: ProviderToken(token=SecretStr('test'))}
        )

    # Test nested immutability
    github_token = store.provider_tokens[ProviderType.GITHUB]
    with pytest.raises(ValidationError):
        github_token.token = SecretStr('new')

    # Verify original values are unchanged
    assert store.provider_tokens[ProviderType.GITHUB].token.get_secret_value() == 'test'


def test_settings_immutability():
    """Test that Settings secrets_store is immutable"""
    settings = Settings(
        secrets_store=SecretStore(
            provider_tokens={
                ProviderType.GITHUB: ProviderToken(token=SecretStr('test'))
            }
        )
    )

    # Test direct modification of secrets_store
    with pytest.raises(ValidationError):
        settings.secrets_store = SecretStore()

    # Test nested modification attempts
    with pytest.raises((TypeError, AttributeError)):
        settings.secrets_store.provider_tokens[ProviderType.GITHUB] = ProviderToken(
            token=SecretStr('new')
        )

    # Test model_copy creates new instance
    new_store = SecretStore(
        provider_tokens={
            ProviderType.GITHUB: ProviderToken(token=SecretStr('new_token'))
        }
    )
    new_settings = settings.model_copy(update={'secrets_store': new_store})

    # Verify original is unchanged and new has updated values
    assert (
        settings.secrets_store.provider_tokens[
            ProviderType.GITHUB
        ].token.get_secret_value()
        == 'test'
    )
    assert (
        new_settings.secrets_store.provider_tokens[
            ProviderType.GITHUB
        ].token.get_secret_value()
        == 'new_token'
    )

    with pytest.raises(ValidationError):
        new_settings.secrets_store.provider_tokens[
            ProviderType.GITHUB
        ].token = SecretStr('')


def test_post_settings_conversion():
    """Test that POSTSettingsModel correctly converts to Settings"""
    # Create POST model with token data
    post_data = POSTSettingsModel(
        provider_tokens={'github': 'test_token', 'gitlab': 'gitlab_token'}
    )

    # Convert to settings using convert_to_settings function
    settings = convert_to_settings(post_data)

    # Verify tokens were converted correctly
    assert (
        settings.secrets_store.provider_tokens[
            ProviderType.GITHUB
        ].token.get_secret_value()
        == 'test_token'
    )
    assert (
        settings.secrets_store.provider_tokens[
            ProviderType.GITLAB
        ].token.get_secret_value()
        == 'gitlab_token'
    )
    assert settings.secrets_store.provider_tokens[ProviderType.GITLAB].user_id is None

    # Verify immutability of converted settings
    with pytest.raises(ValidationError):
        settings.secrets_store = SecretStore()


def test_provider_handler_immutability():
    """Test that ProviderHandler maintains token immutability"""

    # Create initial tokens
    tokens = MappingProxyType(
        {ProviderType.GITHUB: ProviderToken(token=SecretStr('test'))}
    )

    handler = ProviderHandler(provider_tokens=tokens)

    # Try to modify tokens (should raise TypeError due to frozen dict)
    with pytest.raises((TypeError, AttributeError)):
        handler.provider_tokens[ProviderType.GITHUB] = ProviderToken(
            token=SecretStr('new')
        )

    # Try to modify the handler's tokens property
    with pytest.raises((ValidationError, TypeError, AttributeError)):
        handler.provider_tokens = {}

    # Original token should be unchanged
    assert (
        handler.provider_tokens[ProviderType.GITHUB].token.get_secret_value() == 'test'
    )


def test_token_conversion():
    """Test token conversion in SecretStore.create"""
    # Test with string token
    store1 = Settings(
        secrets_store=SecretStore(
            provider_tokens={
                ProviderType.GITHUB: ProviderToken(token=SecretStr('test_token'))
            }
        )
    )

    assert (
        store1.secrets_store.provider_tokens[
            ProviderType.GITHUB
        ].token.get_secret_value()
        == 'test_token'
    )
    assert store1.secrets_store.provider_tokens[ProviderType.GITHUB].user_id is None

    # Test with dict token
    store2 = SecretStore(
        provider_tokens={'github': {'token': 'test_token', 'user_id': 'user1'}}
    )
    assert (
        store2.provider_tokens[ProviderType.GITHUB].token.get_secret_value()
        == 'test_token'
    )
    assert store2.provider_tokens[ProviderType.GITHUB].user_id == 'user1'

    # Test with ProviderToken
    token = ProviderToken(token=SecretStr('test_token'), user_id='user2')
    store3 = SecretStore(provider_tokens={ProviderType.GITHUB: token})
    assert (
        store3.provider_tokens[ProviderType.GITHUB].token.get_secret_value()
        == 'test_token'
    )
    assert store3.provider_tokens[ProviderType.GITHUB].user_id == 'user2'

    store4 = SecretStore(
        provider_tokens={
            ProviderType.GITHUB: 123  # Invalid type
        }
    )

    assert ProviderType.GITHUB not in store4.provider_tokens

    # Test with empty/None token
    store5 = SecretStore(provider_tokens={ProviderType.GITHUB: None})
    assert ProviderType.GITHUB not in store5.provider_tokens

    store6 = SecretStore(
        provider_tokens={
            'invalid_provider': 'test_token'  # Invalid provider type
        }
    )

    assert len(store6.provider_tokens.keys()) == 0
