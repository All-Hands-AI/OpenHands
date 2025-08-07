import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest

from openhands.server.utils.ratelimit_storage import (
    InMemoryRateLimiterStorage,
    RedisRateLimiterStorage,
    create_rate_limiter_storage,
)


class TestInMemoryRateLimiterStorage:
    """Test suite for InMemoryRateLimiterStorage."""

    @pytest.fixture
    def storage(self):
        """Create a fresh InMemoryRateLimiterStorage instance for each test."""
        return InMemoryRateLimiterStorage()

    @pytest.mark.asyncio
    async def test_init(self, storage):
        """Test storage initialization."""
        assert hasattr(storage, 'history')
        assert isinstance(storage.history, dict)

    @pytest.mark.asyncio
    async def test_add_and_get_requests(self, storage):
        """Test adding and retrieving requests."""
        user_id = 'test_user'
        now = datetime.now()

        # Initially no requests
        requests = await storage.get_requests(user_id)
        assert requests == []

        # Add a request
        await storage.add_request(user_id, now)
        requests = await storage.get_requests(user_id)
        assert len(requests) == 1
        assert requests[0] == now

        # Add another request
        later = now + timedelta(seconds=1)
        await storage.add_request(user_id, later)
        requests = await storage.get_requests(user_id)
        assert len(requests) == 2
        assert requests == [now, later]

    @pytest.mark.asyncio
    async def test_get_request_count(self, storage):
        """Test getting request count."""
        user_id = 'test_user'

        # Initially no requests
        count = await storage.get_request_count(user_id)
        assert count == 0

        # Add requests and verify count
        now = datetime.now()
        await storage.add_request(user_id, now)
        count = await storage.get_request_count(user_id)
        assert count == 1

        await storage.add_request(user_id, now + timedelta(seconds=1))
        count = await storage.get_request_count(user_id)
        assert count == 2

    @pytest.mark.asyncio
    async def test_clean_old_requests(self, storage):
        """Test cleaning old requests."""
        user_id = 'test_user'
        now = datetime.now()

        # Add requests at different times
        old_request = now - timedelta(seconds=100)
        recent_request = now - timedelta(seconds=10)
        current_request = now

        await storage.add_request(user_id, old_request)
        await storage.add_request(user_id, recent_request)
        await storage.add_request(user_id, current_request)

        # Clean requests older than 30 seconds
        cutoff = now - timedelta(seconds=30)
        await storage.clean_old_requests(user_id, cutoff)

        # Only recent and current requests should remain
        requests = await storage.get_requests(user_id)
        assert len(requests) == 2
        assert old_request not in requests
        assert recent_request in requests
        assert current_request in requests

    @pytest.mark.asyncio
    async def test_multiple_users(self, storage):
        """Test storage isolation between different users."""
        user1 = 'user1'
        user2 = 'user2'
        now = datetime.now()

        await storage.add_request(user1, now)
        await storage.add_request(user2, now + timedelta(seconds=1))

        user1_requests = await storage.get_requests(user1)
        user2_requests = await storage.get_requests(user2)

        assert len(user1_requests) == 1
        assert len(user2_requests) == 1
        assert user1_requests[0] == now
        assert user2_requests[0] == now + timedelta(seconds=1)

    @pytest.mark.asyncio
    async def test_get_requests_returns_copy(self, storage):
        """Test that get_requests returns a copy, not a reference."""
        user_id = 'test_user'
        now = datetime.now()

        await storage.add_request(user_id, now)
        requests1 = await storage.get_requests(user_id)
        requests2 = await storage.get_requests(user_id)

        # Modify one copy
        requests1.append(now + timedelta(seconds=1))

        # Other copy should be unchanged
        assert len(requests2) == 1
        assert requests1 != requests2


