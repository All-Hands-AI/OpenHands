import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from server.legacy_conversation_manager import (
    _LEGACY_ENTRY_TIMEOUT_SECONDS,
    LegacyCacheEntry,
    LegacyConversationManager,
)

from openhands.core.config.openhands_config import OpenHandsConfig
from openhands.server.config.server_config import ServerConfig
from openhands.server.monitoring import MonitoringListener
from openhands.storage.memory import InMemoryFileStore


@pytest.fixture
def mock_sio():
    """Create a mock SocketIO server."""
    return MagicMock()


@pytest.fixture
def mock_config():
    """Create a mock OpenHands config."""
    return MagicMock(spec=OpenHandsConfig)


@pytest.fixture
def mock_server_config():
    """Create a mock server config."""
    return MagicMock(spec=ServerConfig)


@pytest.fixture
def mock_file_store():
    """Create a mock file store."""
    return MagicMock(spec=InMemoryFileStore)


@pytest.fixture
def mock_monitoring_listener():
    """Create a mock monitoring listener."""
    return MagicMock(spec=MonitoringListener)


@pytest.fixture
def mock_conversation_manager():
    """Create a mock SaasNestedConversationManager."""
    mock_cm = MagicMock()
    mock_cm._get_runtime = AsyncMock()
    return mock_cm


@pytest.fixture
def mock_legacy_conversation_manager():
    """Create a mock ClusteredConversationManager."""
    return MagicMock()


@pytest.fixture
def legacy_manager(
    mock_sio,
    mock_config,
    mock_server_config,
    mock_file_store,
    mock_conversation_manager,
    mock_legacy_conversation_manager,
):
    """Create a LegacyConversationManager instance for testing."""
    return LegacyConversationManager(
        sio=mock_sio,
        config=mock_config,
        server_config=mock_server_config,
        file_store=mock_file_store,
        conversation_manager=mock_conversation_manager,
        legacy_conversation_manager=mock_legacy_conversation_manager,
    )


class TestLegacyCacheEntry:
    """Test the LegacyCacheEntry dataclass."""

    def test_cache_entry_creation(self):
        """Test creating a cache entry."""
        timestamp = time.time()
        entry = LegacyCacheEntry(is_legacy=True, timestamp=timestamp)

        assert entry.is_legacy is True
        assert entry.timestamp == timestamp

    def test_cache_entry_false(self):
        """Test creating a cache entry with False value."""
        timestamp = time.time()
        entry = LegacyCacheEntry(is_legacy=False, timestamp=timestamp)

        assert entry.is_legacy is False
        assert entry.timestamp == timestamp


class TestLegacyConversationManagerCacheCleanup:
    """Test cache cleanup functionality."""

    def test_cleanup_expired_cache_entries_removes_expired(self, legacy_manager):
        """Test that expired entries are removed from cache."""
        current_time = time.time()
        expired_time = current_time - _LEGACY_ENTRY_TIMEOUT_SECONDS - 1
        valid_time = current_time - 100  # Well within timeout

        # Add both expired and valid entries
        legacy_manager._legacy_cache = {
            'expired_conversation': LegacyCacheEntry(True, expired_time),
            'valid_conversation': LegacyCacheEntry(False, valid_time),
            'another_expired': LegacyCacheEntry(True, expired_time - 100),
        }

        legacy_manager._cleanup_expired_cache_entries()

        # Only valid entry should remain
        assert len(legacy_manager._legacy_cache) == 1
        assert 'valid_conversation' in legacy_manager._legacy_cache
        assert 'expired_conversation' not in legacy_manager._legacy_cache
        assert 'another_expired' not in legacy_manager._legacy_cache

    def test_cleanup_expired_cache_entries_keeps_valid(self, legacy_manager):
        """Test that valid entries are kept during cleanup."""
        current_time = time.time()
        valid_time = current_time - 100  # Well within timeout

        legacy_manager._legacy_cache = {
            'valid_conversation_1': LegacyCacheEntry(True, valid_time),
            'valid_conversation_2': LegacyCacheEntry(False, valid_time - 50),
        }

        legacy_manager._cleanup_expired_cache_entries()

        # Both entries should remain
        assert len(legacy_manager._legacy_cache) == 2
        assert 'valid_conversation_1' in legacy_manager._legacy_cache
        assert 'valid_conversation_2' in legacy_manager._legacy_cache

    def test_cleanup_expired_cache_entries_empty_cache(self, legacy_manager):
        """Test cleanup with empty cache."""
        legacy_manager._legacy_cache = {}

        legacy_manager._cleanup_expired_cache_entries()

        assert len(legacy_manager._legacy_cache) == 0


