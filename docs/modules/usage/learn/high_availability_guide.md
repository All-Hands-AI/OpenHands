# OpenHands High Availability and Resilience Guide

This guide covers high availability, disaster recovery, and resilience patterns for OpenHands systems.

## Table of Contents
1. [High Availability Patterns](#high-availability-patterns)
2. [Disaster Recovery](#disaster-recovery)
3. [Resilience Patterns](#resilience-patterns)
4. [State Management](#state-management)

## High Availability Patterns

### 1. Node Management

Implementation of high availability node management:

```python
from enum import Enum
from typing import Dict, List, Optional
import asyncio
import json

class NodeState(Enum):
    STARTING = "starting"
    ACTIVE = "active"
    DEGRADED = "degraded"
    FAILING = "failing"
    INACTIVE = "inactive"

class Node:
    """Representation of a system node"""
    
    def __init__(
        self,
        node_id: str,
        host: str,
        port: int
    ):
        self.node_id = node_id
        self.host = host
        self.port = port
        self.state = NodeState.STARTING
        self.last_heartbeat = datetime.now()
        self.metrics = {}
        self.roles = set()
        
    def to_dict(self) -> dict:
        """Convert node to dictionary"""
        return {
            'node_id': self.node_id,
            'host': self.host,
            'port': self.port,
            'state': self.state.value,
            'last_heartbeat': self.last_heartbeat.isoformat(),
            'metrics': self.metrics,
            'roles': list(self.roles)
        }

class ClusterManager:
    """Manage cluster of nodes"""
    
    def __init__(self, redis_url: str):
        self.redis = aioredis.from_url(redis_url)
        self.nodes: Dict[str, Node] = {}
        self.leader_id: Optional[str] = None
        self.node_timeout = 30  # seconds
        
    async def register_node(
        self,
        node: Node,
        roles: List[str] = None
    ):
        """Register node in cluster"""
        node.roles.update(roles or [])
        self.nodes[node.node_id] = node
        
        # Update Redis
        await self.redis.hset(
            'cluster:nodes',
            node.node_id,
            json.dumps(node.to_dict())
        )
        
        # Elect leader if needed
        if not self.leader_id:
            await self._elect_leader()
            
    async def deregister_node(self, node_id: str):
        """Remove node from cluster"""
        if node_id in self.nodes:
            del self.nodes[node_id]
            
        # Update Redis
        await self.redis.hdel('cluster:nodes', node_id)
        
        # Re-elect leader if needed
        if node_id == self.leader_id:
            await self._elect_leader()
            
    async def update_node_state(
        self,
        node_id: str,
        state: NodeState,
        metrics: Optional[dict] = None
    ):
        """Update node state"""
        if node_id not in self.nodes:
            return
            
        node = self.nodes[node_id]
        node.state = state
        node.last_heartbeat = datetime.now()
        
        if metrics:
            node.metrics.update(metrics)
            
        # Update Redis
        await self.redis.hset(
            'cluster:nodes',
            node_id,
            json.dumps(node.to_dict())
        )
        
    async def _elect_leader(self):
        """Elect cluster leader"""
        active_nodes = [
            node for node in self.nodes.values()
            if node.state == NodeState.ACTIVE
        ]
        
        if active_nodes:
            # Select node with oldest heartbeat
            leader = min(
                active_nodes,
                key=lambda n: n.last_heartbeat
            )
            self.leader_id = leader.node_id
            
            # Update Redis
            await self.redis.set(
                'cluster:leader',
                leader.node_id
            )
            
    async def start_monitoring(self):
        """Start cluster monitoring"""
        while True:
            try:
                await self._check_nodes()
                await asyncio.sleep(10)  # Check every 10 seconds
            except Exception as e:
                logger.error(f"Cluster monitoring error: {e}")
                
    async def _check_nodes(self):
        """Check node health"""
        now = datetime.now()
        
        for node_id, node in list(self.nodes.items()):
            # Check node timeout
            if (now - node.last_heartbeat).seconds > self.node_timeout:
                if node.state != NodeState.INACTIVE:
                    await self.update_node_state(
                        node_id,
                        NodeState.INACTIVE
                    )
                    
            # Check node health
            if node.state == NodeState.ACTIVE:
                try:
                    health = await self._check_node_health(node)
                    if not health['healthy']:
                        await self.update_node_state(
                            node_id,
                            NodeState.DEGRADED
                        )
                except Exception:
                    await self.update_node_state(
                        node_id,
                        NodeState.FAILING
                    )
```

### 2. Load Balancing

Implementation of load balancing:

```python
class LoadBalancer:
    """Load balancer for cluster nodes"""
    
    def __init__(self, cluster_manager: ClusterManager):
        self.cluster_manager = cluster_manager
        self.strategy = "round_robin"  # or "least_connections"
        self.current_index = 0
        self.node_connections: Dict[str, int] = {}
        
    async def get_next_node(
        self,
        required_roles: List[str] = None
    ) -> Optional[Node]:
        """Get next available node"""
        available_nodes = [
            node for node in self.cluster_manager.nodes.values()
            if node.state == NodeState.ACTIVE and
            (not required_roles or
             all(role in node.roles for role in required_roles))
        ]
        
        if not available_nodes:
            return None
            
        if self.strategy == "round_robin":
            node = available_nodes[self.current_index % len(available_nodes)]
            self.current_index += 1
            return node
            
        elif self.strategy == "least_connections":
            return min(
                available_nodes,
                key=lambda n: self.node_connections.get(n.node_id, 0)
            )
            
    async def record_connection(self, node_id: str):
        """Record new connection to node"""
        self.node_connections[node_id] = (
            self.node_connections.get(node_id, 0) + 1
        )
        
    async def record_disconnection(self, node_id: str):
        """Record connection termination"""
        if node_id in self.node_connections:
            self.node_connections[node_id] -= 1
```

## Disaster Recovery

### 1. Backup Management

Implementation of backup and recovery:

```python
class BackupManager:
    """Manage system backups"""
    
    def __init__(
        self,
        storage_path: str,
        s3_bucket: Optional[str] = None
    ):
        self.storage_path = Path(storage_path)
        self.s3_bucket = s3_bucket
        self.s3_client = None
        if s3_bucket:
            self.s3_client = boto3.client('s3')
            
    async def create_backup(self) -> str:
        """Create system backup"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f"backup_{timestamp}.tar.gz"
        backup_path = self.storage_path / backup_file
        
        try:
            # Create backup archive
            with tarfile.open(backup_path, "w:gz") as tar:
                # Backup configuration
                tar.add("config.toml", arcname="config.toml")
                
                # Backup data
                tar.add("data", arcname="data")
                
                # Backup state
                tar.add("state", arcname="state")
                
            # Upload to S3 if configured
            if self.s3_client:
                await self._upload_to_s3(backup_path, backup_file)
                
            return str(backup_path)
            
        except Exception as e:
            logger.error(f"Backup creation failed: {e}")
            raise
            
    async def restore_backup(self, backup_path: str):
        """Restore from backup"""
        try:
            # Download from S3 if needed
            if self.s3_bucket and backup_path.startswith('s3://'):
                backup_file = backup_path.split('/')[-1]
                local_path = self.storage_path / backup_file
                await self._download_from_s3(backup_path, local_path)
                backup_path = str(local_path)
                
            # Extract backup
            with tarfile.open(backup_path, "r:gz") as tar:
                tar.extractall(".")
                
            # Verify restoration
            if not self._verify_restoration():
                raise ValueError("Backup restoration verification failed")
                
        except Exception as e:
            logger.error(f"Backup restoration failed: {e}")
            raise
```

## Resilience Patterns

### 1. Circuit Breaker

Implementation of circuit breaker pattern:

```python
class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"         # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery

class CircuitBreaker:
    """Circuit breaker for external services"""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        half_open_timeout: int = 30
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_timeout = half_open_timeout
        self.state = CircuitState.CLOSED
        self.failures = 0
        self.last_failure_time = None
        self.last_test_time = None
        
    async def call(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Make call through circuit breaker"""
        if not await self._can_proceed():
            raise CircuitOpenError(
                "Circuit breaker is open"
            )
            
        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
            
        except Exception as e:
            await self._on_failure()
            raise
            
    async def _can_proceed(self) -> bool:
        """Check if call can proceed"""
        if self.state == CircuitState.CLOSED:
            return True
            
        if self.state == CircuitState.OPEN:
            if await self._should_attempt_recovery():
                self.state = CircuitState.HALF_OPEN
                self.last_test_time = datetime.now()
                return True
            return False
            
        # Half-open state
        if await self._should_reclose():
            self.state = CircuitState.CLOSED
            return True
            
        return False
        
    async def _on_success(self):
        """Handle successful call"""
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
            self.failures = 0
            self.last_failure_time = None
            self.last_test_time = None
            
    async def _on_failure(self):
        """Handle failed call"""
        self.failures += 1
        self.last_failure_time = datetime.now()
        
        if (self.state == CircuitState.CLOSED and
            self.failures >= self.failure_threshold):
            self.state = CircuitState.OPEN
            
        elif self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
```

### 2. Retry Management

Implementation of retry patterns:

```python
class RetryStrategy:
    """Retry strategy for operations"""
    
    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 30.0,
        exponential: bool = True
    ):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential = exponential
        
    async def execute(
        self,
        func: Callable,
        *args,
        retry_on: tuple = (Exception,),
        **kwargs
    ) -> Any:
        """Execute with retry"""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return await func(*args, **kwargs)
                
            except retry_on as e:
                last_exception = e
                
                if attempt == self.max_retries:
                    break
                    
                delay = self._get_delay(attempt)
                logger.warning(
                    f"Retry attempt {attempt + 1} after {delay}s: {e}"
                )
                await asyncio.sleep(delay)
                
        raise RetryError(
            f"Operation failed after {self.max_retries} retries"
        ) from last_exception
        
    def _get_delay(self, attempt: int) -> float:
        """Calculate retry delay"""
        if self.exponential:
            delay = self.initial_delay * (2 ** attempt)
        else:
            delay = self.initial_delay
            
        return min(delay, self.max_delay)
```

## State Management

### 1. Distributed State

Implementation of distributed state management:

```python
class StateManager:
    """Manage distributed system state"""
    
    def __init__(self, redis_url: str):
        self.redis = aioredis.from_url(redis_url)
        self.local_cache = {}
        self.cache_ttl = 300  # seconds
        
    async def get_state(
        self,
        key: str,
        default: Any = None
    ) -> Any:
        """Get state value"""
        # Check local cache
        cache_key = f"state:{key}"
        if cache_key in self.local_cache:
            value, expiry = self.local_cache[cache_key]
            if datetime.now() < expiry:
                return value
                
        # Get from Redis
        value = await self.redis.get(cache_key)
        if value is None:
            return default
            
        # Update local cache
        value = json.loads(value)
        self.local_cache[cache_key] = (
            value,
            datetime.now() + timedelta(seconds=self.cache_ttl)
        )
        
        return value
        
    async def set_state(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ):
        """Set state value"""
        cache_key = f"state:{key}"
        
        # Update Redis
        await self.redis.set(
            cache_key,
            json.dumps(value),
            ex=ttl
        )
        
        # Update local cache
        self.local_cache[cache_key] = (
            value,
            datetime.now() + timedelta(seconds=ttl or self.cache_ttl)
        )
        
    async def delete_state(self, key: str):
        """Delete state value"""
        cache_key = f"state:{key}"
        
        # Delete from Redis
        await self.redis.delete(cache_key)
        
        # Delete from local cache
        self.local_cache.pop(cache_key, None)
        
    async def clear_cache(self):
        """Clear local cache"""
        self.local_cache.clear()
```

Remember to:
- Implement proper failover mechanisms
- Monitor system health
- Test disaster recovery procedures
- Document recovery processes
- Maintain backup strategies
- Monitor system resilience
- Test high availability features