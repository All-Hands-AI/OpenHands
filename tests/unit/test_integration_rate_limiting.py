import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import Request
from fastapi.responses import JSONResponse

from openhands.server.middleware import (
    IntegrationRateLimitMiddleware,
    UserBasedRateLimiter,
)


class TestUserBasedRateLimiter:
    """Test the UserBasedRateLimiter class."""

    def test_initialization_with_defaults(self):
        """Test that the rate limiter initializes with correct default values."""
        limiter = UserBasedRateLimiter()
        assert limiter.requests == 60
        assert limiter.seconds == 60
        assert limiter.sleep_seconds == 1
        assert len(limiter.storage.history) == 0

    def test_initialization_with_custom_values(self):
        """Test that the rate limiter initializes correctly with custom values."""
        limiter = UserBasedRateLimiter(requests=10, seconds=30, sleep_seconds=2)
        assert limiter.requests == 10
        assert limiter.seconds == 30
        assert limiter.sleep_seconds == 2
        assert len(limiter.storage.history) == 0

    @pytest.mark.asyncio
    async def test_allows_requests_under_limit(self):
        """Test that requests under the limit are allowed."""
        limiter = UserBasedRateLimiter(requests=5, seconds=60, sleep_seconds=0)
        user_id = 'test_user_123'

        # Should allow first 5 requests
        for i in range(5):
            result = await limiter.is_allowed(user_id)
            assert result is True

        # Verify history is tracked correctly
        assert len(limiter.storage.history[user_id]) == 5

    @pytest.mark.asyncio
    async def test_blocks_requests_over_limit(self):
        """Test that requests over the limit are blocked."""
        limiter = UserBasedRateLimiter(requests=2, seconds=60, sleep_seconds=0)
        user_id = 'test_user_456'

        # Allow first 2 requests
        for i in range(2):
            result = await limiter.is_allowed(user_id)
            assert result is True

        # Block the 3rd request
        result = await limiter.is_allowed(user_id)
        assert result is False

        # Verify history still contains the blocked request
        assert len(limiter.storage.history[user_id]) == 3

    @pytest.mark.asyncio
    async def test_blocks_requests_over_double_limit(self):
        """Test that requests over double the limit are immediately blocked."""
        limiter = UserBasedRateLimiter(requests=2, seconds=60, sleep_seconds=1)
        user_id = 'test_user_789'

        # Manually add requests to exceed double limit
        now = datetime.now()
        limiter.storage.history[user_id] = [now] * 5  # 5 requests when limit is 2

        result = await limiter.is_allowed(user_id)
        assert result is False

    @pytest.mark.asyncio
    async def test_sleep_on_moderate_excess(self):
        """Test that requests over limit but under double limit sleep when configured."""
        limiter = UserBasedRateLimiter(requests=2, seconds=60, sleep_seconds=0.1)
        user_id = 'test_user_sleep'

        # Allow first 2 requests
        for i in range(2):
            result = await limiter.is_allowed(user_id)
            assert result is True

        # 3rd request should sleep but then be allowed
        start_time = datetime.now()
        result = await limiter.is_allowed(user_id)
        end_time = datetime.now()

        assert result is True
        # Should have slept for approximately 0.1 seconds
        assert abs((end_time - start_time).total_seconds() - 0.1) < 0.01

    @pytest.mark.asyncio
    async def test_different_users_have_separate_limits(self):
        """Test that different users have independent rate limits."""
        limiter = UserBasedRateLimiter(requests=2, seconds=60, sleep_seconds=0)

        user1 = 'user_1'
        user2 = 'user_2'

        # Each user should get their own limit
        for i in range(2):
            assert await limiter.is_allowed(user1) is True
            assert await limiter.is_allowed(user2) is True

        # Both users should be blocked on their 3rd request
        assert await limiter.is_allowed(user1) is False
        assert await limiter.is_allowed(user2) is False

        # Verify separate history tracking
        assert len(limiter.storage.history[user1]) == 3
        assert len(limiter.storage.history[user2]) == 3

    @pytest.mark.asyncio
    async def test_rejects_empty_user_id(self):
        """Test that empty user IDs are rejected."""
        limiter = UserBasedRateLimiter(requests=10, seconds=60)

        assert await limiter.is_allowed('') is False
        assert await limiter.is_allowed(None) is False

    @pytest.mark.asyncio
    async def test_cleans_old_requests(self):
        """Test that old requests are cleaned up properly."""
        limiter = UserBasedRateLimiter(requests=5, seconds=1)  # 1 second window
        user_id = 'test_user'

        # Add some old requests
        old_time = datetime.now() - timedelta(seconds=2)
        recent_time = datetime.now() - timedelta(seconds=0.5)
        limiter.storage.history[user_id] = [old_time, old_time, recent_time]

        # Clean old requests
        cutoff = datetime.now() - timedelta(seconds=1)
        await limiter.storage.clean_old_requests(user_id, cutoff)

        # Should only have 1 recent request left
        assert len(limiter.storage.history[user_id]) == 1
        assert limiter.storage.history[user_id][0] == recent_time

    @pytest.mark.asyncio
    async def test_rate_limit_window_reset(self):
        """Test that rate limits reset after the time window passes."""
        limiter = UserBasedRateLimiter(
            requests=2, seconds=1, sleep_seconds=0
        )  # 1 second window
        user_id = 'test_window_reset'

        # Use up the limit
        for i in range(2):
            assert await limiter.is_allowed(user_id) is True

        # Should be blocked
        assert await limiter.is_allowed(user_id) is False

        # Wait for window to reset (1.1 seconds to be safe)
        await asyncio.sleep(1.1)

        # Should be allowed again
        assert await limiter.is_allowed(user_id) is True

    @pytest.mark.asyncio
    async def test_concurrent_requests_same_user(self):
        """Test that concurrent requests from the same user are handled correctly."""
        limiter = UserBasedRateLimiter(requests=3, seconds=60, sleep_seconds=0)
        user_id = 'concurrent_user'

        # Create concurrent requests
        tasks = [limiter.is_allowed(user_id) for _ in range(5)]
        results = await asyncio.gather(*tasks)

        # Should have 3 True and 2 False results
        assert sum(results) == 3
        assert len([r for r in results if not r]) == 2


