import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock

import pytest

from openhands.server.middleware import UserBasedRateLimiter
from openhands.server.utils.ratelimit_storage import InMemoryRateLimiterStorage


class MockRateLimiterStorage:
    """Mock storage for testing rate limiter logic."""

    def __init__(self):
        self.requests = []
        self.add_request_calls = []
        self.clean_old_requests_calls = []

    async def get_requests(self, key: str) -> list[datetime]:
        return self.requests.copy()

    async def add_request(self, key: str, timestamp: datetime) -> None:
        self.add_request_calls.append((key, timestamp))
        self.requests.append(timestamp)

    async def clean_old_requests(self, key: str, cutoff: datetime) -> None:
        self.clean_old_requests_calls.append((key, cutoff))
        self.requests = [ts for ts in self.requests if ts > cutoff]

    async def get_request_count(self, key: str) -> int:
        return len(self.requests)


class TestUserBasedRateLimiter:
    """Test suite for UserBasedRateLimiter."""

    @pytest.fixture
    def mock_storage(self):
        """Create a mock storage for testing."""
        return MockRateLimiterStorage()

    @pytest.fixture
    def rate_limiter_with_mock_storage(self, mock_storage):
        """Create a rate limiter with mock storage."""
        return UserBasedRateLimiter(
            requests=5, seconds=60, sleep_seconds=0, storage=mock_storage
        )

    @pytest.fixture
    def rate_limiter_with_memory_storage(self):
        """Create a rate limiter with in-memory storage."""
        return UserBasedRateLimiter(
            requests=5,
            seconds=60,
            sleep_seconds=0,
            storage=InMemoryRateLimiterStorage(),
        )

    @pytest.mark.asyncio
    async def test_init_default_storage(self):
        """Test rate limiter initialization with default storage."""
        rate_limiter = UserBasedRateLimiter()
        assert isinstance(rate_limiter.storage, InMemoryRateLimiterStorage)
        assert rate_limiter.requests == 60
        assert rate_limiter.seconds == 60
        assert rate_limiter.sleep_seconds == 1

    @pytest.mark.asyncio
    async def test_init_custom_storage(self, mock_storage):
        """Test rate limiter initialization with custom storage."""
        rate_limiter = UserBasedRateLimiter(
            requests=10, seconds=30, sleep_seconds=2, storage=mock_storage
        )
        assert rate_limiter.storage is mock_storage
        assert rate_limiter.requests == 10
        assert rate_limiter.seconds == 30
        assert rate_limiter.sleep_seconds == 2

    @pytest.mark.asyncio
    async def test_is_allowed_empty_user_id(self, rate_limiter_with_mock_storage):
        """Test rate limiting with empty user ID."""
        is_allowed = await rate_limiter_with_mock_storage.is_allowed('')
        assert is_allowed is False

        is_allowed = await rate_limiter_with_mock_storage.is_allowed(None)
        assert is_allowed is False

    @pytest.mark.asyncio
    async def test_is_allowed_within_limit(
        self, rate_limiter_with_mock_storage, mock_storage
    ):
        """Test rate limiting within the allowed limit."""
        user_id = 'test_user'

        # First request should be allowed
        is_allowed = await rate_limiter_with_mock_storage.is_allowed(user_id)
        assert is_allowed is True

        # Verify storage interactions
        assert len(mock_storage.add_request_calls) == 1
        assert len(mock_storage.clean_old_requests_calls) == 1
        assert mock_storage.add_request_calls[0][0] == user_id

    @pytest.mark.asyncio
    async def test_is_allowed_at_limit(self, rate_limiter_with_memory_storage):
        """Test rate limiting at the exact limit."""
        user_id = 'test_user'
        now = datetime.now()

        # Add exactly the limit number of requests (5)
        for i in range(5):
            await rate_limiter_with_memory_storage.storage.add_request(
                user_id, now + timedelta(seconds=i)
            )

        # Next request will be added (making it 6), then checked
        # Since 6 > 5 and sleep_seconds=0, it should be rejected
        is_allowed = await rate_limiter_with_memory_storage.is_allowed(user_id)
        assert is_allowed is False

        # Count should now be 6 (over the limit of 5)
        count = await rate_limiter_with_memory_storage.storage.get_request_count(
            user_id
        )
        assert count == 6

    @pytest.mark.asyncio
    async def test_is_allowed_over_limit_no_sleep(
        self, rate_limiter_with_memory_storage
    ):
        """Test rate limiting over the limit with no sleep."""
        user_id = 'test_user'
        now = datetime.now()

        # Add more than the limit (5) but less than 2x limit (10)
        for i in range(7):
            await rate_limiter_with_memory_storage.storage.add_request(
                user_id, now + timedelta(seconds=i)
            )

        # Next request should trigger sleep logic but since sleep_seconds=0, should be rejected
        is_allowed = await rate_limiter_with_memory_storage.is_allowed(user_id)
        assert is_allowed is False

    @pytest.mark.asyncio
    async def test_is_allowed_over_limit_with_sleep(self):
        """Test rate limiting over the limit with sleep."""
        storage = InMemoryRateLimiterStorage()
        rate_limiter = UserBasedRateLimiter(
            requests=3,
            seconds=60,
            sleep_seconds=0.1,  # Short sleep for testing
            storage=storage,
        )

        user_id = 'test_user'
        now = datetime.now()

        # Add more than the limit (3) but less than 2x limit (6)
        for i in range(4):
            await storage.add_request(user_id, now + timedelta(seconds=i))

        # Next request should trigger sleep and then be allowed
        start_time = datetime.now()
        is_allowed = await rate_limiter.is_allowed(user_id)
        end_time = datetime.now()

        assert is_allowed is True
        # Verify that sleep actually happened
        assert abs((end_time - start_time).total_seconds() - 0.1) < 0.01

    @pytest.mark.asyncio
    async def test_is_allowed_way_over_limit(self, rate_limiter_with_memory_storage):
        """Test rate limiting way over the limit (2x limit)."""
        user_id = 'test_user'
        now = datetime.now()

        # Add more than 2x the limit (10 > 2*5)
        for i in range(12):
            await rate_limiter_with_memory_storage.storage.add_request(
                user_id, now + timedelta(seconds=i)
            )

        # Should be immediately rejected
        is_allowed = await rate_limiter_with_memory_storage.is_allowed(user_id)
        assert is_allowed is False

    @pytest.mark.asyncio
    async def test_old_requests_cleaned(self, rate_limiter_with_memory_storage):
        """Test that old requests are properly cleaned."""
        user_id = 'test_user'
        now = datetime.now()

        # Add old requests (outside the 60-second window)
        old_time = now - timedelta(seconds=120)
        for i in range(5):
            await rate_limiter_with_memory_storage.storage.add_request(
                user_id, old_time + timedelta(seconds=i)
            )

        # Add recent request
        await rate_limiter_with_memory_storage.storage.add_request(user_id, now)

        # Make a new request - this should clean old requests
        is_allowed = await rate_limiter_with_memory_storage.is_allowed(user_id)
        assert is_allowed is True

        # Verify old requests were cleaned (should only have 2 requests: recent + new)
        count = await rate_limiter_with_memory_storage.storage.get_request_count(
            user_id
        )
        assert count == 2

    @pytest.mark.asyncio
    async def test_multiple_users_isolation(self, rate_limiter_with_memory_storage):
        """Test that different users have isolated rate limits."""
        user1 = 'user1'
        user2 = 'user2'
        now = datetime.now()

        # Fill up user1's limit (5 requests)
        for i in range(5):
            await rate_limiter_with_memory_storage.storage.add_request(
                user1, now + timedelta(seconds=i)
            )

        # User1 should be over limit (5 + 1 = 6 > 5, sleep_seconds=0)
        is_allowed = await rate_limiter_with_memory_storage.is_allowed(user1)
        assert is_allowed is False

        # User2 should still be allowed (independent limit, first request)
        is_allowed = await rate_limiter_with_memory_storage.is_allowed(user2)
        assert is_allowed is True

        # Verify counts
        count1 = await rate_limiter_with_memory_storage.storage.get_request_count(user1)
        count2 = await rate_limiter_with_memory_storage.storage.get_request_count(user2)
        assert count1 == 6  # 5 pre-existing + 1 from is_allowed call
        assert count2 == 1  # 1 from is_allowed call

    @pytest.mark.asyncio
    async def test_concurrent_requests(self, rate_limiter_with_memory_storage):
        """Test concurrent requests for the same user."""
        user_id = 'test_user'

        # Make multiple concurrent requests
        tasks = []
        for _ in range(10):
            task = asyncio.create_task(
                rate_limiter_with_memory_storage.is_allowed(user_id)
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks)

        # Some should be allowed, some rejected based on the limit
        allowed_count = sum(1 for result in results if result)
        rejected_count = sum(1 for result in results if not result)

        assert allowed_count > 0
        assert rejected_count > 0
        assert allowed_count + rejected_count == 10

    @pytest.mark.asyncio
    async def test_time_window_reset(self, rate_limiter_with_memory_storage):
        """Test that rate limit resets after time window."""
        user_id = 'test_user'

        # Create a rate limiter with short time window for testing
        storage = InMemoryRateLimiterStorage()
        rate_limiter = UserBasedRateLimiter(
            requests=2,
            seconds=1,  # 1 second window
            sleep_seconds=0,
            storage=storage,
        )

        # Make requests to hit the limit
        await rate_limiter.is_allowed(user_id)  # 1st request
        await rate_limiter.is_allowed(user_id)  # 2nd request
        await rate_limiter.is_allowed(user_id)  # 3rd request (over limit)

        # Should be over limit now
        is_allowed = await rate_limiter.is_allowed(user_id)
        assert is_allowed is False

        # Wait for time window to pass
        await asyncio.sleep(1.1)

        # Should be allowed again (old requests cleaned)
        is_allowed = await rate_limiter.is_allowed(user_id)
        assert is_allowed is True

    @pytest.mark.asyncio
    async def test_storage_error_handling(self):
        """Test rate limiter behavior when storage operations fail."""
        # Create a mock storage that raises exceptions
        mock_storage = AsyncMock()
        mock_storage.clean_old_requests = AsyncMock(
            side_effect=Exception('Storage error')
        )
        mock_storage.add_request = AsyncMock(side_effect=Exception('Storage error'))
        mock_storage.get_request_count = AsyncMock(
            side_effect=Exception('Storage error')
        )

        rate_limiter = UserBasedRateLimiter(
            requests=5, seconds=60, sleep_seconds=0, storage=mock_storage
        )

        # Should handle errors gracefully and not crash
        try:
            result = await rate_limiter.is_allowed('test_user')
            # The behavior when storage fails is implementation-dependent
            # but it should not raise an exception
            assert isinstance(result, bool)
        except Exception as e:
            pytest.fail(f'Rate limiter should handle storage errors gracefully: {e}')

    @pytest.mark.asyncio
    async def test_edge_case_zero_requests(self):
        """Test rate limiter with zero allowed requests."""
        storage = InMemoryRateLimiterStorage()
        rate_limiter = UserBasedRateLimiter(
            requests=0, seconds=60, sleep_seconds=0, storage=storage
        )

        # Should immediately be over limit
        is_allowed = await rate_limiter.is_allowed('test_user')
        assert is_allowed is False

    @pytest.mark.asyncio
    async def test_edge_case_zero_time_window(self):
        """Test rate limiter with zero time window."""
        storage = InMemoryRateLimiterStorage()
        rate_limiter = UserBasedRateLimiter(
            requests=5, seconds=0, sleep_seconds=0, storage=storage
        )

        # With zero time window, all requests should be considered old
        is_allowed = await rate_limiter.is_allowed('test_user')
        # Should still be allowed as the request is added after cleaning
        assert is_allowed is True


if __name__ == '__main__':
    pytest.main([__file__])
