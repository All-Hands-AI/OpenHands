"""Ray auto-scaling integration for dynamic cluster scaling based on demand."""

import asyncio
import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
import threading

import ray

logger = logging.getLogger(__name__)


class ScalingDirection(Enum):
    """Direction of scaling operation."""
    UP = "up"
    DOWN = "down"
    STABLE = "stable"


class ScalingStrategy(Enum):
    """Strategy for auto-scaling decisions."""
    DEMAND_BASED = "demand_based"
    RESOURCE_BASED = "resource_based"
    HYBRID = "hybrid"


@dataclass
class ScalingMetrics:
    """Metrics used for auto-scaling decisions."""
    queue_length: int
    average_response_time: float
    cpu_utilization: float
    memory_utilization: float
    active_workers: int
    pending_requests: int
    timestamp: float


@dataclass
class ScalingConfig:
    """Configuration for auto-scaling behavior."""
    # Worker pool limits
    min_workers: int = 2
    max_workers: int = 20
    
    # Scaling triggers
    scale_up_queue_threshold: int = 10
    scale_down_queue_threshold: int = 2
    scale_up_response_time_threshold: float = 5.0  # seconds
    
    # Resource thresholds
    cpu_scale_up_threshold: float = 0.8
    cpu_scale_down_threshold: float = 0.3
    memory_scale_up_threshold: float = 0.8
    
    # Scaling behavior
    scale_up_increment: int = 2
    scale_down_decrement: int = 1
    cooldown_period: float = 60.0  # seconds
    
    # Monitoring
    metrics_collection_interval: float = 10.0  # seconds
    strategy: ScalingStrategy = ScalingStrategy.HYBRID