class TestIntegrationRateLimitMiddleware:
    """Test the IntegrationRateLimitMiddleware class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.rate_limiter = UserBasedRateLimiter(
            requests=2, seconds=60, sleep_seconds=0
        )
        self.middleware = IntegrationRateLimitMiddleware(None, self.rate_limiter)

    @pytest.mark.asyncio
    async def test_ignores_non_integration_routes(self):
        """Test that non-integration routes are not rate limited."""
        non_integration_paths = [
            '/api/v1/conversations',
            '/api/v1/auth',
            '/api/v1/settings',
            '/assets/css/style.css',
            '/api/v2/integration/test',  # Different version
            '/integration/api/v1/test',  # Different order
        ]

        for path in non_integration_paths:
            request = MagicMock(spec=Request)
            request.url.path = path

            call_next = AsyncMock()
            call_next.return_value = 'response'

            result = await self.middleware.dispatch(request, call_next)

            assert result == 'response'
            call_next.assert_called_with(request)
            call_next.reset_mock()

    @pytest.mark.asyncio
    async def test_applies_to_integration_routes(self):
        """Test that integration routes are processed by the middleware."""
        integration_paths = [
            '/api/v1/integration/conversations',
            '/api/v1/integration/conversations/123',
            '/api/v1/integration/other-endpoint',
            '/api/v1/integration/',
        ]

        for i, path in enumerate(integration_paths):
            request = MagicMock(spec=Request)
            request.url.path = path
            # Use different user IDs to avoid rate limiting across tests
            request.state.user_id = f'test_user_{i}'

            call_next = AsyncMock()
            call_next.return_value = 'success'

            result = await self.middleware.dispatch(request, call_next)

            # Should process the request (either allow or rate limit)
            # Since this is the first request for each user, it should be allowed
            assert result == 'success'
            call_next.assert_called_with(request)
            call_next.reset_mock()

    @pytest.mark.asyncio
    async def test_requires_authentication_for_integration_routes(self):
        """Test that integration routes require authentication."""
        request = MagicMock(spec=Request)
        request.url.path = '/api/v1/integration/conversations'
        request.state = MagicMock()
        request.state.user_id = None

        call_next = AsyncMock()

        result = await self.middleware.dispatch(request, call_next)

        assert isinstance(result, JSONResponse)
        assert result.status_code == 401
        call_next.assert_not_called()

    @pytest.mark.asyncio
    async def test_handles_missing_user_state(self):
        """Test that missing user state is handled gracefully."""

        # Create a request object that doesn't have a state attribute
        class MockRequest:
            def __init__(self):
                self.url = MagicMock()
                self.url.path = '/api/v1/integration/conversations'

        request = MockRequest()
        call_next = AsyncMock()

        with patch('openhands.server.middleware.logger') as mock_logger:
            result = await self.middleware.dispatch(request, call_next)

            assert isinstance(result, JSONResponse)
            assert result.status_code == 401
            mock_logger.warning.assert_called_once()
            call_next.assert_not_called()

    @pytest.mark.asyncio
    async def test_allows_requests_under_limit(self):
        """Test that requests under the rate limit are allowed."""
        request = MagicMock(spec=Request)
        request.url.path = '/api/v1/integration/conversations'
        request.state.user_id = 'test_user'

        call_next = AsyncMock()
        call_next.return_value = 'success_response'

        result = await self.middleware.dispatch(request, call_next)

        assert result == 'success_response'
        call_next.assert_called_once_with(request)

    @pytest.mark.asyncio
    async def test_blocks_requests_over_limit(self):
        """Test that requests over the rate limit are blocked."""
        request = MagicMock(spec=Request)
        request.url.path = '/api/v1/integration/conversations'
        request.state.user_id = 'test_user'

        call_next = AsyncMock()
        call_next.return_value = 'success_response'

        # First 2 requests should pass
        for i in range(2):
            result = await self.middleware.dispatch(request, call_next)
            assert result == 'success_response'

        # 3rd request should be blocked
        with patch('openhands.server.middleware.logger') as mock_logger:
            result = await self.middleware.dispatch(request, call_next)

            assert isinstance(result, JSONResponse)
            assert result.status_code == 429
            assert 'Rate limit exceeded' in str(result.body)
            assert 'Retry-After' in result.headers
            assert result.headers['Retry-After'] == '60'  # Default seconds
            mock_logger.warning.assert_called_with(
                'Rate limit exceeded for user test_user'
            )

    @pytest.mark.asyncio
    async def test_rate_limit_response_content(self):
        """Test the content and headers of rate limit responses."""
        # Exhaust the rate limit first
        request = MagicMock(spec=Request)
        request.url.path = '/api/v1/integration/conversations'
        request.state.user_id = 'test_user_response'

        call_next = AsyncMock()

        # Use up the limit
        for i in range(2):
            await self.middleware.dispatch(request, call_next)

        # Next request should be rate limited
        result = await self.middleware.dispatch(request, call_next)

        assert isinstance(result, JSONResponse)
        assert result.status_code == 429

        # Check response body
        response_body = result.body.decode('utf-8')
        assert 'Rate limit exceeded' in response_body
        assert 'retry_after' in response_body

        # Check headers
        assert 'Retry-After' in result.headers
        assert result.headers['Retry-After'] == '60'

    @pytest.mark.asyncio
    async def test_different_users_independent_limits(self):
        """Test that different users have independent rate limits."""
        call_next = AsyncMock()
        call_next.return_value = 'success_response'

        # Test with two different users
        for user_id in ['user_1', 'user_2']:
            request = MagicMock(spec=Request)
            request.url.path = '/api/v1/integration/conversations'
            request.state.user_id = user_id

            # Each user should get 2 requests
            for i in range(2):
                result = await self.middleware.dispatch(request, call_next)
                assert result == 'success_response'

            # 3rd request should be blocked for each user
            result = await self.middleware.dispatch(request, call_next)
            assert isinstance(result, JSONResponse)
            assert result.status_code == 429

    @pytest.mark.asyncio
    async def test_custom_rate_limiter_configuration(self):
        """Test middleware with custom rate limiter configuration."""
        custom_limiter = UserBasedRateLimiter(requests=1, seconds=30, sleep_seconds=0)
        custom_middleware = IntegrationRateLimitMiddleware(None, custom_limiter)

        request = MagicMock(spec=Request)
        request.url.path = '/api/v1/integration/test'
        request.state.user_id = 'custom_user'

        call_next = AsyncMock()
        call_next.return_value = 'success'

        # First request should succeed
        result = await custom_middleware.dispatch(request, call_next)
        assert result == 'success'

        # Second request should be blocked
        result = await custom_middleware.dispatch(request, call_next)
        assert isinstance(result, JSONResponse)
        assert result.status_code == 429
        assert result.headers['Retry-After'] == '30'  # Custom seconds value

    @pytest.mark.asyncio
    async def test_middleware_with_exception_in_rate_limiter(self):
        """Test middleware behavior when rate limiter raises an exception."""
        # Create a mock rate limiter that raises an exception
        mock_limiter = MagicMock()
        mock_limiter.is_allowed = AsyncMock(side_effect=Exception('Rate limiter error'))

        middleware = IntegrationRateLimitMiddleware(None, mock_limiter)

        request = MagicMock(spec=Request)
        request.url.path = '/api/v1/integration/test'
        request.state.user_id = 'test_user'

        call_next = AsyncMock()

        # Should raise the exception from the rate limiter
        with pytest.raises(Exception, match='Rate limiter error'):
            await middleware.dispatch(request, call_next)

    @pytest.mark.asyncio
    async def test_empty_string_user_id_handling(self):
        """Test handling of empty string user ID."""
        request = MagicMock(spec=Request)
        request.url.path = '/api/v1/integration/conversations'
        request.state.user_id = ''  # Empty string

        call_next = AsyncMock()

        result = await self.middleware.dispatch(request, call_next)

        # Should be treated as unauthenticated
        assert isinstance(result, JSONResponse)
        assert result.status_code == 401
        call_next.assert_not_called()
