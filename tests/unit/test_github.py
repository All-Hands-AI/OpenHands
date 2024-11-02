import time
from unittest.mock import MagicMock, patch

import pytest

from openhands.server.github import UserVerifier, CACHE_TTL


def test_user_verifier_singleton():
    """Test that UserVerifier is a singleton"""
    verifier1 = UserVerifier()
    verifier2 = UserVerifier()
    assert verifier1 is verifier2


@patch('openhands.server.sheets_client.GoogleSheetsClient')
def test_sheet_caching(mock_sheets_client):
    """Test that sheet data is cached and only refreshed after TTL"""
    # Setup mock
    mock_instance = MagicMock()
    mock_instance.get_usernames.return_value = ['user1', 'user2']
    mock_sheets_client.return_value = mock_instance

    # Create verifier with mocked sheets client
    verifier = UserVerifier()
    verifier.spreadsheet_id = 'test-sheet-id'
    verifier.sheets_client = mock_instance
    verifier.cached_sheet_users = None
    verifier.last_fetch_time = 0

    # First check should fetch and cache
    verifier.is_user_allowed('user1')
    assert mock_instance.get_usernames.call_count == 1
    assert verifier.cached_sheet_users == ['user1', 'user2']
    first_call_time = verifier.last_fetch_time

    # Immediate second check should use cache
    verifier.is_user_allowed('user2')
    assert mock_instance.get_usernames.call_count == 1  # Still 1
    assert verifier.last_fetch_time == first_call_time

    # Move time forward past TTL
    verifier.last_fetch_time = time.time() - (CACHE_TTL + 1)

    # Check should refresh cache
    verifier.is_user_allowed('user1')
    assert mock_instance.get_usernames.call_count == 2  # Increased to 2


@patch('openhands.server.sheets_client.GoogleSheetsClient')
def test_user_verification_with_cache(mock_sheets_client):
    """Test that user verification works correctly with caching"""
    # Setup mock
    mock_instance = MagicMock()
    mock_instance.get_usernames.return_value = ['allowed_user']
    mock_sheets_client.return_value = mock_instance

    # Create verifier with mocked sheets client
    verifier = UserVerifier()
    verifier.spreadsheet_id = 'test-sheet-id'
    verifier.sheets_client = mock_instance
    verifier.cached_sheet_users = None
    verifier.last_fetch_time = 0

    # Test allowed user
    assert verifier.is_user_allowed('allowed_user') is True
    assert mock_instance.get_usernames.call_count == 1

    # Test disallowed user using cache
    assert verifier.is_user_allowed('disallowed_user') is False
    assert mock_instance.get_usernames.call_count == 1  # Still 1, using cache
