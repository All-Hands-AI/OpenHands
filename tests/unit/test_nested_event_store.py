"""
Unit tests for the NestedEventStore class.

These tests focus on the search_events method, which retrieves events from a remote API
and applies filtering based on various criteria.
"""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from openhands.events.action import MessageAction
from openhands.events.event import EventSource
from openhands.events.event_filter import EventFilter
from openhands.events.nested_event_store import NestedEventStore


def create_mock_event(
    id: int, content: str, source: str = 'user', hidden: bool = False
) -> dict[str, Any]:
    """Create a properly formatted mock event dictionary."""
    event_dict = {
        'id': id,
        'action': 'message',  # This is required for the event_from_dict function
        'args': {
            'content': content,
        },
        'source': source,
    }

    # Add hidden as a property that will be set on the event after deserialization
    if hidden:
        event_dict['hidden'] = True

    return event_dict


def create_mock_response(
    events: list[dict[str, Any]], has_more: bool = False
) -> MagicMock:
    """Helper function to create a mock HTTP response."""
    mock_response = MagicMock()
    mock_response.json.return_value = {'events': events, 'has_more': has_more}
    return mock_response


class TestNestedEventStore:
    """Tests for the NestedEventStore class."""

    @pytest.fixture
    def event_store(self):
        """Create a NestedEventStore instance for testing."""
        return NestedEventStore(
            base_url='http://test-api.example.com',
            sid='test-session',
            user_id='test-user',
            session_api_key='test-api-key',
        )

    @patch('httpx.get')
    def test_search_events_basic(self, mock_get, event_store):
        """Test basic event retrieval without filters."""
        # Setup mock response with two events
        mock_events = [
            create_mock_event(1, 'Hello', 'user'),
            create_mock_event(2, 'World', 'agent'),
        ]
        mock_get.return_value = create_mock_response(mock_events)

        # Call the method
        events = list(event_store.search_events())

        # Verify the results
        assert len(events) == 2
        assert events[0].id == 1
        assert events[1].id == 2

        # Verify the API call
        mock_get.assert_called_once_with(
            'http://test-api.example.com/events?start_id=0&reverse=False',
            headers={'X-Session-API-Key': 'test-api-key'},
        )

    @patch('httpx.get')
    def test_search_events_with_limit(self, mock_get, event_store):
        """Test event retrieval with a limit."""
        # Setup mock response
        mock_events = [
            create_mock_event(1, 'Hello', 'user'),
            create_mock_event(2, 'World', 'agent'),
        ]
        mock_get.return_value = create_mock_response(mock_events)

        # Call the method with a limit
        events = list(event_store.search_events(limit=1))

        # Verify the results
        assert len(events) == 1
        assert events[0].id == 1

        # Verify the API call includes the limit parameter
        mock_get.assert_called_once_with(
            'http://test-api.example.com/events?start_id=0&reverse=False&limit=1',
            headers={'X-Session-API-Key': 'test-api-key'},
        )

    @patch('httpx.get')
    def test_search_events_with_start_id(self, mock_get, event_store):
        """Test event retrieval with a specific start_id."""
        # Setup mock response
        mock_events = [
            create_mock_event(5, 'Hello', 'user'),
            create_mock_event(6, 'World', 'agent'),
        ]
        mock_get.return_value = create_mock_response(mock_events)

        # Call the method with a start_id
        events = list(event_store.search_events(start_id=5))

        # Verify the results
        assert len(events) == 2
        assert events[0].id == 5
        assert events[1].id == 6

        # Verify the API call includes the correct start_id
        mock_get.assert_called_once_with(
            'http://test-api.example.com/events?start_id=5&reverse=False',
            headers={'X-Session-API-Key': 'test-api-key'},
        )

    @patch('httpx.get')
    def test_search_events_reverse_order(self, mock_get, event_store):
        """Test event retrieval in reverse order."""
        # Setup mock response
        mock_events = [
            create_mock_event(3, 'World', 'agent'),
            create_mock_event(2, 'Hello', 'user'),
        ]
        mock_get.return_value = create_mock_response(mock_events)

        # Call the method with reverse=True
        events = list(event_store.search_events(reverse=True))

        # Verify the results
        assert len(events) == 2
        assert events[0].id == 3
        assert events[1].id == 2

        # Verify the API call includes reverse=True
        mock_get.assert_called_once_with(
            'http://test-api.example.com/events?start_id=0&reverse=True',
            headers={'X-Session-API-Key': 'test-api-key'},
        )

    @patch('httpx.get')
    def test_search_events_with_end_id(self, mock_get, event_store):
        """Test event retrieval with a specific end_id."""
        # Setup mock response
        mock_events = [
            create_mock_event(1, 'Hello', 'user'),
            create_mock_event(2, 'World', 'agent'),
            create_mock_event(3, 'End', 'user'),
        ]
        mock_get.return_value = create_mock_response(mock_events)

        # Call the method with an end_id
        events = list(event_store.search_events(end_id=3))

        # Verify the results
        assert len(events) == 3
        assert events[0].id == 1
        assert events[1].id == 2
        assert events[2].id == 3

        # Verify the API call
        mock_get.assert_called_once_with(
            'http://test-api.example.com/events?start_id=0&reverse=False',
            headers={'X-Session-API-Key': 'test-api-key'},
        )

    @patch('httpx.get')
    @patch('openhands.events.event_filter.EventFilter.exclude')
    def test_search_events_with_filter(self, mock_exclude, mock_get, event_store):
        """Test event retrieval with an EventFilter."""
        # Setup mock response with mixed events
        mock_events = [
            create_mock_event(1, 'Hello', 'user'),
            create_mock_event(2, 'World', 'agent'),
            create_mock_event(3, 'Hidden', 'user'),
        ]
        mock_get.return_value = create_mock_response(mock_events)

        # Configure the mock to exclude the third event (simulating exclude_hidden=True)
        # Return True for the third event (to exclude it) and False for others
        mock_exclude.side_effect = [False, False, True]

        # Create a filter (the actual implementation doesn't matter since we're mocking exclude)
        event_filter = EventFilter()

        # Call the method with the filter
        events = list(event_store.search_events(filter=event_filter))

        # Verify the results (should exclude the third event)
        assert len(events) == 2
        assert events[0].id == 1
        assert events[1].id == 2

        # Verify the API call
        mock_get.assert_called_once_with(
            'http://test-api.example.com/events?start_id=0&reverse=False',
            headers={'X-Session-API-Key': 'test-api-key'},
        )

    @patch('httpx.get')
    def test_search_events_with_source_filter(self, mock_get, event_store):
        """Test event retrieval with a source filter."""
        # Setup mock response with mixed sources
        mock_events = [
            create_mock_event(1, 'Hello', 'user'),
            create_mock_event(2, 'World', 'agent'),
            create_mock_event(3, 'Another', 'user'),
        ]
        mock_get.return_value = create_mock_response(mock_events)

        # Create a filter to include only user events
        event_filter = EventFilter(source='user')

        # Call the method with the filter
        events = list(event_store.search_events(filter=event_filter))

        # Verify the results (should only include user events)
        assert len(events) == 2
        assert events[0].id == 1
        assert events[0].source == EventSource.USER
        assert events[1].id == 3
        assert events[1].source == EventSource.USER

        # Verify the API call
        mock_get.assert_called_once_with(
            'http://test-api.example.com/events?start_id=0&reverse=False',
            headers={'X-Session-API-Key': 'test-api-key'},
        )

    @patch('httpx.get')
    def test_search_events_with_type_filter(self, mock_get, event_store):
        """Test event retrieval with a type filter."""
        # Setup mock response with different event types
        mock_events = [
            create_mock_event(1, 'Hello', 'user'),
            # Create a different type of event (read)
            {
                'id': 2,
                'action': 'read',  # Using the correct ActionType.READ value
                'args': {
                    'path': '/test/file.txt',
                },
                'source': 'agent',
            },
            create_mock_event(3, 'Another', 'user'),
        ]
        mock_get.return_value = create_mock_response(mock_events)

        # Create a filter to include only MessageAction events
        event_filter = EventFilter(include_types=(MessageAction,))

        # Call the method with the filter
        events = list(event_store.search_events(filter=event_filter))

        # Verify the results (should only include MessageAction events)
        assert len(events) == 2
        assert events[0].id == 1
        assert events[1].id == 3

        # Verify the API call
        mock_get.assert_called_once_with(
            'http://test-api.example.com/events?start_id=0&reverse=False',
            headers={'X-Session-API-Key': 'test-api-key'},
        )

    @patch('httpx.get')
    def test_search_events_pagination(self, mock_get, event_store):
        """Test event retrieval with pagination (has_more=True)."""
        # Setup first page response
        first_page_events = [
            create_mock_event(1, 'Hello', 'user'),
            create_mock_event(2, 'World', 'agent'),
        ]
        first_response = create_mock_response(first_page_events, has_more=True)

        # Setup second page response
        second_page_events = [
            create_mock_event(3, 'More', 'user'),
            create_mock_event(4, 'Data', 'agent'),
        ]
        second_response = create_mock_response(second_page_events, has_more=False)

        # Configure mock to return different responses on consecutive calls
        mock_get.side_effect = [first_response, second_response]

        # Call the method
        events = list(event_store.search_events())

        # Verify the results (should include all events from both pages)
        assert len(events) == 4
        assert events[0].id == 1
        assert events[1].id == 2
        assert events[2].id == 3
        assert events[3].id == 4

        # Verify the API calls
        assert mock_get.call_count == 2
        # First call with start_id=0
        mock_get.assert_any_call(
            'http://test-api.example.com/events?start_id=0&reverse=False',
            headers={'X-Session-API-Key': 'test-api-key'},
        )
        # Second call with start_id=3 (after processing events with IDs 1 and 2)
        mock_get.assert_any_call(
            'http://test-api.example.com/events?start_id=3&reverse=False',
            headers={'X-Session-API-Key': 'test-api-key'},
        )

    @patch('httpx.get')
    def test_search_events_no_session_api_key(self, mock_get):
        """Test event retrieval without a session API key."""
        # Create event store without session_api_key
        event_store = NestedEventStore(
            base_url='http://test-api.example.com',
            sid='test-session',
            user_id='test-user',
        )

        # Setup mock response
        mock_events = [create_mock_event(1, 'Hello', 'user')]
        mock_get.return_value = create_mock_response(mock_events)

        # Call the method
        events = list(event_store.search_events())

        # Verify the results
        assert len(events) == 1

        # Verify the API call has no headers
        mock_get.assert_called_once_with(
            'http://test-api.example.com/events?start_id=0&reverse=False', headers={}
        )

    @patch('httpx.get')
    def test_search_events_with_query_filter(self, mock_get, event_store):
        """Test event retrieval with a text query filter."""
        # Setup mock response with different content
        mock_events = [
            create_mock_event(1, 'Hello world', 'user'),
            create_mock_event(2, 'Python is great', 'agent'),
            create_mock_event(3, 'Hello Python', 'user'),
        ]
        mock_get.return_value = create_mock_response(mock_events)

        # Create a filter to search for 'Python'
        event_filter = EventFilter(query='Python')

        # Call the method with the filter
        events = list(event_store.search_events(filter=event_filter))

        # Verify the results (should only include events with 'Python' in content)
        assert len(events) == 2
        assert events[0].id == 2
        assert events[1].id == 3

        # Verify the API call
        mock_get.assert_called_once_with(
            'http://test-api.example.com/events?start_id=0&reverse=False',
            headers={'X-Session-API-Key': 'test-api-key'},
        )
