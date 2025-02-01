# OpenHands Caching and Performance Strategies Guide

This guide covers caching patterns, performance optimization strategies, and resource management for OpenHands systems.

## Table of Contents
1. [Cache System](#cache-system)
2. [Memory Management](#memory-management)
3. [Resource Pooling](#resource-pooling)
4. [Performance Optimization](#performance-optimization)

## Cache System

### 1. Multi-Level Cache

Implementation of multi-level caching system:

```python
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
import asyncio
import hashlib
import json

class CacheLevel:
    """Cache level definition"""
    
    def __init__(
        self,
        name: str,
        ttl: int,
        max_size: Optional[int] = None
    ):
        self.name = name
        self.ttl = ttl
        self.max_size = max_size
        self.data: Dict[str, Tuple[Any, datetime]] = {}
        self.hits = 0
        self.misses = 0
        
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if key not in self.data:
            self.misses += 1
            return None
            
        value, expiry = self.data[key]
        if datetime.now() > expiry:
            del self.data[key]
            self.misses += 1
            return None
            
        self.hits += 1
        return value
        
    async def set(self, key: str, value: Any):
        """Set cache value"""
        # Check size limit
        if (self.max_size and
            len(self.data) >= self.max_size):
            # Remove oldest entry
            oldest_key = min(
                self.data.keys(),
                key=lambda k: self.data[k][1]
            )
            del self.data[oldest_key]
            
        self.data[key] = (
            value,
            datetime.now() + timedelta(seconds=self.ttl)
        )
        
    def clear(self):
        """Clear cache level"""
        self.data.clear()
        
    @property
    def hit_ratio(self) -> float:
        """Calculate hit ratio"""
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return self.hits / total

class MultiLevelCache:
    """Multi-level cache system"""
    
    def __init__(self):
        self.levels: List[CacheLevel] = []
        
    def add_level(
        self,
        name: str,
        ttl: int,
        max_size: Optional[int] = None
    ):
        """Add cache level"""
        level = CacheLevel(name, ttl, max_size)
        self.levels.append(level)
        
    async def get(
        self,
        key: str,
        compute_func: Optional[callable] = None
    ) -> Optional[Any]:
        """Get value from cache"""
        # Generate cache key
        cache_key = self._generate_key(key)
        
        # Check each level
        for level in self.levels:
            value = await level.get(cache_key)
            if value is not None:
                # Update higher levels
                await self._update_levels(
                    cache_key,
                    value,
                    level
                )
                return value
                
        # Compute if missing
        if compute_func:
            value = await compute_func()
            await self.set(cache_key, value)
            return value
            
        return None
        
    async def set(self, key: str, value: Any):
        """Set cache value"""
        cache_key = self._generate_key(key)
        
        # Update all levels
        for level in self.levels:
            await level.set(cache_key, value)
            
    async def invalidate(self, key: str):
        """Invalidate cache entry"""
        cache_key = self._generate_key(key)
        
        for level in self.levels:
            if cache_key in level.data:
                del level.data[cache_key]
                
    def get_stats(self) -> dict:
        """Get cache statistics"""
        return {
            level.name: {
                'size': len(level.data),
                'hits': level.hits,
                'misses': level.misses,
                'hit_ratio': level.hit_ratio
            }
            for level in self.levels
        }
        
    async def _update_levels(
        self,
        key: str,
        value: Any,
        found_level: CacheLevel
    ):
        """Update higher cache levels"""
        found_idx = self.levels.index(found_level)
        
        for level in self.levels[:found_idx]:
            await level.set(key, value)
            
    def _generate_key(self, key: Any) -> str:
        """Generate cache key"""
        if isinstance(key, str):
            return hashlib.md5(key.encode()).hexdigest()
        return hashlib.md5(
            json.dumps(key).encode()
        ).hexdigest()
```

### 2. Distributed Cache

Implementation of distributed caching:

```python
class DistributedCache:
    """Distributed cache system"""
    
    def __init__(
        self,
        redis_url: str,
        prefix: str = "cache:"
    ):
        self.redis = aioredis.from_url(redis_url)
        self.prefix = prefix
        self.local_cache = {}
        self.local_ttl = 60  # 1 minute
        
    async def get(
        self,
        key: str,
        default: Any = None
    ) -> Any:
        """Get cached value"""
        cache_key = f"{self.prefix}{key}"
        
        # Check local cache
        if cache_key in self.local_cache:
            value, expiry = self.local_cache[cache_key]
            if datetime.now() < expiry:
                return value
            del self.local_cache[cache_key]
            
        # Get from Redis
        value = await self.redis.get(cache_key)
        if value is None:
            return default
            
        # Update local cache
        try:
            value = json.loads(value)
            self.local_cache[cache_key] = (
                value,
                datetime.now() + timedelta(seconds=self.local_ttl)
            )
            return value
        except json.JSONDecodeError:
            return value
            
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ):
        """Set cached value"""
        cache_key = f"{self.prefix}{key}"
        
        # Update Redis
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            await self.redis.set(
                cache_key,
                value,
                ex=ttl
            )
        except Exception as e:
            logger.error(f"Cache set failed: {e}")
            
        # Update local cache
        self.local_cache[cache_key] = (
            value,
            datetime.now() + timedelta(seconds=self.local_ttl)
        )
        
    async def delete(self, key: str):
        """Delete cached value"""
        cache_key = f"{self.prefix}{key}"
        
        # Delete from Redis
        await self.redis.delete(cache_key)
        
        # Delete from local cache
        if cache_key in self.local_cache:
            del self.local_cache[cache_key]
            
    async def clear(self):
        """Clear all cached values"""
        # Clear Redis
        keys = await self.redis.keys(f"{self.prefix}*")
        if keys:
            await self.redis.delete(*keys)
            
        # Clear local cache
        self.local_cache.clear()
```

## Memory Management

### 1. Memory Pool

Implementation of memory pooling:

```python
class MemoryPool:
    """Memory pool for object reuse"""
    
    def __init__(
        self,
        max_size: int = 1000,
        cleanup_interval: int = 300
    ):
        self.max_size = max_size
        self.cleanup_interval = cleanup_interval
        self.pools: Dict[type, List[Any]] = {}
        self.last_cleanup = datetime.now()
        self.stats = {
            'created': 0,
            'reused': 0,
            'discarded': 0
        }
        
    async def acquire(
        self,
        obj_type: type,
        *args,
        **kwargs
    ) -> Any:
        """Acquire object from pool"""
        # Check cleanup
        await self._check_cleanup()
        
        # Get pool for type
        pool = self.pools.get(obj_type, [])
        
        if pool:
            # Reuse object
            obj = pool.pop()
            if hasattr(obj, 'reset'):
                obj.reset()
            self.stats['reused'] += 1
            return obj
            
        # Create new object
        obj = obj_type(*args, **kwargs)
        self.stats['created'] += 1
        return obj
        
    async def release(
        self,
        obj: Any
    ):
        """Release object back to pool"""
        obj_type = type(obj)
        
        if obj_type not in self.pools:
            self.pools[obj_type] = []
            
        pool = self.pools[obj_type]
        
        if len(pool) < self.max_size:
            pool.append(obj)
        else:
            self.stats['discarded'] += 1
            
    async def _check_cleanup(self):
        """Check if cleanup needed"""
        now = datetime.now()
        if (now - self.last_cleanup).seconds >= self.cleanup_interval:
            await self._cleanup()
            self.last_cleanup = now
            
    async def _cleanup(self):
        """Clean up pools"""
        for pool in self.pools.values():
            while len(pool) > self.max_size:
                pool.pop()
                self.stats['discarded'] += 1
```

## Resource Pooling

### 1. Connection Pool

Implementation of connection pooling:

```python
class PooledConnection:
    """Pooled connection wrapper"""
    
    def __init__(
        self,
        connection: Any,
        pool: 'ConnectionPool'
    ):
        self.connection = connection
        self.pool = pool
        self.in_use = False
        self.last_used = None
        
    async def acquire(self):
        """Acquire connection"""
        self.in_use = True
        self.last_used = datetime.now()
        return self.connection
        
    async def release(self):
        """Release connection"""
        self.in_use = False
        await self.pool.release(self)

class ConnectionPool:
    """Connection pool implementation"""
    
    def __init__(
        self,
        create_connection: callable,
        min_size: int = 1,
        max_size: int = 10,
        max_idle_time: int = 300
    ):
        self.create_connection = create_connection
        self.min_size = min_size
        self.max_size = max_size
        self.max_idle_time = max_idle_time
        self.connections: List[PooledConnection] = []
        self.semaphore = asyncio.Semaphore(max_size)
        
    async def initialize(self):
        """Initialize connection pool"""
        # Create minimum connections
        for _ in range(self.min_size):
            conn = await self._create_connection()
            self.connections.append(conn)
            
    async def acquire(self) -> PooledConnection:
        """Acquire connection from pool"""
        async with self.semaphore:
            # Find available connection
            for conn in self.connections:
                if not conn.in_use:
                    return await conn.acquire()
                    
            # Create new connection if possible
            if len(self.connections) < self.max_size:
                conn = await self._create_connection()
                self.connections.append(conn)
                return await conn.acquire()
                
            # Wait for connection
            while True:
                for conn in self.connections:
                    if not conn.in_use:
                        return await conn.acquire()
                await asyncio.sleep(0.1)
                
    async def release(self, conn: PooledConnection):
        """Release connection back to pool"""
        conn.in_use = False
        self.semaphore.release()
        
    async def cleanup(self):
        """Clean up idle connections"""
        now = datetime.now()
        
        # Keep minimum connections
        if len(self.connections) <= self.min_size:
            return
            
        # Remove idle connections
        for conn in self.connections[:]:
            if (not conn.in_use and
                conn.last_used and
                (now - conn.last_used).seconds > self.max_idle_time):
                self.connections.remove(conn)
                await self._close_connection(conn)
                
    async def _create_connection(self) -> PooledConnection:
        """Create new connection"""
        conn = await self.create_connection()
        return PooledConnection(conn, self)
        
    async def _close_connection(
        self,
        conn: PooledConnection
    ):
        """Close connection"""
        if hasattr(conn.connection, 'close'):
            await conn.connection.close()
```

## Performance Optimization

### 1. Performance Monitor

Implementation of performance monitoring:

```python
class PerformanceMetric:
    """Performance metric tracking"""
    
    def __init__(self, name: str):
        self.name = name
        self.values: List[float] = []
        self.start_time = None
        
    def start(self):
        """Start timing"""
        self.start_time = time.time()
        
    def stop(self):
        """Stop timing"""
        if self.start_time:
            duration = time.time() - self.start_time
            self.values.append(duration)
            self.start_time = None
            
    @property
    def average(self) -> float:
        """Calculate average"""
        if not self.values:
            return 0.0
        return sum(self.values) / len(self.values)
        
    @property
    def percentile_95(self) -> float:
        """Calculate 95th percentile"""
        if not self.values:
            return 0.0
        return sorted(self.values)[
            int(len(self.values) * 0.95)
        ]

class PerformanceMonitor:
    """Performance monitoring system"""
    
    def __init__(self):
        self.metrics: Dict[str, PerformanceMetric] = {}
        
    def start_metric(self, name: str):
        """Start metric timing"""
        if name not in self.metrics:
            self.metrics[name] = PerformanceMetric(name)
        self.metrics[name].start()
        
    def stop_metric(self, name: str):
        """Stop metric timing"""
        if name in self.metrics:
            self.metrics[name].stop()
            
    def get_metrics(self) -> dict:
        """Get performance metrics"""
        return {
            name: {
                'count': len(metric.values),
                'average': metric.average,
                'p95': metric.percentile_95
            }
            for name, metric in self.metrics.items()
        }
        
    async def monitor_function(
        self,
        name: str,
        func: callable,
        *args,
        **kwargs
    ) -> Any:
        """Monitor function performance"""
        self.start_metric(name)
        try:
            return await func(*args, **kwargs)
        finally:
            self.stop_metric(name)
```

Remember to:
- Implement proper caching
- Manage memory efficiently
- Pool resources appropriately
- Monitor performance
- Optimize resource usage
- Handle cleanup properly
- Document optimization strategies