import pytest
import requests
from unittest.mock import patch, MagicMock

from openhands.resolver.issue_definitions import PRHandler
from openhands.resolver.github_issue import ReviewThread


def test_handle_nonexistent_issue_reference():
    handler = PRHandler("test-owner", "test-repo", "test-token")
    
    # Mock the requests.get to simulate a 404 error
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Client Error: Not Found")
    
    with patch('requests.get', return_value=mock_response):
        # Call the method with a non-existent issue reference
        result = handler._PRHandler__get_context_from_external_issues_references(
            closing_issues=[],
            closing_issue_numbers=[],
            issue_body="This references #999999",  # Non-existent issue
            review_comments=[],
            review_threads=[],
            thread_comments=None
        )
        
        # The method should return an empty list since the referenced issue couldn't be fetched
        assert result == []


def test_handle_rate_limit_error():
    handler = PRHandler("test-owner", "test-repo", "test-token")
    
    # Mock the requests.get to simulate a rate limit error
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
        "403 Client Error: Rate Limit Exceeded"
    )
    
    with patch('requests.get', return_value=mock_response):
        # Call the method with an issue reference
        result = handler._PRHandler__get_context_from_external_issues_references(
            closing_issues=[],
            closing_issue_numbers=[],
            issue_body="This references #123",
            review_comments=[],
            review_threads=[],
            thread_comments=None
        )
        
        # The method should return an empty list since the request was rate limited
        assert result == []


def test_handle_network_error():
    handler = PRHandler("test-owner", "test-repo", "test-token")
    
    # Mock the requests.get to simulate a network error
    with patch('requests.get', side_effect=requests.exceptions.ConnectionError("Network Error")):
        # Call the method with an issue reference
        result = handler._PRHandler__get_context_from_external_issues_references(
            closing_issues=[],
            closing_issue_numbers=[],
            issue_body="This references #123",
            review_comments=[],
            review_threads=[],
            thread_comments=None
        )
        
        # The method should return an empty list since the network request failed
        assert result == []


def test_successful_issue_reference():
    handler = PRHandler("test-owner", "test-repo", "test-token")
    
    # Mock a successful response
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"body": "This is the referenced issue body"}
    
    with patch('requests.get', return_value=mock_response):
        # Call the method with an issue reference
        result = handler._PRHandler__get_context_from_external_issues_references(
            closing_issues=[],
            closing_issue_numbers=[],
            issue_body="This references #123",
            review_comments=[],
            review_threads=[],
            thread_comments=None
        )
        
        # The method should return a list with the referenced issue body
        assert result == ["This is the referenced issue body"]