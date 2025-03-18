from unittest.mock import patch

import pytest
from pydantic import SecretStr

from openhands.core.config import AppConfig
from openhands.core.config.search_config import SearchConfig
from openhands.events.action import SearchAction
from openhands.events.observation.error import ErrorObservation
from openhands.events.observation.search_engine import SearchEngineObservation
from openhands.runtime.search_engine.brave_search import search


def test_search_config_defaults():
    """Test that SearchConfig has the expected default values."""
    config = SearchConfig()
    assert config.brave_api_key is None
    assert config.brave_api_url == 'https://api.search.brave.com/res/v1/web/search'


def test_search_config_in_app_config():
    """Test that SearchConfig is properly integrated into AppConfig."""
    app_config = AppConfig()
    assert isinstance(app_config.search, SearchConfig)
    assert app_config.search.brave_api_key is None
    assert app_config.search.brave_api_url == 'https://api.search.brave.com/res/v1/web/search'


def test_search_with_empty_query():
    """Test that search returns an error for empty queries."""
    action = SearchAction(query='')
    result = search(action)
    assert isinstance(result, ErrorObservation)
    assert 'must be a non-empty string' in result.content


def test_search_with_missing_api_key():
    """Test that search raises an error when API key is not configured."""
    action = SearchAction(query='test query')
    
    # Mock the config to ensure brave_api_key is None
    mock_config = AppConfig()
    mock_config.search.brave_api_key = None
    
    with patch('openhands.core.config.load_app_config', return_value=mock_config):
        with pytest.raises(ValueError) as exc_info:
            search(action)
        assert 'Brave Search API key not set in configuration' in str(exc_info.value)


def test_search_with_valid_config(requests_mock):
    """Test that search works correctly with valid configuration."""
    action = SearchAction(query='test query')
    
    # Mock the config with a valid API key
    mock_config = AppConfig()
    mock_config.search.brave_api_key = SecretStr('test-api-key')
    
    # Mock the Brave Search API response
    mock_response = {
        'web': {
            'results': [
                {
                    'title': 'Test Result',
                    'url': 'https://example.com',
                    'description': 'Test description'
                }
            ]
        }
    }
    requests_mock.get(
        mock_config.search.brave_api_url,
        json=mock_response
    )
    
    with patch('openhands.core.config.load_app_config', return_value=mock_config):
        result = search(action)
        assert isinstance(result, SearchEngineObservation)
        assert 'Test Result' in result.content
        assert 'https://example.com' in result.content
        assert 'Test description' in result.content