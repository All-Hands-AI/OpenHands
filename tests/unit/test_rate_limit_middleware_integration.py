import asyncio
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from openhands.server.middleware import (
    IntegrationRateLimitMiddleware,
    UserBasedRateLimiter,
)
from openhands.server.utils.ratelimit_storage import (
    InMemoryRateLimiterStorage,
    create_rate_limiter_storage,
)


class TestIntegrationRateLimitMiddleware:
    """Test suite for IntegrationRateLimitMiddleware."""

    @pytest.fixture
    def app(self):
        """Create a FastAPI app for testing."""
        app = FastAPI()

        @app.get('/api/v1/integration/test')
        async def test_endpoint():
            return {'message': 'success'}

        @app.get('/api/other/test')
        async def other_endpoint():
            return {'message': 'other'}

        return app

    @pytest.fixture
    def rate_limiter(self):
        """Create a rate limiter for testing."""
        storage = InMemoryRateLimiterStorage()
        return UserBasedRateLimiter(
            requests=3, seconds=60, sleep_seconds=0, storage=storage
        )

    @pytest.fixture
    def app_with_middleware(self, app, rate_limiter):
        """Create app with rate limiting middleware."""
        app.add_middleware(IntegrationRateLimitMiddleware, rate_limiter=rate_limiter)
        return app

    def create_mock_request(self, path: str, user_id: str = 'test_user'):
        """Create a mock request with user state."""
        request = MagicMock(spec=Request)
        request.url.path = path
        request.state = MagicMock()
        request.state.user_id = user_id
        return request

    @pytest.mark.asyncio
    async def test_middleware_skips_non_integration_routes(self, rate_limiter):
        """Test that middleware skips non-integration API routes."""
        middleware = IntegrationRateLimitMiddleware(None, rate_limiter)

        request = self.create_mock_request('/api/other/test')
        call_next = AsyncMock(return_value=JSONResponse({'message': 'success'}))

        response = await middleware.dispatch(request, call_next)

        # Should call next without rate limiting
        call_next.assert_called_once_with(request)
        assert response.body == b'{"message":"success"}'

    @pytest.mark.asyncio
    async def test_middleware_applies_to_integration_routes(self, rate_limiter):
        """Test that middleware applies rate limiting to integration routes."""
        middleware = IntegrationRateLimitMiddleware(None, rate_limiter)

        request = self.create_mock_request('/api/v1/integration/test')
        call_next = AsyncMock(return_value=JSONResponse({'message': 'success'}))

        response = await middleware.dispatch(request, call_next)

        # Should call next (request allowed)
        call_next.assert_called_once_with(request)
        assert response.body == b'{"message":"success"}'

    @pytest.mark.asyncio
    async def test_middleware_blocks_over_limit_requests(self, rate_limiter):
        """Test that middleware blocks requests over the rate limit."""
        middleware = IntegrationRateLimitMiddleware(None, rate_limiter)
        request = self.create_mock_request('/api/v1/integration/test')
        call_next = AsyncMock(return_value=JSONResponse({'message': 'success'}))

        # Make requests up to the limit (limit is 3)
        # First 3 requests should succeed
        for _ in range(3):
            await middleware.dispatch(request, call_next)

        # 4th request should be blocked (3 + 1 = 4 > 3)
        response = await middleware.dispatch(request, call_next)

        # Should call next 3 times, then block the 4th
        assert call_next.call_count == 3  # Only first 3 calls succeeded
        assert response.status_code == 429
        assert 'Rate limit exceeded' in str(response.body)

    @pytest.mark.asyncio
    async def test_middleware_missing_user_id(self, rate_limiter):
        """Test middleware behavior when user_id is missing."""
        middleware = IntegrationRateLimitMiddleware(None, rate_limiter)

        request = self.create_mock_request('/api/v1/integration/test')
        request.state.user_id = None  # No user ID
        call_next = AsyncMock()

        response = await middleware.dispatch(request, call_next)

        # Should return 401 unauthorized
        assert response.status_code == 401
        assert 'Authentication required' in str(response.body)
        call_next.assert_not_called()

    @pytest.mark.asyncio
    async def test_middleware_no_state_attribute(self, rate_limiter):
        """Test middleware behavior when request has no state."""
        middleware = IntegrationRateLimitMiddleware(None, rate_limiter)

        request = MagicMock(spec=Request)
        request.url.path = '/api/v1/integration/test'
        # No state attribute
        delattr(request, 'state')
        call_next = AsyncMock()

        response = await middleware.dispatch(request, call_next)

        # Should return 401 unauthorized
        assert response.status_code == 401
        call_next.assert_not_called()

    @pytest.mark.asyncio
    async def test_middleware_different_users_isolated(self, rate_limiter):
        """Test that different users have isolated rate limits."""
        middleware = IntegrationRateLimitMiddleware(None, rate_limiter)
        call_next = AsyncMock(return_value=JSONResponse({'message': 'success'}))

        # Fill up user1's limit
        request_user1 = self.create_mock_request('/api/v1/integration/test', 'user1')
        for _ in range(4):  # 3 + 1 over limit for user1
            await middleware.dispatch(request_user1, call_next)

        # User1 should be rate limited
        response = await middleware.dispatch(request_user1, call_next)
        assert response.status_code == 429

        # User2 should still be allowed
        request_user2 = self.create_mock_request('/api/v1/integration/test', 'user2')
        response = await middleware.dispatch(request_user2, call_next)
        assert response.status_code != 429

    @pytest.mark.asyncio
    async def test_rate_limiter_storage_error_handling(self):
        """Test middleware behavior when storage operations fail."""
        # Create a mock storage that fails
        mock_storage = AsyncMock()
        mock_storage.clean_old_requests = AsyncMock(
            side_effect=Exception('Storage error')
        )
        mock_storage.add_request = AsyncMock(side_effect=Exception('Storage error'))
        mock_storage.get_request_count = AsyncMock(
            side_effect=Exception('Storage error')
        )

        rate_limiter = UserBasedRateLimiter(
            requests=3, seconds=60, sleep_seconds=0, storage=mock_storage
        )

        middleware = IntegrationRateLimitMiddleware(None, rate_limiter)
        request = self.create_mock_request('/api/v1/integration/test')
        call_next = AsyncMock(return_value=JSONResponse({'message': 'success'}))

        # Should handle storage errors gracefully
        response = await middleware.dispatch(request, call_next)

        # The exact behavior depends on implementation, but should not crash
        assert response is not None
        assert isinstance(response.status_code, int)


