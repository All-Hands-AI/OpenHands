"""
Lifecycle Manager - Keeps the system alive
"""

import asyncio
import logging
import os
import psutil
from datetime import datetime
from typing import Optional

from openhands.autonomous.consciousness.core import ConsciousnessCore
from openhands.autonomous.executor.executor import AutonomousExecutor
from openhands.autonomous.lifecycle.health import HealthStatus, SystemHealth
from openhands.autonomous.memory.memory import MemorySystem
from openhands.autonomous.perception.base import PerceptionLayer

logger = logging.getLogger(__name__)


class LifecycleManager:
    """
    L5: Lifecycle Manager

    Manages the entire lifecycle of the autonomous system.
    """

    def __init__(
        self,
        repo_path: str,
        health_check_interval: int = 300,
        max_memory_mb: int = 2048,
        max_cpu_percent: float = 80.0,
    ):
        """
        Args:
            repo_path: Path to repository
            health_check_interval: Health check interval (seconds)
            max_memory_mb: Max memory usage (MB)
            max_cpu_percent: Max CPU usage (%)
        """
        self.repo_path = repo_path
        self.health_check_interval = health_check_interval
        self.max_memory_mb = max_memory_mb
        self.max_cpu_percent = max_cpu_percent

        # Timestamp
        self.start_time = datetime.now()

        # Components (will be initialized)
        self.perception: Optional[PerceptionLayer] = None
        self.consciousness: Optional[ConsciousnessCore] = None
        self.executor: Optional[AutonomousExecutor] = None
        self.memory: Optional[MemorySystem] = None

        # State
        self.running = False
        self.health_status = HealthStatus.HEALTHY

        # Metrics
        self.events_processed = 0
        self.decisions_made = 0

    async def initialize(self):
        """Initialize all components"""
        logger.info("Initializing autonomous system...")

        # L4: Memory (initialize first, as others may need it)
        self.memory = MemorySystem()

        # L1: Perception
        from openhands.autonomous.perception.git_monitor import GitMonitor
        from openhands.autonomous.perception.health_monitor import HealthMonitor

        self.perception = PerceptionLayer()

        # Register monitors
        git_monitor = GitMonitor(repo_path=self.repo_path)
        health_monitor = HealthMonitor(repo_path=self.repo_path)

        self.perception.register_monitor(git_monitor)
        self.perception.register_monitor(health_monitor)

        # L2: Consciousness
        self.consciousness = ConsciousnessCore(
            autonomy_level='medium',
            auto_approve=False,
        )

        # L3: Executor
        self.executor = AutonomousExecutor(
            max_concurrent_tasks=3,
            auto_commit=True,
            auto_pr=False,
        )

        logger.info("All components initialized")

    async def start(self):
        """Start the autonomous system"""
        if self.running:
            logger.warning("System already running")
            return

        self.running = True
        logger.info("🌱 Starting autonomous digital life system...")

        # Start components
        await self.perception.start()
        await self.executor.start()

        # Start main loop
        asyncio.create_task(self._main_loop())

        # Start health monitor
        asyncio.create_task(self._health_monitor_loop())

        logger.info("✨ System is ALIVE and running autonomously!")

    async def stop(self):
        """Stop the autonomous system"""
        self.running = False
        logger.info("Stopping autonomous system...")

        # Stop components
        if self.perception:
            await self.perception.stop()

        if self.executor:
            await self.executor.stop()

        logger.info("System stopped")

    async def _main_loop(self):
        """
        Main system loop

        This is the heartbeat of the digital life.
        """
        logger.info("Main loop started")

        while self.running:
            try:
                # Get perception events
                events = await self.perception.get_events_batch(max_events=10, timeout=5.0)

                if not events:
                    # No events, generate proactive goals
                    if self.consciousness:
                        goals = await self.consciousness.generate_proactive_goals()
                        if goals:
                            logger.info(f"Generated {len(goals)} proactive goals")
                    continue

                # Process each event
                for event in events:
                    self.events_processed += 1

                    # Consciousness decides what to do
                    decision = await self.consciousness.process_event(event)

                    if decision:
                        self.decisions_made += 1

                        # Check if should execute
                        should_execute = self.consciousness.should_approve_decision(decision)

                        if should_execute:
                            # Submit for execution
                            task = await self.executor.submit_decision(decision)
                            logger.info(f"Submitted task {task.id} for execution")

                            # TODO: After task completes, record experience
                            # For now, we'd need to poll or use callbacks

                        else:
                            logger.info(f"Decision requires human approval: {decision.decision_type.value}")
                            # TODO: Notify human for approval

            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)
                await asyncio.sleep(5)

    async def _health_monitor_loop(self):
        """Monitor system health"""
        while self.running:
            try:
                health = await self._check_health()

                # Log health status
                if health.status != self.health_status:
                    logger.info(f"Health status changed: {self.health_status.value} -> {health.status.value}")
                    self.health_status = health.status

                # Take action if unhealthy
                if health.status in (HealthStatus.UNHEALTHY, HealthStatus.CRITICAL):
                    await self._self_heal(health)

            except Exception as e:
                logger.error(f"Error in health monitor: {e}", exc_info=True)

            await asyncio.sleep(self.health_check_interval)

    async def _check_health(self) -> SystemHealth:
        """Check system health"""
        # Get resource usage
        process = psutil.Process(os.getpid())
        memory_mb = process.memory_info().rss / 1024 / 1024
        cpu_percent = process.cpu_percent(interval=1.0)

        # Check component health
        perception_active = self.perception.running if self.perception else False
        consciousness_active = self.consciousness is not None
        executor_active = self.executor.running if self.executor else False
        memory_accessible = self.memory is not None

        # Get executor stats
        executor_stats = self.executor.get_statistics() if self.executor else {}
        tasks_completed = executor_stats.get('completed', 0)
        tasks_failed = executor_stats.get('failed', 0)

        # Determine overall status
        status = HealthStatus.HEALTHY

        # Check resource limits
        if memory_mb > self.max_memory_mb:
            status = HealthStatus.DEGRADED
            logger.warning(f"Memory usage high: {memory_mb:.1f} MB")

        if cpu_percent > self.max_cpu_percent:
            status = HealthStatus.DEGRADED
            logger.warning(f"CPU usage high: {cpu_percent:.1f}%")

        # Check components
        if not all([perception_active, consciousness_active, executor_active, memory_accessible]):
            status = HealthStatus.UNHEALTHY
            logger.error("Some components are not active")

        # Create health snapshot
        health = SystemHealth(
            status=status,
            timestamp=datetime.now(),
            uptime_seconds=(datetime.now() - self.start_time).total_seconds(),
            perception_active=perception_active,
            consciousness_active=consciousness_active,
            executor_active=executor_active,
            memory_accessible=memory_accessible,
            memory_mb=memory_mb,
            cpu_percent=cpu_percent,
            events_processed=self.events_processed,
            decisions_made=self.decisions_made,
            tasks_completed=tasks_completed,
            tasks_failed=tasks_failed,
        )

        return health

    async def _self_heal(self, health: SystemHealth):
        """
        Attempt to self-heal from unhealthy state

        This is where the system becomes truly autonomous - fixing itself.
        """
        logger.warning("Attempting self-healing...")

        # Restart dead components
        if not health.perception_active and self.perception:
            logger.info("Restarting perception layer...")
            await self.perception.start()

        if not health.executor_active and self.executor:
            logger.info("Restarting executor...")
            await self.executor.start()

        # Memory issues
        if health.memory_mb > self.max_memory_mb:
            logger.info("High memory usage, triggering garbage collection...")
            import gc
            gc.collect()

        logger.info("Self-healing complete")

    async def get_status(self) -> dict:
        """Get system status"""
        health = await self._check_health()

        return {
            'alive': self.running,
            'health': health.to_dict(),
            'components': {
                'perception': {
                    'active': health.perception_active,
                    'monitors': len(self.perception.monitors) if self.perception else 0,
                },
                'consciousness': {
                    'active': health.consciousness_active,
                    'active_goals': len(self.consciousness.get_active_goals()) if self.consciousness else 0,
                },
                'executor': {
                    'active': health.executor_active,
                    'stats': self.executor.get_statistics() if self.executor else {},
                },
                'memory': {
                    'accessible': health.memory_accessible,
                    'stats': self.memory.get_statistics() if self.memory else {},
                },
            },
        }
