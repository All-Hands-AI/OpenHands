"""Worker pool management for distributed Ray runtime execution."""

import asyncio
import os
import tempfile
import time
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional, Set
import logging

import ray

from .ray_actor import RayExecutionActor

logger = logging.getLogger(__name__)


class WorkerSelectionStrategy(Enum):
    """Strategies for selecting workers from the pool."""
    ROUND_ROBIN = "round_robin"
    LEAST_BUSY = "least_busy"
    RANDOM = "random"
    SESSION_AFFINITY = "session_affinity"


class WorkerHealth(Enum):
    """Worker health states."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"
    INITIALIZING = "initializing"


class WorkerMetrics:
    """Metrics tracking for a single worker."""
    
    def __init__(self, worker_id: str):
        self.worker_id = worker_id
        self.total_requests = 0
        self.active_requests = 0
        self.failed_requests = 0
        self.average_response_time = 0.0
        self.last_activity = time.time()
        self.health = WorkerHealth.INITIALIZING
        self.sessions: Set[str] = set()
    
    def record_request_start(self):
        """Record the start of a new request."""
        self.active_requests += 1
        self.total_requests += 1
        self.last_activity = time.time()
    
    def record_request_end(self, duration: float, success: bool = True):
        """Record the completion of a request."""
        self.active_requests = max(0, self.active_requests - 1)
        if not success:
            self.failed_requests += 1
        
        # Update running average response time
        if self.total_requests > 0:
            self.average_response_time = (
                (self.average_response_time * (self.total_requests - 1) + duration) 
                / self.total_requests
            )
    
    def update_health(self):
        """Update worker health based on metrics."""
        failure_rate = self.failed_requests / max(1, self.total_requests)
        
        if failure_rate > 0.1:  # More than 10% failure rate
            self.health = WorkerHealth.FAILED
        elif failure_rate > 0.05 or self.average_response_time > 5.0:
            self.health = WorkerHealth.DEGRADED
        else:
            self.health = WorkerHealth.HEALTHY
    
    def is_available(self) -> bool:
        """Check if worker is available for new requests."""
        return self.health in [WorkerHealth.HEALTHY, WorkerHealth.DEGRADED]


class RayWorkerPool:
    """Manages a pool of Ray execution actors with load balancing and health monitoring."""
    
    def __init__(
        self,
        pool_size: int = 3,
        max_pool_size: int = 10,
        selection_strategy: WorkerSelectionStrategy = WorkerSelectionStrategy.LEAST_BUSY,
        health_check_interval: float = 30.0,
        session_timeout: float = 1800.0,  # 30 minutes
        workspace_path: str = None,
        env_vars: dict = None
    ):
        self.pool_size = pool_size
        self.max_pool_size = max_pool_size
        self.selection_strategy = selection_strategy
        self.health_check_interval = health_check_interval
        self.session_timeout = session_timeout
        self.workspace_path = workspace_path or os.path.join(tempfile.gettempdir(), "ray-workspace")
        self.env_vars = env_vars or {}
        
        self.workers: Dict[str, ray.ObjectRef] = {}  # worker_id -> actor_ref
        self.metrics: Dict[str, WorkerMetrics] = {}  # worker_id -> metrics
        self.session_affinity: Dict[str, str] = {}  # session_id -> worker_id
        self.round_robin_index = 0
        
        self._initialized = False
        self._health_check_task: Optional[asyncio.Task] = None
        
        logger.info(f"Initializing RayWorkerPool with {pool_size} workers")
    
    async def initialize(self):
        """Initialize the worker pool."""
        if self._initialized:
            return
        
        logger.info("Starting worker pool initialization")
        
        # Create initial pool of workers
        for i in range(self.pool_size):
            await self._create_worker()
        
        # Start health monitoring
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        
        self._initialized = True
        logger.info(f"Worker pool initialized with {len(self.workers)} workers")
    
    async def _create_worker(self) -> str:
        """Create a new worker and add it to the pool."""
        worker_id = str(uuid.uuid4())
        
        try:
            # Create Ray actor with workspace and environment
            actor_ref = RayExecutionActor.remote(
                workspace_path=self.workspace_path,
                env_vars=self.env_vars
            )
            
            # Wait for actor to be ready (with timeout)
            try:
                ready_future = actor_ref.ping.remote()
                # Use ray.get with timeout for simplicity
                result = ray.get(ready_future, timeout=10.0)
                logger.debug(f"Worker {worker_id} ping successful: {result}")
            except Exception as e:
                logger.warning(f"Worker {worker_id} ping failed: {e}, continuing anyway")
            
            self.workers[worker_id] = actor_ref
            self.metrics[worker_id] = WorkerMetrics(worker_id)
            self.metrics[worker_id].health = WorkerHealth.HEALTHY
            
            logger.info(f"Created worker {worker_id}")
            return worker_id
            
        except Exception as e:
            logger.error(f"Failed to create worker: {e}")
            raise
    
    async def _remove_worker(self, worker_id: str):
        """Remove a worker from the pool."""
        if worker_id in self.workers:
            try:
                # Kill the Ray actor
                ray.kill(self.workers[worker_id])
            except Exception as e:
                logger.warning(f"Error killing worker {worker_id}: {e}")
            
            # Clean up references
            del self.workers[worker_id]
            del self.metrics[worker_id]
            
            # Remove session affinity mappings
            sessions_to_remove = [
                session_id for session_id, mapped_worker_id in self.session_affinity.items()
                if mapped_worker_id == worker_id
            ]
            for session_id in sessions_to_remove:
                del self.session_affinity[session_id]
            
            logger.info(f"Removed worker {worker_id}")
    
    async def get_worker(self, session_id: Optional[str] = None) -> tuple[str, ray.ObjectRef]:
        """Get an available worker based on selection strategy."""
        if not self._initialized:
            await self.initialize()
        
        available_workers = [
            worker_id for worker_id, metrics in self.metrics.items()
            if metrics.is_available()
        ]
        
        if not available_workers:
            # Try to create a new worker if under max capacity
            if len(self.workers) < self.max_pool_size:
                worker_id = await self._create_worker()
                available_workers = [worker_id]
            else:
                raise RuntimeError("No healthy workers available and at max pool size")
        
        # Apply selection strategy
        if session_id and session_id in self.session_affinity:
            # Use session affinity if available
            worker_id = self.session_affinity[session_id]
            if worker_id in available_workers:
                return worker_id, self.workers[worker_id]
        
        # Select worker based on strategy
        if self.selection_strategy == WorkerSelectionStrategy.LEAST_BUSY:
            worker_id = min(
                available_workers,
                key=lambda w: self.metrics[w].active_requests
            )
        elif self.selection_strategy == WorkerSelectionStrategy.ROUND_ROBIN:
            worker_id = available_workers[self.round_robin_index % len(available_workers)]
            self.round_robin_index += 1
        else:  # Random or fallback
            import random
            worker_id = random.choice(available_workers)
        
        # Set session affinity if provided
        if session_id:
            self.session_affinity[session_id] = worker_id
            self.metrics[worker_id].sessions.add(session_id)
        
        return worker_id, self.workers[worker_id]
    
    async def execute_action(
        self,
        action_data: dict,
        session_id: Optional[str] = None,
        timeout: float = 60.0
    ) -> dict:
        """Execute an action using an available worker."""
        worker_id, worker_ref = await self.get_worker(session_id)
        metrics = self.metrics[worker_id]
        
        start_time = time.time()
        metrics.record_request_start()
        
        try:
            # Execute action with timeout
            future = worker_ref.execute_action.remote(action_data)
            # Use ray.get with timeout for now (could be made async in future)
            result = ray.get(future, timeout=timeout)
            
            duration = time.time() - start_time
            metrics.record_request_end(duration, success=True)
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            metrics.record_request_end(duration, success=False)
            
            logger.error(f"Action execution failed on worker {worker_id}: {e}")
            
            # Mark worker as potentially unhealthy
            metrics.update_health()
            
            # Retry on another worker if available
            if len([w for w in self.metrics.values() if w.is_available()]) > 1:
                logger.info(f"Retrying action on different worker")
                # Remove session affinity for this request to force different worker
                if session_id and session_id in self.session_affinity:
                    temp_affinity = self.session_affinity.pop(session_id)
                    try:
                        return await self.execute_action(action_data, session_id, timeout)
                    finally:
                        # Restore affinity if retry also fails
                        if session_id:
                            self.session_affinity[session_id] = temp_affinity
            
            raise
    
    async def _health_check_loop(self):
        """Background task to monitor worker health."""
        while True:
            try:
                await asyncio.sleep(self.health_check_interval)
                await self._perform_health_checks()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")
    
    async def _perform_health_checks(self):
        """Perform health checks on all workers."""
        current_time = time.time()
        workers_to_remove = []
        
        for worker_id, metrics in self.metrics.items():
            # Update health based on metrics
            metrics.update_health()
            
            # Check for inactive sessions
            expired_sessions = [
                session_id for session_id in metrics.sessions
                if current_time - metrics.last_activity > self.session_timeout
            ]
            for session_id in expired_sessions:
                metrics.sessions.discard(session_id)
                self.session_affinity.pop(session_id, None)
            
            # Mark failed workers for removal
            if metrics.health == WorkerHealth.FAILED:
                workers_to_remove.append(worker_id)
        
        # Remove failed workers and create replacements
        for worker_id in workers_to_remove:
            logger.warning(f"Removing failed worker {worker_id}")
            await self._remove_worker(worker_id)
            
            # Create replacement if under minimum pool size
            if len(self.workers) < self.pool_size:
                try:
                    await self._create_worker()
                except Exception as e:
                    logger.error(f"Failed to create replacement worker: {e}")
    
    def get_pool_stats(self) -> Dict[str, Any]:
        """Get current pool statistics."""
        healthy_workers = sum(1 for m in self.metrics.values() if m.health == WorkerHealth.HEALTHY)
        degraded_workers = sum(1 for m in self.metrics.values() if m.health == WorkerHealth.DEGRADED)
        failed_workers = sum(1 for m in self.metrics.values() if m.health == WorkerHealth.FAILED)
        
        total_requests = sum(m.total_requests for m in self.metrics.values())
        total_failures = sum(m.failed_requests for m in self.metrics.values())
        active_requests = sum(m.active_requests for m in self.metrics.values())
        
        return {
            'pool_size': len(self.workers),
            'healthy_workers': healthy_workers,
            'degraded_workers': degraded_workers,
            'failed_workers': failed_workers,
            'active_sessions': len(self.session_affinity),
            'total_requests': total_requests,
            'total_failures': total_failures,
            'active_requests': active_requests,
            'failure_rate': total_failures / max(1, total_requests),
            'average_response_time': sum(m.average_response_time for m in self.metrics.values()) / max(1, len(self.metrics))
        }
    
    async def shutdown(self):
        """Shutdown the worker pool."""
        logger.info("Shutting down worker pool")
        
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        
        # Remove all workers
        worker_ids = list(self.workers.keys())
        for worker_id in worker_ids:
            await self._remove_worker(worker_id)
        
        self._initialized = False
        logger.info("Worker pool shutdown complete")