class TestRateLimitMiddlewareConfiguration:
    """Test suite for rate limiting configuration and setup."""

    @pytest.mark.asyncio
    async def test_create_memory_storage_from_env(self):
        """Test creating memory storage from environment variables."""
        with patch.dict(os.environ, {'RATE_LIMITER_STORAGE_TYPE': 'memory'}):
            storage = create_rate_limiter_storage(
                storage_type=os.getenv('RATE_LIMITER_STORAGE_TYPE', 'memory')
            )
            assert isinstance(storage, InMemoryRateLimiterStorage)

    @pytest.mark.asyncio
    async def test_rate_limiter_configuration_with_custom_settings(self):
        """Test rate limiter with custom configuration."""
        storage = InMemoryRateLimiterStorage()
        rate_limiter = UserBasedRateLimiter(
            requests=100, seconds=3600, sleep_seconds=2, storage=storage
        )

        assert rate_limiter.requests == 100
        assert rate_limiter.seconds == 3600
        assert rate_limiter.sleep_seconds == 2
        assert rate_limiter.storage is storage

    @pytest.mark.asyncio
    async def test_middleware_setup_integration(self):
        """Test complete middleware setup as it would be in the application."""
        # Simulate the setup from listen.py
        RATE_LIMITER_STORAGE_TYPE = 'memory'
        RATE_LIMITER_HOST_URL = None
        RATE_LIMITER_HOST_PASSWORD = None
        RATE_LIMITER_KEY_PREFIX = None

        rate_limiter_storage = create_rate_limiter_storage(
            storage_type=RATE_LIMITER_STORAGE_TYPE,
            host_url=RATE_LIMITER_HOST_URL,
            host_password=RATE_LIMITER_HOST_PASSWORD,
            key_prefix=RATE_LIMITER_KEY_PREFIX,
        )

        integration_rate_limiter = UserBasedRateLimiter(
            requests=10, seconds=60, sleep_seconds=0, storage=rate_limiter_storage
        )

        # Verify setup
        assert isinstance(rate_limiter_storage, InMemoryRateLimiterStorage)
        assert integration_rate_limiter.requests == 10
        assert integration_rate_limiter.seconds == 60
        assert integration_rate_limiter.storage is rate_limiter_storage

    @pytest.mark.asyncio
    async def test_environment_variable_defaults(self):
        """Test that environment variables have sensible defaults."""
        # Test default values as they would be used in listen.py
        RATE_LIMITER_STORAGE_TYPE = os.getenv('RATE_LIMITER_STORAGE_TYPE', 'memory')
        RATE_LIMITER_HOST_URL = os.getenv('RATE_LIMITER_HOST_URL')
        RATE_LIMITER_HOST_PASSWORD = os.getenv('RATE_LIMITER_HOST_PASSWORD')
        RATE_LIMITER_KEY_PREFIX = os.getenv('RATE_LIMITER_KEY_PREFIX')

        assert RATE_LIMITER_STORAGE_TYPE == 'memory'
        assert not RATE_LIMITER_HOST_URL
        assert not RATE_LIMITER_HOST_PASSWORD
        assert not RATE_LIMITER_KEY_PREFIX

        # Should create memory storage with these defaults
        storage = create_rate_limiter_storage(
            storage_type=RATE_LIMITER_STORAGE_TYPE,
            host_url=RATE_LIMITER_HOST_URL,
            host_password=RATE_LIMITER_HOST_PASSWORD,
            key_prefix=RATE_LIMITER_KEY_PREFIX,
        )
        assert isinstance(storage, InMemoryRateLimiterStorage)


