import json
from abc import ABC, abstractmethod
from collections import defaultdict
from datetime import datetime

from openhands.core.logger import openhands_logger as logger

try:
    import redis.asyncio as redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning(
        'Redis not available. Rate limiting will use in-memory storage only.'
    )


class RateLimiterStorage(ABC):
    """Abstract interface for rate limiter storage backends."""

    @abstractmethod
    async def get_requests(self, key: str) -> list[datetime]:
        """Get list of request timestamps for a user."""
        pass

    @abstractmethod
    async def add_request(self, key: str, timestamp: datetime) -> None:
        """Add a request timestamp for a user."""
        pass

    @abstractmethod
    async def clean_old_requests(self, key: str, cutoff: datetime) -> None:
        """Remove requests older than cutoff time."""
        pass

    @abstractmethod
    async def get_request_count(self, key: str) -> int:
        """Get current request count for a user."""
        pass


class InMemoryRateLimiterStorage(RateLimiterStorage):
    """In-memory storage backend for rate limiting."""

    def __init__(self):
        self.history: dict[str, list[datetime]] = defaultdict(list)

    async def get_requests(self, key: str) -> list[datetime]:
        return self.history[key].copy()

    async def add_request(self, key: str, timestamp: datetime) -> None:
        self.history[key].append(timestamp)

    async def clean_old_requests(self, key: str, cutoff: datetime) -> None:
        self.history[key] = [ts for ts in self.history[key] if ts > cutoff]

    async def get_request_count(self, key: str) -> int:
        return len(self.history[key])


class RedisRateLimiterStorage(RateLimiterStorage):
    """Redis storage backend for rate limiting."""

    def __init__(
        self,
        redis_url: str | None = None,
        redis_password: str | None = None,
        key_prefix: str | None = None,
    ):
        if not REDIS_AVAILABLE:
            raise ImportError(
                "Redis is not available. Install 'redis' package to use Redis storage."
            )
        if not redis_url:
            raise ValueError('Redis URL is required')
        if not key_prefix:
            raise ValueError('Key prefix is required')

        self.redis_url = redis_url
        self.redis_password = redis_password
        self.key_prefix = key_prefix
        self._redis_client = self.__init_client()

    def __init_client(self):
        return redis.from_url(
            self.redis_url, password=self.redis_password, decode_responses=True
        )

    async def _get_redis_client(self):
        """Get or create Redis client."""
        if self._redis_client is None:
            self._redis_client = self.__init_client()
        return self._redis_client

    def _get_key(self, user_id: str) -> str:
        """Get Redis key for user."""
        return f'{self.key_prefix}:{user_id}'

    async def get_requests(self, key: str) -> list[datetime]:
        client = await self._get_redis_client()
        redis_key = self._get_key(key)

        try:
            data = await client.get(redis_key)
            if data:
                timestamps = json.loads(data)
                return [datetime.fromisoformat(ts) for ts in timestamps]
            return []
        except Exception as e:
            logger.error(f'Failed to get requests from Redis for user {key}: {e}')
            return []

    async def add_request(self, key: str, timestamp: datetime) -> None:
        client = await self._get_redis_client()
        redis_key = self._get_key(key)

        try:
            # Get existing requests
            current_requests = await self.get_requests(key)
            current_requests.append(timestamp)

            # Store back to Redis
            timestamps = [ts.isoformat() for ts in current_requests]
            await client.set(
                redis_key, json.dumps(timestamps), ex=3600
            )  # 1 hour expiry
        except Exception as e:
            logger.error(f'Failed to add request to Redis for user {key}: {e}')

    async def clean_old_requests(self, key: str, cutoff: datetime) -> None:
        client = await self._get_redis_client()
        redis_key = self._get_key(key)

        try:
            current_requests = await self.get_requests(key)
            cleaned_requests = [ts for ts in current_requests if ts > cutoff]

            if cleaned_requests:
                timestamps = [ts.isoformat() for ts in cleaned_requests]
                await client.set(redis_key, json.dumps(timestamps), ex=3600)
            else:
                await client.delete(redis_key)
        except Exception as e:
            logger.error(f'Failed to clean old requests from Redis for user {key}: {e}')

    async def get_request_count(self, key: str) -> int:
        requests = await self.get_requests(key)
        return len(requests)

    async def close(self):
        """Close Redis connection."""
        if self._redis_client:
            await self._redis_client.close()


def create_rate_limiter_storage(
    storage_type: str = 'memory',
    host_url: str | None = 'redis://localhost:6379',
    host_password: str | None = None,
    key_prefix: str | None = None,
) -> RateLimiterStorage:
    """
    Create a rate limiter storage backend based on configuration.

    Args:
        storage_type: Type of storage ("memory" or "redis")
        redis_url: Redis connection URL (for redis storage)
        redis_password: Redis password (for redis storage)
        key_prefix: Key prefix for Redis keys (for redis storage)

    Returns:
        RateLimiterStorage instance
    """
    if storage_type.lower() == 'redis':
        if not REDIS_AVAILABLE:
            logger.warning('Redis not available, falling back to in-memory storage')
            return InMemoryRateLimiterStorage()
        return RedisRateLimiterStorage(host_url, host_password, key_prefix)
    else:
        return InMemoryRateLimiterStorage()
