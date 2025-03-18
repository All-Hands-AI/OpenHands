import pytest
from pydantic import SecretStr, ValidationError

from openhands.integrations.provider import ProviderToken, ProviderType, SecretStore
from openhands.server.settings import Settings, POSTSettingsModel


def test_provider_token_immutability():
    """Test that ProviderToken is immutable"""
    token = ProviderToken(token=SecretStr("test"), user_id="user1")
    
    # These should raise ValidationError
    with pytest.raises(ValidationError):
        token.token = SecretStr("new")
    
    with pytest.raises(ValidationError):
        token.user_id = "new_user"


def test_secret_store_immutability():
    """Test that SecretStore is immutable"""
    store = SecretStore.create({
        ProviderType.GITHUB: ProviderToken(token=SecretStr("test"))
    })
    
    # These should raise ValidationError due to frozen field
    with pytest.raises(ValidationError):
        store.provider_tokens = {}
    
    # The token itself should be immutable
    with pytest.raises(ValidationError):
        store.provider_tokens[ProviderType.GITHUB].token = SecretStr("new")
    
    # Verify the original token is unchanged
    assert store.provider_tokens[ProviderType.GITHUB].token.get_secret_value() == "test"


def test_settings_token_updates():
    """Test that Settings handles token updates immutably"""
    # Create initial settings
    settings = Settings(
        secrets_store=SecretStore.create({
            ProviderType.GITHUB: ProviderToken(token=SecretStr("initial"))
        })
    )
    
    # Update token
    new_settings = settings.with_updated_provider_token(
        ProviderType.GITHUB,
        "new_token",
        "user1"
    )
    
    # Original settings should be unchanged
    assert settings.secrets_store.provider_tokens[ProviderType.GITHUB].token.get_secret_value() == "initial"
    assert settings.secrets_store.provider_tokens[ProviderType.GITHUB].user_id is None
    
    # New settings should have updated token
    assert new_settings.secrets_store.provider_tokens[ProviderType.GITHUB].token.get_secret_value() == "new_token"
    assert new_settings.secrets_store.provider_tokens[ProviderType.GITHUB].user_id == "user1"


def test_post_settings_model():
    """Test that POSTSettingsModel correctly handles token updates"""
    # Create initial settings
    current_settings = Settings(
        secrets_store=SecretStore.create({
            ProviderType.GITHUB: ProviderToken(token=SecretStr("initial"))
        })
    )
    
    # Create POST model with updates
    post_data = POSTSettingsModel(
        provider_tokens={
            "github": {"token": "new_token", "user_id": "user1"},
            "gitlab": "gitlab_token"
        }
    )
    
    # Convert to settings
    new_settings = post_data.to_settings(current_settings)
    
    # Original settings should be unchanged
    assert current_settings.secrets_store.provider_tokens[ProviderType.GITHUB].token.get_secret_value() == "initial"
    
    # New settings should have updated tokens
    assert new_settings.secrets_store.provider_tokens[ProviderType.GITHUB].token.get_secret_value() == "new_token"
    assert new_settings.secrets_store.provider_tokens[ProviderType.GITHUB].user_id == "user1"
    assert new_settings.secrets_store.provider_tokens[ProviderType.GITLAB].token.get_secret_value() == "gitlab_token"


def test_provider_handler_immutability():
    """Test that ProviderHandler maintains token immutability"""
    from openhands.integrations.provider import ProviderHandler
    
    # Create initial tokens
    tokens = {
        ProviderType.GITHUB: ProviderToken(token=SecretStr("test"))
    }
    
    handler = ProviderHandler(tokens, None)
    
    # Try to modify tokens (should raise TypeError due to frozen dict)
    with pytest.raises((TypeError, AttributeError)):
        handler.provider_tokens[ProviderType.GITHUB] = ProviderToken(token=SecretStr("new"))
    
    # Try to modify the handler's tokens property
    with pytest.raises((ValidationError, TypeError, AttributeError)):
        handler.provider_tokens = {}
    
    # Original token should be unchanged
    assert handler.provider_tokens[ProviderType.GITHUB].token.get_secret_value() == "test"


def test_token_conversion():
    """Test token conversion in SecretStore.create"""
    # Test with string token
    store1 = SecretStore.create({
        ProviderType.GITHUB: "test_token"
    })
    assert store1.provider_tokens[ProviderType.GITHUB].token.get_secret_value() == "test_token"
    
    # Test with dict token
    store2 = SecretStore.create({
        ProviderType.GITHUB: {"token": "test_token", "user_id": "user1"}
    })
    assert store2.provider_tokens[ProviderType.GITHUB].token.get_secret_value() == "test_token"
    assert store2.provider_tokens[ProviderType.GITHUB].user_id == "user1"
    
    # Test with SecretStr token
    store3 = SecretStore.create({
        ProviderType.GITHUB: SecretStr("test_token")
    })
    assert store3.provider_tokens[ProviderType.GITHUB].token.get_secret_value() == "test_token"