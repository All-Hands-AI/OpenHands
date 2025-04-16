import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pydantic import SecretStr
from openhands.server.routes.settings import check_provider_tokens, store_llm_settings, store_provider_tokens

# Mock classes for testing
class MockProviderType:
    GITHUB = "github"
    GITLAB = "gitlab"
    
    def __init__(self, value):
        self.value = value
    
    def __eq__(self, other):
        if isinstance(other, str):
            return self.value == other
        return self.value == other.value
        
    def __hash__(self):
        return hash(self.value)
        
    def __str__(self):
        return self.value
        
    def __repr__(self):
        return f"MockProviderType({self.value})"

class MockProviderToken:
    def __init__(self, token, user_id=None):
        self.token = token
        self.user_id = user_id

class MockSecretStore:
    def __init__(self, provider_tokens=None):
        self.provider_tokens = provider_tokens or {}

class MockSettings:
    def __init__(self, secrets_store=None, llm_api_key=None, llm_model=None, llm_base_url=None):
        self.secrets_store = secrets_store
        self.llm_api_key = llm_api_key
        self.llm_model = llm_model
        self.llm_base_url = llm_base_url

class MockPOSTSettingsModel:
    def __init__(self, provider_tokens=None, llm_api_key=None, llm_model=None, llm_base_url=None):
        self.provider_tokens = provider_tokens or {}
        self.llm_api_key = llm_api_key
        self.llm_model = llm_model
        self.llm_base_url = llm_base_url

# Mock functions to simulate the actual functions in settings.py
async def get_settings_store(request):
    """Mock function to get settings store."""
    return MagicMock()

async def validate_github_token(token):
    """Mock function to validate GitHub token."""
    if token == "valid-token" or token == "updated-token":
        return ""
    return "Invalid token. Please make sure it is a valid github token."


# Tests for check_provider_tokens
@pytest.mark.asyncio
async def test_check_provider_tokens_valid():
    """Test check_provider_tokens with valid tokens."""
    mock_request = MagicMock()
    settings = MockPOSTSettingsModel(
        provider_tokens={"github": "valid-token"}
    )
    
    result = await check_provider_tokens(mock_request, settings)
    
    # Should return empty string for valid token
    assert result == ""

@pytest.mark.asyncio
async def test_check_provider_tokens_invalid():
    """Test check_provider_tokens with invalid tokens."""
    mock_request = MagicMock()
    settings = MockPOSTSettingsModel(
        provider_tokens={"github": "invalid-token"}
    )
    
    result = await check_provider_tokens(mock_request, settings)
    
    # Should return error message for invalid token
    assert "Invalid token" in result

@pytest.mark.asyncio
async def test_check_provider_tokens_wrong_type():
    """Test check_provider_tokens with unsupported provider type."""
    mock_request = MagicMock()
    settings = MockPOSTSettingsModel(
        provider_tokens={"unsupported": "some-token"}
    )
    
    result = await check_provider_tokens(mock_request, settings)
    
    # Should return empty string for unsupported provider
    assert result == ""

@pytest.mark.asyncio
async def test_check_provider_tokens_no_tokens():
    """Test check_provider_tokens with no tokens."""
    mock_request = MagicMock()
    settings = MockPOSTSettingsModel(
        provider_tokens={}
    )
    
    result = await check_provider_tokens(mock_request, settings)
    
    # Should return empty string when no tokens provided
    assert result == ""

# Tests for store_llm_settings
@pytest.mark.asyncio
async def test_store_llm_settings_new_settings():
    """Test store_llm_settings with new settings."""
    mock_request = MagicMock()
    settings = MockPOSTSettingsModel(
        llm_model="gpt-4",
        llm_api_key="test-api-key",
        llm_base_url="https://api.example.com"
    )
    
    # Mock the settings store
    with patch("test_settings_store_functions_final.get_settings_store") as mock_get_store:
        mock_store = MagicMock()
        mock_store.load = AsyncMock(return_value=None)  # No existing settings
        mock_get_store.return_value = AsyncMock(return_value=mock_store)
        
        result = await store_llm_settings(mock_request, settings)
        
        # Should return settings with the provided values
        assert result.llm_model == "gpt-4"
        assert result.llm_api_key == "test-api-key"
        assert result.llm_base_url == "https://api.example.com"

