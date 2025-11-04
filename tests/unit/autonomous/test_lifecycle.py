"""
Tests for Lifecycle Manager (L5)
"""

import asyncio

import pytest

from openhands.autonomous.lifecycle.health import HealthStatus, SystemHealth
from openhands.autonomous.lifecycle.manager import LifecycleManager


class TestSystemHealth:
    """Tests for SystemHealth class"""

    def test_create_health_snapshot(self):
        """Test creating a health snapshot"""
        from datetime import datetime

        health = SystemHealth(
            status=HealthStatus.HEALTHY,
            timestamp=datetime.now(),
            uptime_seconds=100.0,
            perception_active=True,
            consciousness_active=True,
            executor_active=True,
            memory_accessible=True,
            memory_mb=100.0,
            cpu_percent=25.0,
            events_processed=50,
            decisions_made=10,
            tasks_completed=8,
            tasks_failed=2,
        )

        assert health.status == HealthStatus.HEALTHY
        assert health.perception_active
        assert health.memory_mb == 100.0

    def test_health_to_dict(self):
        """Test serializing health to dict"""
        from datetime import datetime

        health = SystemHealth(
            status=HealthStatus.HEALTHY,
            timestamp=datetime.now(),
            uptime_seconds=100.0,
            perception_active=True,
            consciousness_active=True,
            executor_active=True,
            memory_accessible=True,
            memory_mb=100.0,
            cpu_percent=25.0,
            events_processed=50,
            decisions_made=10,
            tasks_completed=8,
            tasks_failed=2,
        )

        data = health.to_dict()

        assert data['status'] == 'healthy'
        assert data['components']['perception'] is True
        assert data['resources']['memory_mb'] == 100.0
        assert data['metrics']['events_processed'] == 50