@ray.remote
class RayAutoScaler:
    """Ray actor for handling auto-scaling decisions and operations."""
    
    def __init__(self, config: ScalingConfig):
        """Initialize the auto-scaler.
        
        Args:
            config: Auto-scaling configuration
        """
        self.config = config
        self.metrics_history: List[ScalingMetrics] = []
        self.last_scaling_time = 0.0
        self.scaling_decisions: List[Dict[str, Any]] = []
        
        logger.info(f"RayAutoScaler initialized with strategy: {config.strategy}")
    
    def collect_metrics(self, worker_pool_stats: Dict[str, Any]) -> ScalingMetrics:
        """Collect current metrics for scaling decisions.
        
        Args:
            worker_pool_stats: Statistics from the worker pool
            
        Returns:
            Current scaling metrics
        """
        try:
            # Extract metrics from worker pool stats
            queue_length = worker_pool_stats.get('pending_requests', 0)
            avg_response_time = worker_pool_stats.get('average_response_time', 0.0)
            active_workers = worker_pool_stats.get('active_workers', 0)
            pending_requests = worker_pool_stats.get('total_pending', 0)
            
            # Get Ray cluster resource utilization
            cluster_resources = ray.cluster_resources()
            available_cpus = cluster_resources.get('CPU', 0)
            used_cpus = ray.available_resources().get('CPU', 0)
            
            cpu_utilization = max(0.0, (available_cpus - used_cpus) / available_cpus) if available_cpus > 0 else 0.0
            
            # Simplified memory utilization (would use actual memory stats in production)
            memory_utilization = min(0.9, cpu_utilization + 0.1)  # Approximation
            
            metrics = ScalingMetrics(
                queue_length=queue_length,
                average_response_time=avg_response_time,
                cpu_utilization=cpu_utilization,
                memory_utilization=memory_utilization,
                active_workers=active_workers,
                pending_requests=pending_requests,
                timestamp=time.time()
            )
            
            # Store metrics in history (keep last 100 entries)
            self.metrics_history.append(metrics)
            if len(self.metrics_history) > 100:
                self.metrics_history.pop(0)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting scaling metrics: {e}")
            # Return default metrics on error
            return ScalingMetrics(
                queue_length=0, average_response_time=0.0, cpu_utilization=0.0,
                memory_utilization=0.0, active_workers=1, pending_requests=0,
                timestamp=time.time()
            )
    
    def should_scale(self, metrics: ScalingMetrics) -> tuple[ScalingDirection, int]:
        """Determine if scaling is needed and by how much.
        
        Args:
            metrics: Current scaling metrics
            
        Returns:
            Tuple of (scaling_direction, number_of_workers_to_change)
        """
        try:
            # Check cooldown period
            if time.time() - self.last_scaling_time < self.config.cooldown_period:
                return ScalingDirection.STABLE, 0
            
            # Apply scaling strategy
            if self.config.strategy == ScalingStrategy.DEMAND_BASED:
                return self._demand_based_scaling(metrics)
            elif self.config.strategy == ScalingStrategy.RESOURCE_BASED:
                return self._resource_based_scaling(metrics)
            else:  # HYBRID
                return self._hybrid_scaling(metrics)
                
        except Exception as e:
            logger.error(f"Error in scaling decision: {e}")
            return ScalingDirection.STABLE, 0
    
    def _demand_based_scaling(self, metrics: ScalingMetrics) -> tuple[ScalingDirection, int]:
        """Make scaling decisions based on demand metrics."""
        # Scale up conditions
        if (metrics.queue_length > self.config.scale_up_queue_threshold or
            metrics.average_response_time > self.config.scale_up_response_time_threshold):
            
            if metrics.active_workers < self.config.max_workers:
                scale_amount = min(
                    self.config.scale_up_increment,
                    self.config.max_workers - metrics.active_workers
                )
                return ScalingDirection.UP, scale_amount
        
        # Scale down conditions
        elif (metrics.queue_length < self.config.scale_down_queue_threshold and
              metrics.average_response_time < 1.0 and
              metrics.pending_requests == 0):
            
            if metrics.active_workers > self.config.min_workers:
                scale_amount = min(
                    self.config.scale_down_decrement,
                    metrics.active_workers - self.config.min_workers
                )
                return ScalingDirection.DOWN, scale_amount
        
        return ScalingDirection.STABLE, 0
    
    def _resource_based_scaling(self, metrics: ScalingMetrics) -> tuple[ScalingDirection, int]:
        """Make scaling decisions based on resource utilization."""
        # Scale up conditions
        if (metrics.cpu_utilization > self.config.cpu_scale_up_threshold or
            metrics.memory_utilization > self.config.memory_scale_up_threshold):
            
            if metrics.active_workers < self.config.max_workers:
                scale_amount = min(
                    self.config.scale_up_increment,
                    self.config.max_workers - metrics.active_workers
                )
                return ScalingDirection.UP, scale_amount
        
        # Scale down conditions
        elif (metrics.cpu_utilization < self.config.cpu_scale_down_threshold and
              metrics.memory_utilization < self.config.cpu_scale_down_threshold):
            
            if metrics.active_workers > self.config.min_workers:
                scale_amount = min(
                    self.config.scale_down_decrement,
                    metrics.active_workers - self.config.min_workers
                )
                return ScalingDirection.DOWN, scale_amount
        
        return ScalingDirection.STABLE, 0
    
    def _hybrid_scaling(self, metrics: ScalingMetrics) -> tuple[ScalingDirection, int]:
        """Make scaling decisions using hybrid approach (demand + resource)."""
        demand_direction, demand_amount = self._demand_based_scaling(metrics)
        resource_direction, resource_amount = self._resource_based_scaling(metrics)
        
        # Prioritize scale-up signals from either strategy
        if demand_direction == ScalingDirection.UP or resource_direction == ScalingDirection.UP:
            scale_amount = max(demand_amount, resource_amount)
            return ScalingDirection.UP, scale_amount
        
        # Scale down only if both strategies agree
        elif demand_direction == ScalingDirection.DOWN and resource_direction == ScalingDirection.DOWN:
            scale_amount = min(demand_amount, resource_amount)
            return ScalingDirection.DOWN, scale_amount
        
        return ScalingDirection.STABLE, 0
    
    def record_scaling_decision(self, direction: ScalingDirection, amount: int, 
                              reason: str, success: bool) -> None:
        """Record a scaling decision for monitoring and analysis.
        
        Args:
            direction: Direction of scaling
            amount: Number of workers changed
            reason: Reason for scaling decision
            success: Whether the scaling operation succeeded
        """
        decision = {
            'timestamp': time.time(),
            'direction': direction.value,
            'amount': amount,
            'reason': reason,
            'success': success
        }
        
        self.scaling_decisions.append(decision)
        
        # Keep last 50 scaling decisions
        if len(self.scaling_decisions) > 50:
            self.scaling_decisions.pop(0)
        
        if success:
            self.last_scaling_time = time.time()
        
        logger.info(f"Scaling decision recorded: {direction.value} by {amount} workers - {reason}")
    
    def get_scaling_stats(self) -> Dict[str, Any]:
        """Get auto-scaling statistics and history.
        
        Returns:
            Dictionary with scaling statistics
        """
        recent_metrics = self.metrics_history[-10:] if self.metrics_history else []
        recent_decisions = self.scaling_decisions[-10:] if self.scaling_decisions else []
        
        return {
            'config': {
                'min_workers': self.config.min_workers,
                'max_workers': self.config.max_workers,
                'strategy': self.config.strategy.value,
                'cooldown_period': self.config.cooldown_period
            },
            'current_metrics': self.metrics_history[-1].__dict__ if self.metrics_history else None,
            'recent_metrics': [m.__dict__ for m in recent_metrics],
            'recent_decisions': recent_decisions,
            'total_decisions': len(self.scaling_decisions),
            'last_scaling_time': self.last_scaling_time,
            'metrics_collected': len(self.metrics_history)
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Health check for the auto-scaler.
        
        Returns:
            Health check information
        """
        return {
            'status': 'healthy',
            'uptime': time.time(),
            'metrics_count': len(self.metrics_history),
            'decisions_count': len(self.scaling_decisions),
            'last_metrics_time': self.metrics_history[-1].timestamp if self.metrics_history else 0
        }


class AutoScalingManager:
    """Manager for Ray auto-scaling integration."""
    
    def __init__(self, config: ScalingConfig, worker_pool=None):
        """Initialize auto-scaling manager.
        
        Args:
            config: Auto-scaling configuration
            worker_pool: Worker pool to manage
        """
        self.config = config
        self.worker_pool = worker_pool
        self.auto_scaler = None
        self.monitoring_task = None
        self.scaling_callbacks: List[Callable] = []
        self._running = False
        self._lock = threading.Lock()
        
        logger.info("AutoScalingManager initialized")
    
    async def initialize(self) -> None:
        """Initialize the auto-scaling system."""
        try:
            if not ray.is_initialized():
                logger.warning("Ray not initialized, cannot start auto-scaling")
                return
            
            # Create auto-scaler actor
            self.auto_scaler = RayAutoScaler.remote(self.config)
            
            # Start monitoring loop
            self._running = True
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())
            
            logger.info("Auto-scaling system initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize auto-scaling: {e}")
            raise
    
    async def _monitoring_loop(self) -> None:
        """Main monitoring loop for auto-scaling decisions."""
        while self._running:
            try:
                # Collect current metrics from worker pool
                if self.worker_pool:
                    worker_stats = self.worker_pool.get_pool_stats()
                    
                    # Get metrics from auto-scaler
                    metrics = ray.get(self.auto_scaler.collect_metrics.remote(worker_stats))
                    
                    # Get scaling decision
                    direction, amount = ray.get(self.auto_scaler.should_scale.remote(metrics))
                    
                    # Execute scaling if needed
                    if direction != ScalingDirection.STABLE:
                        success = await self._execute_scaling(direction, amount, metrics)
                        
                        reason = self._get_scaling_reason(direction, metrics)
                        ray.get(self.auto_scaler.record_scaling_decision.remote(
                            direction, amount, reason, success
                        ))
                        
                        # Notify callbacks
                        self._notify_scaling_callbacks(direction, amount, success)
                
                # Wait for next monitoring cycle
                await asyncio.sleep(self.config.metrics_collection_interval)
                
            except Exception as e:
                logger.error(f"Error in auto-scaling monitoring loop: {e}")
                await asyncio.sleep(self.config.metrics_collection_interval)
    
    async def _execute_scaling(self, direction: ScalingDirection, amount: int,
                             metrics: ScalingMetrics) -> bool:
        """Execute the scaling operation.
        
        Args:
            direction: Direction to scale
            amount: Number of workers to add/remove
            metrics: Current metrics
            
        Returns:
            True if scaling succeeded, False otherwise
        """
        try:
            if not self.worker_pool:
                logger.warning("No worker pool available for scaling")
                return False
            
            if direction == ScalingDirection.UP:
                # Scale up by adding workers
                current_size = len(self.worker_pool.workers)
                target_size = min(current_size + amount, self.config.max_workers)
                
                for _ in range(target_size - current_size):
                    await self.worker_pool._create_worker()
                
                logger.info(f"Scaled UP: Added {target_size - current_size} workers (total: {target_size})")
                
            elif direction == ScalingDirection.DOWN:
                # Scale down by removing workers
                current_size = len(self.worker_pool.workers)
                target_size = max(current_size - amount, self.config.min_workers)
                
                workers_to_remove = current_size - target_size
                removed_workers = 0
                
                # Remove least busy workers
                for worker_id in list(self.worker_pool.workers.keys())[:workers_to_remove]:
                    await self.worker_pool._remove_worker(worker_id)
                    removed_workers += 1
                
                logger.info(f"Scaled DOWN: Removed {removed_workers} workers (total: {target_size})")
            
            return True
            
        except Exception as e:
            logger.error(f"Error executing scaling operation: {e}")
            return False
    
    def _get_scaling_reason(self, direction: ScalingDirection, metrics: ScalingMetrics) -> str:
        """Get human-readable reason for scaling decision.
        
        Args:
            direction: Scaling direction
            metrics: Current metrics
            
        Returns:
            Scaling reason string
        """
        if direction == ScalingDirection.UP:
            reasons = []
            if metrics.queue_length > self.config.scale_up_queue_threshold:
                reasons.append(f"queue_length={metrics.queue_length}")
            if metrics.average_response_time > self.config.scale_up_response_time_threshold:
                reasons.append(f"response_time={metrics.average_response_time:.2f}s")
            if metrics.cpu_utilization > self.config.cpu_scale_up_threshold:
                reasons.append(f"cpu={metrics.cpu_utilization:.2%}")
            if metrics.memory_utilization > self.config.memory_scale_up_threshold:
                reasons.append(f"memory={metrics.memory_utilization:.2%}")
            
            return f"Scale up due to: {', '.join(reasons)}"
            
        elif direction == ScalingDirection.DOWN:
            return (f"Scale down due to low utilization: "
                   f"queue={metrics.queue_length}, "
                   f"response_time={metrics.average_response_time:.2f}s, "
                   f"cpu={metrics.cpu_utilization:.2%}")
        
        return "No scaling needed"
    
    def _notify_scaling_callbacks(self, direction: ScalingDirection, amount: int, success: bool) -> None:
        """Notify registered callbacks about scaling events.
        
        Args:
            direction: Scaling direction
            amount: Number of workers changed
            success: Whether scaling succeeded
        """
        with self._lock:
            for callback in self.scaling_callbacks:
                try:
                    callback(direction, amount, success)
                except Exception as e:
                    logger.error(f"Error in scaling callback: {e}")
    
    def add_scaling_callback(self, callback: Callable[[ScalingDirection, int, bool], None]) -> None:
        """Add a callback to be notified of scaling events.
        
        Args:
            callback: Callback function taking (direction, amount, success)
        """
        with self._lock:
            self.scaling_callbacks.append(callback)
    
    def remove_scaling_callback(self, callback: Callable) -> None:
        """Remove a scaling callback.
        
        Args:
            callback: Callback function to remove
        """
        with self._lock:
            if callback in self.scaling_callbacks:
                self.scaling_callbacks.remove(callback)
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get auto-scaling statistics.
        
        Returns:
            Auto-scaling statistics
        """
        if not self.auto_scaler:
            return {'error': 'Auto-scaler not initialized'}
        
        try:
            stats = ray.get(self.auto_scaler.get_scaling_stats.remote())
            stats['monitoring_active'] = self._running
            stats['callbacks_registered'] = len(self.scaling_callbacks)
            return stats
        except Exception as e:
            logger.error(f"Error getting auto-scaling stats: {e}")
            return {'error': str(e)}
    
    async def force_scaling_check(self) -> Dict[str, Any]:
        """Force an immediate scaling check and return the decision.
        
        Returns:
            Scaling decision information
        """
        if not self.auto_scaler or not self.worker_pool:
            return {'error': 'Auto-scaler or worker pool not available'}
        
        try:
            worker_stats = self.worker_pool.get_pool_stats()
            metrics = ray.get(self.auto_scaler.collect_metrics.remote(worker_stats))
            direction, amount = ray.get(self.auto_scaler.should_scale.remote(metrics))
            
            return {
                'direction': direction.value,
                'amount': amount,
                'reason': self._get_scaling_reason(direction, metrics),
                'current_workers': len(self.worker_pool.workers),
                'metrics': metrics.__dict__
            }
            
        except Exception as e:
            logger.error(f"Error in forced scaling check: {e}")
            return {'error': str(e)}
    
    async def shutdown(self) -> None:
        """Shutdown the auto-scaling system."""
        try:
            self._running = False
            
            if self.monitoring_task:
                self.monitoring_task.cancel()
                try:
                    await self.monitoring_task
                except asyncio.CancelledError:
                    pass
            
            # Clear callbacks
            with self._lock:
                self.scaling_callbacks.clear()
            
            logger.info("Auto-scaling system shutdown")
            
        except Exception as e:
            logger.error(f"Error shutting down auto-scaling: {e}")