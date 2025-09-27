"""Unit tests for EventStore cache functionality.

These tests focus on the cache control behavior introduced to fix GCP storage errors
where EventStore was attempting to read cache files it cannot create.
"""

import tempfile
from unittest.mock import MagicMock, patch

import pytest

from openhands.events.action import NullAction
from openhands.events.event import EventSource
from openhands.events.event_store import EventStore
from openhands.events.observation import NullObservation
from openhands.events.stream import EventStream
from openhands.storage.local import LocalFileStore


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def file_store(temp_dir):
    """Create a LocalFileStore for testing."""
    return LocalFileStore(temp_dir)


class TestEventStoreCache:
    """Tests for EventStore cache control functionality."""

    def test_event_store_cache_disabled_by_default(self, file_store):
        """Test that EventStore has cache disabled by default."""
        event_store = EventStore(
            sid='test-conversation', file_store=file_store, user_id='test-user'
        )

        assert event_store.use_cache is False, (
            'EventStore should have use_cache=False by default'
        )

    def test_event_store_cache_can_be_enabled(self, file_store):
        """Test that EventStore cache can be explicitly enabled."""
        event_store = EventStore(
            sid='test-conversation',
            file_store=file_store,
            user_id='test-user',
            use_cache=True,
        )

        assert event_store.use_cache is True, (
            'EventStore should respect explicit use_cache=True'
        )

    def test_event_stream_cache_enabled_by_default(self, file_store):
        """Test that EventStream has cache enabled by default."""
        event_stream = EventStream(
            sid='test-conversation', file_store=file_store, user_id='test-user'
        )

        assert event_stream.use_cache is True, (
            'EventStream should have use_cache=True by default'
        )

    def test_cache_disabled_returns_dummy_page(self, file_store):
        """Test that when cache is disabled, _load_cache_page_for_index returns dummy page."""
        event_store = EventStore(
            sid='test-conversation',
            file_store=file_store,
            user_id='test-user',
            use_cache=False,
        )

        # Load a cache page for any index
        cache_page = event_store._load_cache_page_for_index(150)

        # Should return the dummy page
        assert cache_page.events is None, 'Should return dummy page with None events'
        assert cache_page.start == 1, 'Dummy page should have start=1'
        assert cache_page.end == -1, 'Dummy page should have end=-1'

    def test_cache_enabled_attempts_to_load_cache(self, file_store):
        """Test that when cache is enabled, _load_cache_page_for_index attempts to load cache."""
        event_store = EventStore(
            sid='test-conversation',
            file_store=file_store,
            user_id='test-user',
            use_cache=True,
        )

        # Mock the _load_cache_page method to verify it's called
        with patch.object(event_store, '_load_cache_page') as mock_load_cache:
            mock_load_cache.return_value = MagicMock(events=None, start=150, end=175)

            # Load a cache page for index 150
            event_store._load_cache_page_for_index(150)

            # Should have called _load_cache_page
            mock_load_cache.assert_called_once_with(150, 175)

    def test_search_events_works_without_cache(self, file_store):
        """Test that search_events works correctly when cache is disabled."""
        event_store = EventStore(
            sid='test-conversation',
            file_store=file_store,
            user_id='test-user',
            use_cache=False,
        )

        # Search for events should work without errors
        events = list(event_store.search_events())

        # Should return empty list since no events exist
        assert events == [], 'Should return empty list when no events exist'

    def test_search_events_with_missing_cache_files(self, file_store):
        """Test that search_events handles missing cache files gracefully when cache is disabled."""
        # Create an EventStore with cache disabled
        event_store = EventStore(
            sid='test-conversation',
            file_store=file_store,
            user_id='test-user',
            use_cache=False,
        )

        # Mock file_store.read to simulate GCP "No such object" error
        original_read = file_store.read

        def mock_read(path):
            if 'event_cache' in path:
                # Simulate GCP storage error
                raise Exception(
                    'No such object: prod-openhands-sessions/users/.../event_cache/150-175.json'
                )
            return original_read(path)

        file_store.read = mock_read

        # Search for events in a specific range
        events = list(event_store.search_events(start_id=150, end_id=175))

        # Should work without errors (returns empty since no individual event files exist)
        assert events == [], 'Should handle missing cache files gracefully'

    def test_get_event_works_without_cache(self, file_store):
        """Test that get_event works correctly when cache is disabled."""
        event_store = EventStore(
            sid='test-conversation',
            file_store=file_store,
            user_id='test-user',
            use_cache=False,
        )

        # Try to get a specific event that doesn't exist
        # This should handle the FileNotFoundError gracefully
        try:
            event = event_store.get_event(0)
            # If no exception, should return None
            assert event is None, "Should return None when event doesn't exist"
        except FileNotFoundError:
            # This is expected behavior when the event file doesn't exist
            pass

    def test_cache_integration_with_event_stream(self, file_store):
        """Test that EventStream can write cache files and EventStore can read them when enabled."""
        # Create an EventStream (cache enabled by default)
        event_stream = EventStream(
            sid='test-conversation', file_store=file_store, user_id='test-user'
        )

        # Add some events to create cache files
        for i in range(10):
            event_stream.add_event(NullObservation(f'test{i}'), EventSource.AGENT)

        # Close the stream to ensure cache files are written
        event_stream.close()

        # Create an EventStore with cache enabled
        event_store = EventStore(
            sid='test-conversation',
            file_store=file_store,
            user_id='test-user',
            use_cache=True,
        )

        # Should be able to read events using cache
        events = list(event_store.search_events())

        # Should find the events
        assert len(events) > 0, 'Should find events when cache is enabled'

    def test_cache_disabled_avoids_storage_requests(self, file_store):
        """Test that when cache is disabled, no storage requests are made for cache files."""
        event_store = EventStore(
            sid='test-conversation',
            file_store=file_store,
            user_id='test-user',
            use_cache=False,
        )

        # Mock file_store.read to track calls
        original_read = file_store.read
        read_calls = []

        def mock_read(path):
            read_calls.append(path)
            return original_read(path)

        file_store.read = mock_read

        # Search for events
        list(event_store.search_events(start_id=150, end_id=175))

        # Should not have made any calls to read cache files
        cache_calls = [call for call in read_calls if 'event_cache' in call]
        assert len(cache_calls) == 0, (
            'Should not make storage requests for cache files when cache is disabled'
        )

    def test_backwards_compatibility(self, file_store):
        """Test that existing code continues to work with the new cache control."""
        # Create EventStore without specifying use_cache (should default to False)
        event_store = EventStore(
            sid='test-conversation', file_store=file_store, user_id='test-user'
        )

        # Should work without errors
        events = list(event_store.search_events())
        assert events == [], 'Should work with default cache settings'

        # Create EventStream without specifying use_cache (should default to True)
        event_stream = EventStream(
            sid='test-conversation-2', file_store=file_store, user_id='test-user'
        )

        # Should work without errors
        event_stream.add_event(NullAction(), EventSource.AGENT)
        events = list(event_stream.get_events())
        assert len(events) == 1, 'EventStream should work with default cache settings'

        event_stream.close()
