"""Tests for the Brave Search functionality."""

from unittest.mock import Mock, patch

import pytest

from openhands.core.config import AppConfig, SearchConfig
from openhands.events.action import SearchAction
from openhands.events.observation.error import ErrorObservation
from openhands.events.observation.search_engine import SearchEngineObservation
from openhands.runtime.search_engine.brave_search import search


@pytest.fixture
def mock_config():
    """Create a mock config with search enabled."""
    config = AppConfig()
    config.search = SearchConfig(
        enabled=True,
        api_key="test_key",
        api_url="https://test.url"
    )
    return config


@pytest.fixture
def mock_query_api():
    """Create a mock query_api function."""
    with patch("openhands.runtime.search_engine.brave_search.query_api") as mock:
        mock.return_value = SearchEngineObservation(
            query="test query",
            content="test content"
        )
        yield mock


def test_search_disabled(mock_query_api):
    """Test that search returns error when disabled."""
    config = AppConfig()
    config.search = SearchConfig(enabled=False)
    action = SearchAction(query="test query")

    result = search(action, config)
    assert isinstance(result, ErrorObservation)
    assert "not enabled" in result.content
    mock_query_api.assert_not_called()


def test_search_no_api_key(mock_query_api):
    """Test that search returns error when API key is not set."""
    config = AppConfig()
    config.search = SearchConfig(enabled=True)
    action = SearchAction(query="test query")

    result = search(action, config)
    assert isinstance(result, ErrorObservation)
    assert "API key not configured" in result.content
    mock_query_api.assert_not_called()


def test_search_empty_query(mock_query_api, mock_config):
    """Test that search returns error when query is empty."""
    action = SearchAction(query="")

    result = search(action, mock_config)
    assert isinstance(result, ErrorObservation)
    assert "must be a non-empty string" in result.content
    mock_query_api.assert_not_called()


def test_search_success(mock_query_api, mock_config):
    """Test that search returns results when everything is configured correctly."""
    action = SearchAction(query="test query")

    result = search(action, mock_config)
    assert isinstance(result, SearchEngineObservation)
    assert result.query == "test query"
    assert result.content == "test content"
    mock_query_api.assert_called_once_with(
        query="test query",
        API_KEY="test_key",
        BRAVE_SEARCH_URL="https://test.url"
    )