class TestRedisRateLimiterStorage:
    """Test suite for RedisRateLimiterStorage."""

    @pytest.fixture
    def mock_redis_available(self):
        """Mock Redis as available."""
        with patch('openhands.server.utils.ratelimit_storage.REDIS_AVAILABLE', True):
            yield

    @pytest.fixture
    def mock_redis_unavailable(self):
        """Mock Redis as unavailable."""
        with patch('openhands.server.utils.ratelimit_storage.REDIS_AVAILABLE', False):
            yield

    @pytest.fixture
    def mock_redis_client(self):
        """Create a mock Redis client."""
        client = AsyncMock()
        client.get = AsyncMock()
        client.set = AsyncMock()
        client.delete = AsyncMock()
        client.close = AsyncMock()
        return client

    @pytest.mark.asyncio
    async def test_init_success(self, mock_redis_available):
        """Test successful Redis storage initialization."""
        with patch('redis.asyncio.from_url') as mock_from_url:
            mock_client = AsyncMock()
            mock_from_url.return_value = mock_client

            storage = RedisRateLimiterStorage(
                redis_url='redis://localhost:6379',
                redis_password='test_password',
                key_prefix='test_prefix',
            )

            assert storage.redis_url == 'redis://localhost:6379'
            assert storage.redis_password == 'test_password'
            assert storage.key_prefix == 'test_prefix'
            assert storage._redis_client is not None
            mock_from_url.assert_called_once_with(
                'redis://localhost:6379',
                password='test_password',
                decode_responses=True,
            )

    @pytest.mark.asyncio
    async def test_init_redis_unavailable(self, mock_redis_unavailable):
        """Test Redis storage initialization when Redis is unavailable."""
        with pytest.raises(ImportError, match='Redis is not available'):
            RedisRateLimiterStorage(
                redis_url='redis://localhost:6379', key_prefix='test_prefix'
            )

    @pytest.mark.asyncio
    async def test_init_missing_url(self, mock_redis_available):
        """Test Redis storage initialization with missing URL."""
        with pytest.raises(ValueError, match='Redis URL is required'):
            RedisRateLimiterStorage(key_prefix='test_prefix')

    @pytest.mark.asyncio
    async def test_init_missing_prefix(self, mock_redis_available):
        """Test Redis storage initialization with missing key prefix."""
        with pytest.raises(ValueError, match='Key prefix is required'):
            RedisRateLimiterStorage(redis_url='redis://localhost:6379')

    @pytest.mark.asyncio
    async def test_get_key_formatting(self, mock_redis_available):
        """Test Redis key formatting."""
        with patch('redis.asyncio.from_url') as mock_from_url:
            mock_client = AsyncMock()
            mock_from_url.return_value = mock_client

            storage = RedisRateLimiterStorage(
                redis_url='redis://localhost:6379', key_prefix='test_prefix'
            )

            key = storage._get_key('user123')
            assert key == 'test_prefix:user123'

    @pytest.mark.asyncio
    async def test_get_requests_empty(self, mock_redis_available, mock_redis_client):
        """Test getting requests when none exist."""
        # Mock Redis client
        mock_redis_client.get.return_value = None
        with patch('redis.asyncio.from_url', return_value=mock_redis_client):
            storage = RedisRateLimiterStorage(
                redis_url='redis://localhost:6379', key_prefix='test_prefix'
            )
            requests = await storage.get_requests('user123')

        assert requests == []
        mock_redis_client.get.assert_called_once_with('test_prefix:user123')

    @pytest.mark.asyncio
    async def test_get_requests_with_data(
        self, mock_redis_available, mock_redis_client
    ):
        """Test getting requests with existing data."""
        # Mock data in Redis
        now = datetime.now()
        timestamps = [now.isoformat(), (now + timedelta(seconds=1)).isoformat()]
        mock_redis_client.get.return_value = json.dumps(timestamps)

        with patch('redis.asyncio.from_url', return_value=mock_redis_client):
            storage = RedisRateLimiterStorage(
                redis_url='redis://localhost:6379', key_prefix='test_prefix'
            )
            requests = await storage.get_requests('user123')

        assert len(requests) == 2
        assert isinstance(requests[0], datetime)
        assert isinstance(requests[1], datetime)

    @pytest.mark.asyncio
    async def test_add_request(self, mock_redis_available, mock_redis_client):
        """Test adding a request."""
        now = datetime.now()
        mock_redis_client.get.return_value = None  # No existing data

        with patch('redis.asyncio.from_url', return_value=mock_redis_client):
            storage = RedisRateLimiterStorage(
                redis_url='redis://localhost:6379', key_prefix='test_prefix'
            )
            await storage.add_request('user123', now)

        # Verify Redis calls
        mock_redis_client.get.assert_called_once()
        mock_redis_client.set.assert_called_once()

        # Check the data that was set
        set_call_args = mock_redis_client.set.call_args
        key, data, ex = set_call_args[0][0], set_call_args[0][1], set_call_args[1]['ex']

        assert key == 'test_prefix:user123'
        assert ex == 3600  # 1 hour expiry

        stored_timestamps = json.loads(data)
        assert len(stored_timestamps) == 1
        assert datetime.fromisoformat(stored_timestamps[0]) == now

    @pytest.mark.asyncio
    async def test_clean_old_requests(self, mock_redis_available, mock_redis_client):
        """Test cleaning old requests."""
        now = datetime.now()
        old_time = now - timedelta(seconds=100)
        recent_time = now - timedelta(seconds=10)

        # Mock existing data
        timestamps = [old_time.isoformat(), recent_time.isoformat()]
        mock_redis_client.get.return_value = json.dumps(timestamps)

        cutoff = now - timedelta(seconds=30)

        with patch('redis.asyncio.from_url', return_value=mock_redis_client):
            storage = RedisRateLimiterStorage(
                redis_url='redis://localhost:6379', key_prefix='test_prefix'
            )
            await storage.clean_old_requests('user123', cutoff)

        # Should call set with only recent data
        mock_redis_client.set.assert_called_once()
        set_call_args = mock_redis_client.set.call_args
        data = set_call_args[0][1]

        stored_timestamps = json.loads(data)
        assert len(stored_timestamps) == 1
        assert datetime.fromisoformat(stored_timestamps[0]) == recent_time

    @pytest.mark.asyncio
    async def test_clean_old_requests_delete_when_empty(
        self, mock_redis_available, mock_redis_client
    ):
        """Test deleting key when all requests are old."""
        now = datetime.now()
        old_time = now - timedelta(seconds=100)

        # Mock existing data with only old timestamps
        timestamps = [old_time.isoformat()]
        mock_redis_client.get.return_value = json.dumps(timestamps)

        cutoff = now - timedelta(seconds=30)

        with patch('redis.asyncio.from_url', return_value=mock_redis_client):
            storage = RedisRateLimiterStorage(
                redis_url='redis://localhost:6379', key_prefix='test_prefix'
            )
            await storage.clean_old_requests('user123', cutoff)

        # Should delete the key
        mock_redis_client.delete.assert_called_once_with('test_prefix:user123')
        mock_redis_client.set.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_request_count(self, mock_redis_available, mock_redis_client):
        """Test getting request count."""
        now = datetime.now()
        timestamps = [now.isoformat(), (now + timedelta(seconds=1)).isoformat()]
        mock_redis_client.get.return_value = json.dumps(timestamps)

        with patch('redis.asyncio.from_url', return_value=mock_redis_client):
            storage = RedisRateLimiterStorage(
                redis_url='redis://localhost:6379', key_prefix='test_prefix'
            )
            count = await storage.get_request_count('user123')

        assert count == 2

    @pytest.mark.asyncio
    async def test_redis_error_handling(self, mock_redis_available, mock_redis_client):
        """Test Redis error handling."""
        # Mock Redis to raise an exception
        mock_redis_client.get.side_effect = Exception('Redis connection error')

        with patch('redis.asyncio.from_url', return_value=mock_redis_client):
            storage = RedisRateLimiterStorage(
                redis_url='redis://localhost:6379', key_prefix='test_prefix'
            )
            # Should return empty list on error
            requests = await storage.get_requests('user123')
            assert requests == []

            # Should handle errors gracefully for other operations
            now = datetime.now()
            await storage.add_request('user123', now)  # Should not raise
            await storage.clean_old_requests('user123', now)  # Should not raise

    @pytest.mark.asyncio
    async def test_close_connection(self, mock_redis_available, mock_redis_client):
        """Test closing Redis connection."""
        with patch('redis.asyncio.from_url', return_value=mock_redis_client):
            storage = RedisRateLimiterStorage(
                redis_url='redis://localhost:6379', key_prefix='test_prefix'
            )
            # Client is already initialized in constructor
            assert storage._redis_client is not None

            # Close connection
            await storage.close()
            mock_redis_client.close.assert_called_once()