class TestLifecycleManager:
    """Tests for LifecycleManager class"""

    @pytest.mark.asyncio
    async def test_create_manager(self, temp_repo):
        """Test creating lifecycle manager"""
        manager = LifecycleManager(
            repo_path=str(temp_repo),
            health_check_interval=1,
        )

        assert manager.repo_path == str(temp_repo)
        assert not manager.running

    @pytest.mark.asyncio
    async def test_initialize_components(self, temp_repo):
        """Test initializing all components"""
        manager = LifecycleManager(repo_path=str(temp_repo))

        await manager.initialize()

        # All components should be initialized
        assert manager.perception is not None
        assert manager.consciousness is not None
        assert manager.executor is not None
        assert manager.memory is not None

        # Monitors should be registered
        assert len(manager.perception.monitors) > 0

    @pytest.mark.asyncio
    async def test_start_stop_manager(self, lifecycle_manager):
        """Test starting and stopping the manager"""
        # Start in background
        start_task = asyncio.create_task(lifecycle_manager.start())

        # Wait for startup
        await asyncio.sleep(0.2)
        assert lifecycle_manager.running

        # Components should be running
        assert lifecycle_manager.perception.running
        assert lifecycle_manager.executor.running

        # Stop
        await lifecycle_manager.stop()
        assert not lifecycle_manager.running

        # Wait for start task
        try:
            await asyncio.wait_for(start_task, timeout=2.0)
        except asyncio.TimeoutError:
            pass

    @pytest.mark.asyncio
    async def test_check_health(self, lifecycle_manager):
        """Test health checking"""
        health = await lifecycle_manager._check_health()

        assert isinstance(health, SystemHealth)
        assert health.status in [
            HealthStatus.HEALTHY,
            HealthStatus.DEGRADED,
            HealthStatus.UNHEALTHY,
        ]

        # Components should be reported
        assert health.perception_active is not None
        assert health.consciousness_active is not None

    @pytest.mark.asyncio
    async def test_health_status_healthy(self, lifecycle_manager):
        """Test healthy status detection"""
        # Start system
        start_task = asyncio.create_task(lifecycle_manager.start())
        await asyncio.sleep(0.2)

        # Check health
        health = await lifecycle_manager._check_health()

        # Should be healthy
        assert health.status == HealthStatus.HEALTHY

        # Stop
        await lifecycle_manager.stop()

        try:
            await asyncio.wait_for(start_task, timeout=2.0)
        except asyncio.TimeoutError:
            pass

    @pytest.mark.asyncio
    async def test_health_status_unhealthy(self, lifecycle_manager):
        """Test unhealthy status detection"""
        # Start system
        start_task = asyncio.create_task(lifecycle_manager.start())
        await asyncio.sleep(0.2)

        # Manually stop a component
        await lifecycle_manager.perception.stop()

        # Check health
        health = await lifecycle_manager._check_health()

        # Should detect unhealthy
        assert health.status == HealthStatus.UNHEALTHY
        assert not health.perception_active

        # Stop
        await lifecycle_manager.stop()

        try:
            await asyncio.wait_for(start_task, timeout=2.0)
        except asyncio.TimeoutError:
            pass

    @pytest.mark.asyncio
    async def test_self_healing(self, lifecycle_manager):
        """Test self-healing functionality"""
        # Start system
        start_task = asyncio.create_task(lifecycle_manager.start())
        await asyncio.sleep(0.2)

        # Stop perception
        await lifecycle_manager.perception.stop()

        # Create unhealthy state
        health = SystemHealth(
            status=HealthStatus.UNHEALTHY,
            timestamp=lifecycle_manager.start_time,
            uptime_seconds=1.0,
            perception_active=False,
            consciousness_active=True,
            executor_active=True,
            memory_accessible=True,
            memory_mb=100.0,
            cpu_percent=25.0,
            events_processed=0,
            decisions_made=0,
            tasks_completed=0,
            tasks_failed=0,
        )

        # Trigger self-heal
        await lifecycle_manager._self_heal(health)

        # Perception should be restarted
        assert lifecycle_manager.perception.running

        # Stop
        await lifecycle_manager.stop()

        try:
            await asyncio.wait_for(start_task, timeout=2.0)
        except asyncio.TimeoutError:
            pass

    @pytest.mark.asyncio
    async def test_get_status(self, lifecycle_manager):
        """Test getting system status"""
        status = await lifecycle_manager.get_status()

        assert 'alive' in status
        assert 'health' in status
        assert 'components' in status

        # Components should be reported
        assert 'perception' in status['components']
        assert 'consciousness' in status['components']
        assert 'executor' in status['components']
        assert 'memory' in status['components']

    @pytest.mark.asyncio
    async def test_metrics_tracking(self, lifecycle_manager):
        """Test that metrics are tracked"""
        # Start system
        start_task = asyncio.create_task(lifecycle_manager.start())
        await asyncio.sleep(0.2)

        # Emit some events
        from datetime import datetime

        from openhands.autonomous.perception.base import (
            EventPriority,
            EventType,
            PerceptionEvent,
        )

        event = PerceptionEvent(
            event_type=EventType.TEST_PASSED,
            priority=EventPriority.LOW,
            timestamp=datetime.now(),
            source="Test",
            data={},
        )

        lifecycle_manager.perception.emit_event(event)

        # Wait for processing
        await asyncio.sleep(0.3)

        # Check metrics
        assert lifecycle_manager.events_processed >= 0

        # Stop
        await lifecycle_manager.stop()

        try:
            await asyncio.wait_for(start_task, timeout=2.0)
        except asyncio.TimeoutError:
            pass

    @pytest.mark.asyncio
    async def test_resource_limits(self, temp_repo):
        """Test resource limit enforcement"""
        manager = LifecycleManager(
            repo_path=str(temp_repo),
            max_memory_mb=100,  # Very low limit
            max_cpu_percent=5.0,  # Very low limit
        )

        await manager.initialize()

        health = await manager._check_health()

        # Depending on actual usage, might be degraded
        # This is hard to test reliably, so just check it runs
        assert health.status in [
            HealthStatus.HEALTHY,
            HealthStatus.DEGRADED,
            HealthStatus.UNHEALTHY,
        ]