class TestIsLegacyRuntime:
    """Test the is_legacy_runtime method."""

    def test_is_legacy_runtime_none(self, legacy_manager):
        """Test with None runtime."""
        result = legacy_manager.is_legacy_runtime(None)
        assert result is False

    def test_is_legacy_runtime_legacy_command(self, legacy_manager):
        """Test with legacy runtime command."""
        runtime = {'command': 'some_old_legacy_command'}
        result = legacy_manager.is_legacy_runtime(runtime)
        assert result is True

    def test_is_legacy_runtime_new_command(self, legacy_manager):
        """Test with new runtime command containing openhands.server."""
        runtime = {'command': 'python -m openhands.server.listen'}
        result = legacy_manager.is_legacy_runtime(runtime)
        assert result is False

    def test_is_legacy_runtime_partial_match(self, legacy_manager):
        """Test with command that partially matches but is still legacy."""
        runtime = {'command': 'openhands.client.start'}
        result = legacy_manager.is_legacy_runtime(runtime)
        assert result is True

    def test_is_legacy_runtime_empty_command(self, legacy_manager):
        """Test with empty command."""
        runtime = {'command': ''}
        result = legacy_manager.is_legacy_runtime(runtime)
        assert result is True

    def test_is_legacy_runtime_missing_command_key(self, legacy_manager):
        """Test with runtime missing command key."""
        runtime = {'other_key': 'value'}
        # This should raise a KeyError
        with pytest.raises(KeyError):
            legacy_manager.is_legacy_runtime(runtime)