class TestRateLimitingBehavior:
    """Test suite for end-to-end rate limiting behavior."""

    @pytest.mark.asyncio
    async def test_rate_limit_time_window_behavior(self):
        """Test rate limiting behavior over time windows."""
        storage = InMemoryRateLimiterStorage()
        rate_limiter = UserBasedRateLimiter(
            requests=2,
            seconds=1,  # 1 second window
            sleep_seconds=0,
            storage=storage,
        )

        middleware = IntegrationRateLimitMiddleware(None, rate_limiter)
        request = MagicMock(spec=Request)
        request.url.path = '/api/v1/integration/test'
        request.state = MagicMock()
        request.state.user_id = 'test_user'
        call_next = AsyncMock(return_value=JSONResponse({'message': 'success'}))

        # First two requests should be allowed (limit is 2)
        response1 = await middleware.dispatch(request, call_next)
        response2 = await middleware.dispatch(request, call_next)
        assert response1.status_code == 200
        assert response2.status_code == 200

        # Third request should be blocked (2 + 1 = 3 > 2)
        response3 = await middleware.dispatch(request, call_next)
        assert response3.status_code == 429  # Over limit, blocked

        # Fourth request should also be blocked
        response4 = await middleware.dispatch(request, call_next)
        assert response4.status_code == 429

        # Wait for time window to reset
        await asyncio.sleep(1.1)

        # Should be allowed again
        response5 = await middleware.dispatch(request, call_next)
        assert response5.status_code == 200

    @pytest.mark.asyncio
    async def test_concurrent_requests_same_user(self):
        """Test concurrent requests from the same user."""
        storage = InMemoryRateLimiterStorage()
        rate_limiter = UserBasedRateLimiter(
            requests=5, seconds=60, sleep_seconds=0, storage=storage
        )

        middleware = IntegrationRateLimitMiddleware(None, rate_limiter)

        async def make_request():
            request = MagicMock(spec=Request)
            request.url.path = '/api/v1/integration/test'
            request.state = MagicMock()
            request.state.user_id = 'test_user'
            call_next = AsyncMock(return_value=JSONResponse({'message': 'success'}))
            return await middleware.dispatch(request, call_next)

        # Make 10 concurrent requests
        tasks = [make_request() for _ in range(10)]
        responses = await asyncio.gather(*tasks)

        # Some should be allowed, some should be rate limited
        success_count = sum(1 for r in responses if r.status_code == 200)
        rate_limited_count = sum(1 for r in responses if r.status_code == 429)

        assert success_count > 0
        assert rate_limited_count > 0
        assert success_count + rate_limited_count == 10


if __name__ == '__main__':
    pytest.main([__file__])