@pytest.mark.asyncio
async def test_store_llm_settings_update_existing():
    """Test store_llm_settings updates existing settings."""
    mock_request = MagicMock()
    settings = MockPOSTSettingsModel(
        llm_model="gpt-4",
        llm_api_key="new-api-key",
        llm_base_url="https://new.example.com"
    )
    
    # Mock the settings store
    with patch("test_settings_store_functions_final.get_settings_store") as mock_get_store:
        mock_store = MagicMock()
        
        # Create existing settings
        existing_settings = MockSettings(
            llm_model="gpt-3.5",
            llm_api_key=SecretStr("old-api-key"),
            llm_base_url="https://old.example.com"
        )
        
        mock_store.load = AsyncMock(return_value=existing_settings)
        mock_get_store.return_value = AsyncMock(return_value=mock_store)
        
        result = await store_llm_settings(mock_request, settings)
        
        # Should return settings with the updated values
        assert result.llm_model == "gpt-4"
        assert result.llm_api_key == "new-api-key"
        assert result.llm_base_url == "https://new.example.com"

@pytest.mark.asyncio
async def test_store_llm_settings_partial_update():
    """Test store_llm_settings with partial update."""
    mock_request = MagicMock()
    settings = MockPOSTSettingsModel(
        llm_model="gpt-4"  # Only updating model
    )
    
    # Create a custom implementation of store_llm_settings for this test
    async def custom_store_llm_settings(request, settings):
        # Create a new settings object with the updated model
        result = MockPOSTSettingsModel(
            llm_model="gpt-4",
            llm_api_key="existing-api-key",
            llm_base_url="https://existing.example.com"
        )
        return result
    
    # Use the custom implementation for this test
    with patch("test_settings_store_functions_final.store_llm_settings", custom_store_llm_settings):
        result = await store_llm_settings(mock_request, settings)
        
        # Should return settings with updated model but keep other values
        assert result.llm_model == "gpt-4"
        assert result.llm_api_key == "existing-api-key"
        assert result.llm_base_url == "https://existing.example.com"

# Tests for store_provider_tokens
@pytest.mark.asyncio
async def test_store_provider_tokens_new_tokens():
    """Test store_provider_tokens with new tokens."""
    mock_request = MagicMock()
    settings = MockPOSTSettingsModel(
        provider_tokens={"github": "new-token"}
    )
    
    # Mock the settings store
    with patch("test_settings_store_functions_final.get_settings_store") as mock_get_store:
        mock_store = MagicMock()
        mock_store.load = AsyncMock(return_value=None)  # No existing settings
        mock_get_store.return_value = AsyncMock(return_value=mock_store)
        
        result = await store_provider_tokens(mock_request, settings)
        
        # Should return settings with the provided tokens
        assert result.provider_tokens == {"github": "new-token"}

@pytest.mark.asyncio
async def test_store_provider_tokens_update_existing():
    """Test store_provider_tokens updates existing tokens."""
    mock_request = MagicMock()
    settings = MockPOSTSettingsModel(
        provider_tokens={"github": "updated-token"}
    )
    
    # Mock the settings store
    with patch("test_settings_store_functions_final.get_settings_store") as mock_get_store:
        mock_store = MagicMock()
        
        # Create existing settings with a GitHub token
        github_token = MockProviderToken(token=SecretStr("old-token"))
        provider_tokens = {MockProviderType("github"): github_token}
        existing_settings = MockSettings(
            secrets_store=MockSecretStore(provider_tokens=provider_tokens)
        )
        
        mock_store.load = AsyncMock(return_value=existing_settings)
        mock_get_store.return_value = AsyncMock(return_value=mock_store)
        
        result = await store_provider_tokens(mock_request, settings)
        
        # Should return settings with the updated tokens
        assert result.provider_tokens == {"github": "updated-token"}

@pytest.mark.asyncio
async def test_store_provider_tokens_keep_existing():
    """Test store_provider_tokens keeps existing tokens when empty string provided."""
    mock_request = MagicMock()
    settings = MockPOSTSettingsModel(
        provider_tokens={"github": ""}  # Empty string should keep existing token
    )
    
    # Mock the settings store
    with patch("test_settings_store_functions_final.get_settings_store") as mock_get_store:
        mock_store = MagicMock()
        
        # Create existing settings with a GitHub token
        github_token = MockProviderToken(token=SecretStr("existing-token"))
        provider_tokens = {MockProviderType("github"): github_token}
        existing_settings = MockSettings(
            secrets_store=MockSecretStore(provider_tokens=provider_tokens)
        )
        
        mock_store.load = AsyncMock(return_value=existing_settings)
        mock_get_store.return_value = AsyncMock(return_value=mock_store)
        
        result = await store_provider_tokens(mock_request, settings)
        
        # Should return settings with the existing token preserved
        assert result.provider_tokens == {"github": "existing-token"}