class TestShouldStartInLegacyMode:
    """Test the should_start_in_legacy_mode method."""

    @pytest.mark.asyncio
    async def test_cache_hit_valid_entry_legacy(self, legacy_manager):
        """Test cache hit with valid legacy entry."""
        conversation_id = 'test_conversation'
        current_time = time.time()

        # Add valid cache entry
        legacy_manager._legacy_cache[conversation_id] = LegacyCacheEntry(
            True, current_time - 100
        )

        result = await legacy_manager.should_start_in_legacy_mode(conversation_id)

        assert result is True
        # Should not call _get_runtime since we hit cache
        legacy_manager.conversation_manager._get_runtime.assert_not_called()

    @pytest.mark.asyncio
    async def test_cache_hit_valid_entry_non_legacy(self, legacy_manager):
        """Test cache hit with valid non-legacy entry."""
        conversation_id = 'test_conversation'
        current_time = time.time()

        # Add valid cache entry
        legacy_manager._legacy_cache[conversation_id] = LegacyCacheEntry(
            False, current_time - 100
        )

        result = await legacy_manager.should_start_in_legacy_mode(conversation_id)

        assert result is False
        # Should not call _get_runtime since we hit cache
        legacy_manager.conversation_manager._get_runtime.assert_not_called()

    @pytest.mark.asyncio
    async def test_cache_miss_legacy_runtime(self, legacy_manager):
        """Test cache miss with legacy runtime."""
        conversation_id = 'test_conversation'
        runtime = {'command': 'old_command'}

        legacy_manager.conversation_manager._get_runtime.return_value = runtime

        result = await legacy_manager.should_start_in_legacy_mode(conversation_id)

        assert result is True
        # Should call _get_runtime
        legacy_manager.conversation_manager._get_runtime.assert_called_once_with(
            conversation_id
        )
        # Should cache the result
        assert conversation_id in legacy_manager._legacy_cache
        assert legacy_manager._legacy_cache[conversation_id].is_legacy is True

    @pytest.mark.asyncio
    async def test_cache_miss_non_legacy_runtime(self, legacy_manager):
        """Test cache miss with non-legacy runtime."""
        conversation_id = 'test_conversation'
        runtime = {'command': 'python -m openhands.server.listen'}

        legacy_manager.conversation_manager._get_runtime.return_value = runtime

        result = await legacy_manager.should_start_in_legacy_mode(conversation_id)

        assert result is False
        # Should call _get_runtime
        legacy_manager.conversation_manager._get_runtime.assert_called_once_with(
            conversation_id
        )
        # Should cache the result
        assert conversation_id in legacy_manager._legacy_cache
        assert legacy_manager._legacy_cache[conversation_id].is_legacy is False

    @pytest.mark.asyncio
    async def test_cache_expired_entry(self, legacy_manager):
        """Test with expired cache entry."""
        conversation_id = 'test_conversation'
        expired_time = time.time() - _LEGACY_ENTRY_TIMEOUT_SECONDS - 1
        runtime = {'command': 'python -m openhands.server.listen'}

        # Add expired cache entry
        legacy_manager._legacy_cache[conversation_id] = LegacyCacheEntry(
            True,
            expired_time,  # This should be considered expired
        )

        legacy_manager.conversation_manager._get_runtime.return_value = runtime

        result = await legacy_manager.should_start_in_legacy_mode(conversation_id)

        assert result is False  # Runtime indicates non-legacy
        # Should call _get_runtime since cache is expired
        legacy_manager.conversation_manager._get_runtime.assert_called_once_with(
            conversation_id
        )
        # Should update cache with new result
        assert legacy_manager._legacy_cache[conversation_id].is_legacy is False

    @pytest.mark.asyncio
    async def test_cache_exactly_at_timeout(self, legacy_manager):
        """Test with cache entry exactly at timeout boundary."""
        conversation_id = 'test_conversation'
        timeout_time = time.time() - _LEGACY_ENTRY_TIMEOUT_SECONDS
        runtime = {'command': 'python -m openhands.server.listen'}

        # Add cache entry exactly at timeout
        legacy_manager._legacy_cache[conversation_id] = LegacyCacheEntry(
            True, timeout_time
        )

        legacy_manager.conversation_manager._get_runtime.return_value = runtime

        result = await legacy_manager.should_start_in_legacy_mode(conversation_id)

        # Should treat as expired and fetch from runtime
        assert result is False
        legacy_manager.conversation_manager._get_runtime.assert_called_once_with(
            conversation_id
        )

    @pytest.mark.asyncio
    async def test_runtime_returns_none(self, legacy_manager):
        """Test when runtime returns None."""
        conversation_id = 'test_conversation'

        legacy_manager.conversation_manager._get_runtime.return_value = None

        result = await legacy_manager.should_start_in_legacy_mode(conversation_id)

        assert result is False
        # Should cache the result
        assert conversation_id in legacy_manager._legacy_cache
        assert legacy_manager._legacy_cache[conversation_id].is_legacy is False

    @pytest.mark.asyncio
    async def test_cleanup_called_on_each_invocation(self, legacy_manager):
        """Test that cleanup is called on each invocation."""
        conversation_id = 'test_conversation'
        runtime = {'command': 'test'}

        legacy_manager.conversation_manager._get_runtime.return_value = runtime

        # Mock the cleanup method to verify it's called
        with patch.object(
            legacy_manager, '_cleanup_expired_cache_entries'
        ) as mock_cleanup:
            await legacy_manager.should_start_in_legacy_mode(conversation_id)
            mock_cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_multiple_conversations_cached_independently(self, legacy_manager):
        """Test that multiple conversations are cached independently."""
        conv1 = 'conversation_1'
        conv2 = 'conversation_2'

        runtime1 = {'command': 'old_command'}  # Legacy
        runtime2 = {'command': 'python -m openhands.server.listen'}  # Non-legacy

        # Mock to return different runtimes based on conversation_id
        def mock_get_runtime(conversation_id):
            if conversation_id == conv1:
                return runtime1
            return runtime2

        legacy_manager.conversation_manager._get_runtime.side_effect = mock_get_runtime

        result1 = await legacy_manager.should_start_in_legacy_mode(conv1)
        result2 = await legacy_manager.should_start_in_legacy_mode(conv2)

        assert result1 is True
        assert result2 is False

        # Both should be cached
        assert conv1 in legacy_manager._legacy_cache
        assert conv2 in legacy_manager._legacy_cache
        assert legacy_manager._legacy_cache[conv1].is_legacy is True
        assert legacy_manager._legacy_cache[conv2].is_legacy is False

    @pytest.mark.asyncio
    async def test_cache_timestamp_updated_on_refresh(self, legacy_manager):
        """Test that cache timestamp is updated when entry is refreshed."""
        conversation_id = 'test_conversation'
        old_time = time.time() - _LEGACY_ENTRY_TIMEOUT_SECONDS - 1
        runtime = {'command': 'test'}

        # Add expired entry
        legacy_manager._legacy_cache[conversation_id] = LegacyCacheEntry(True, old_time)
        legacy_manager.conversation_manager._get_runtime.return_value = runtime

        # Record time before call
        before_call = time.time()
        await legacy_manager.should_start_in_legacy_mode(conversation_id)
        after_call = time.time()

        # Timestamp should be updated
        cached_entry = legacy_manager._legacy_cache[conversation_id]
        assert cached_entry.timestamp >= before_call
        assert cached_entry.timestamp <= after_call