class TestCreateRateLimiterStorage:
    """Test suite for create_rate_limiter_storage factory function."""

    @pytest.mark.asyncio
    async def test_create_memory_storage(self):
        """Test creating in-memory storage."""
        storage = create_rate_limiter_storage(storage_type='memory')
        assert isinstance(storage, InMemoryRateLimiterStorage)

    @pytest.mark.asyncio
    async def test_create_memory_storage_default(self):
        """Test creating in-memory storage as default."""
        storage = create_rate_limiter_storage()
        assert isinstance(storage, InMemoryRateLimiterStorage)

    @pytest.mark.asyncio
    async def test_create_memory_storage_unknown_type(self):
        """Test creating in-memory storage for unknown type."""
        storage = create_rate_limiter_storage(storage_type='unknown')
        assert isinstance(storage, InMemoryRateLimiterStorage)

    @pytest.mark.asyncio
    async def test_create_redis_storage(self):
        """Test creating Redis storage."""
        with patch('openhands.server.utils.ratelimit_storage.REDIS_AVAILABLE', True):
            storage = create_rate_limiter_storage(
                storage_type='redis',
                host_url='redis://localhost:6379',
                key_prefix='test_prefix',
            )
            assert isinstance(storage, RedisRateLimiterStorage)

    @pytest.mark.asyncio
    async def test_create_redis_storage_unavailable(self):
        """Test creating Redis storage when Redis is unavailable."""
        with patch('openhands.server.utils.ratelimit_storage.REDIS_AVAILABLE', False):
            storage = create_rate_limiter_storage(
                storage_type='redis',
                host_url='redis://localhost:6379',
                key_prefix='test_prefix',
            )
            # Should fallback to in-memory storage
            assert isinstance(storage, InMemoryRateLimiterStorage)

    @pytest.mark.asyncio
    async def test_create_redis_storage_case_insensitive(self):
        """Test creating Redis storage with case-insensitive type."""
        with patch('openhands.server.utils.ratelimit_storage.REDIS_AVAILABLE', True):
            storage = create_rate_limiter_storage(
                storage_type='REDIS',
                host_url='redis://localhost:6379',
                key_prefix='test_prefix',
            )
            assert isinstance(storage, RedisRateLimiterStorage)


if __name__ == '__main__':
    pytest.main([__file__])