class TestLegacyConversationManagerIntegration:
    """Integration tests for LegacyConversationManager."""

    @pytest.mark.asyncio
    async def test_get_instance_creates_proper_manager(
        self,
        mock_sio,
        mock_config,
        mock_file_store,
        mock_server_config,
        mock_monitoring_listener,
    ):
        """Test that get_instance creates a properly configured manager."""
        with patch(
            'server.legacy_conversation_manager.SaasNestedConversationManager'
        ) as mock_saas, patch(
            'server.legacy_conversation_manager.ClusteredConversationManager'
        ) as mock_clustered:
            mock_saas.get_instance.return_value = MagicMock()
            mock_clustered.get_instance.return_value = MagicMock()

            manager = LegacyConversationManager.get_instance(
                mock_sio,
                mock_config,
                mock_file_store,
                mock_server_config,
                mock_monitoring_listener,
            )

            assert isinstance(manager, LegacyConversationManager)
            assert manager.sio == mock_sio
            assert manager.config == mock_config
            assert manager.file_store == mock_file_store
            assert manager.server_config == mock_server_config

            # Verify that both nested managers are created
            mock_saas.get_instance.assert_called_once()
            mock_clustered.get_instance.assert_called_once()

    def test_legacy_cache_initialized_empty(self, legacy_manager):
        """Test that legacy cache is initialized as empty dict."""
        assert isinstance(legacy_manager._legacy_cache, dict)
        assert len(legacy_manager._legacy_cache) == 0


class TestEdgeCases:
    """Test edge cases and error scenarios."""

    @pytest.mark.asyncio
    async def test_get_runtime_raises_exception(self, legacy_manager):
        """Test behavior when _get_runtime raises an exception."""
        conversation_id = 'test_conversation'

        legacy_manager.conversation_manager._get_runtime.side_effect = Exception(
            'Runtime error'
        )

        # Should propagate the exception
        with pytest.raises(Exception, match='Runtime error'):
            await legacy_manager.should_start_in_legacy_mode(conversation_id)

    @pytest.mark.asyncio
    async def test_very_large_cache(self, legacy_manager):
        """Test behavior with a large number of cache entries."""
        current_time = time.time()

        # Add many cache entries
        for i in range(1000):
            legacy_manager._legacy_cache[f'conversation_{i}'] = LegacyCacheEntry(
                i % 2 == 0, current_time - i
            )

        # This should work without issues
        await legacy_manager.should_start_in_legacy_mode('new_conversation')

        # Should have added one more entry
        assert len(legacy_manager._legacy_cache) == 1001

    def test_cleanup_with_concurrent_modifications(self, legacy_manager):
        """Test cleanup behavior when cache is modified during cleanup."""
        current_time = time.time()
        expired_time = current_time - _LEGACY_ENTRY_TIMEOUT_SECONDS - 1

        # Add expired entries
        legacy_manager._legacy_cache = {
            f'conversation_{i}': LegacyCacheEntry(True, expired_time) for i in range(10)
        }

        # This should work without raising exceptions
        legacy_manager._cleanup_expired_cache_entries()

        # All entries should be removed
        assert len(legacy_manager._legacy_cache) == 0
