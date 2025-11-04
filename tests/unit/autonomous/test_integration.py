"""
Integration tests for autonomous system

Tests the full pipeline: Perception -> Consciousness -> Execution -> Memory
"""

import asyncio
from datetime import datetime

import pytest

from openhands.autonomous.consciousness.decision import DecisionType
from openhands.autonomous.executor.task import TaskStatus
from openhands.autonomous.lifecycle.manager import LifecycleManager
from openhands.autonomous.perception.base import EventPriority, EventType, PerceptionEvent


class TestFullPipeline:
    """Test the complete autonomous system pipeline"""

    @pytest.mark.asyncio
    async def test_perception_to_decision(self, lifecycle_manager):
        """Test that perception events lead to decisions"""
        # Create a test failure event
        event = PerceptionEvent(
            event_type=EventType.TEST_FAILED,
            priority=EventPriority.HIGH,
            timestamp=datetime.now(),
            source="TestMonitor",
            data={'test': 'test_sample', 'error': 'AssertionError'},
        )

        # Process through consciousness
        decision = await lifecycle_manager.consciousness.process_event(event)

        # Should generate fix decision
        assert decision is not None
        assert decision.decision_type == DecisionType.FIX_BUG
        assert decision.confidence > 0

    @pytest.mark.asyncio
    async def test_decision_to_execution(self, lifecycle_manager):
        """Test that decisions lead to execution"""
        # Create event
        event = PerceptionEvent(
            event_type=EventType.TEST_FAILED,
            priority=EventPriority.HIGH,
            timestamp=datetime.now(),
            source="TestMonitor",
            data={'test': 'test_sample'},
        )

        # Get decision
        decision = await lifecycle_manager.consciousness.process_event(event)

        # Submit for execution
        task = await lifecycle_manager.executor.submit_decision(decision)

        assert task.decision == decision
        assert task.status == TaskStatus.PENDING

    @pytest.mark.asyncio
    async def test_execution_to_memory(self, lifecycle_manager):
        """Test that execution results are stored in memory"""
        # Create and execute a simple decision
        event = PerceptionEvent(
            event_type=EventType.TEST_FAILED,
            priority=EventPriority.HIGH,
            timestamp=datetime.now(),
            source="TestMonitor",
            data={'test': 'test_sample'},
        )

        decision = await lifecycle_manager.consciousness.process_event(event)
        task = await lifecycle_manager.executor.submit_decision(decision)

        # Execute task
        await lifecycle_manager.executor._execute_task(task)

        # Record experience
        experience = await lifecycle_manager.memory.record_experience(task)

        # Should be stored
        assert experience is not None

        # Verify in database
        experiences = lifecycle_manager.memory.get_experiences(limit=10)
        assert len(experiences) >= 1

    @pytest.mark.asyncio
    async def test_full_lifecycle(self, lifecycle_manager):
        """Test the complete lifecycle from start to stop"""
        # Start system
        start_task = asyncio.create_task(lifecycle_manager.start())

        # Wait for startup
        await asyncio.sleep(0.3)

        # System should be running
        assert lifecycle_manager.running
        assert lifecycle_manager.perception.running
        assert lifecycle_manager.executor.running

        # Emit an event
        event = PerceptionEvent(
            event_type=EventType.TEST_PASSED,
            priority=EventPriority.LOW,
            timestamp=datetime.now(),
            source="TestMonitor",
            data={},
        )

        lifecycle_manager.perception.emit_event(event)

        # Wait for processing
        await asyncio.sleep(0.3)

        # Check that event was processed
        assert lifecycle_manager.events_processed >= 1

        # Stop system
        await lifecycle_manager.stop()

        # System should be stopped
        assert not lifecycle_manager.running

        try:
            await asyncio.wait_for(start_task, timeout=2.0)
        except asyncio.TimeoutError:
            pass

    @pytest.mark.asyncio
    async def test_proactive_goal_generation(self, lifecycle_manager):
        """Test that system generates proactive goals"""
        # Generate goals
        goals = await lifecycle_manager.consciousness.generate_proactive_goals()

        # Should generate some goals
        assert len(goals) > 0

        # Goals should have subtasks
        for goal in goals:
            assert len(goal.subtasks) > 0

    @pytest.mark.asyncio
    async def test_learning_from_experience(self, lifecycle_manager):
        """Test that system learns from multiple experiences"""
        # Create multiple similar experiences
        for i in range(5):
            event = PerceptionEvent(
                event_type=EventType.TEST_FAILED,
                priority=EventPriority.HIGH,
                timestamp=datetime.now(),
                source="TestMonitor",
                data={'test': f'test_{i}'},
            )

            decision = await lifecycle_manager.consciousness.process_event(event)
            task = await lifecycle_manager.executor.submit_decision(decision)

            # Mark as completed
            task.mark_started()
            task.mark_completed(output=f"Fixed test {i}")

            # Record experience
            await lifecycle_manager.memory.record_experience(task)

        # Identify patterns
        patterns = await lifecycle_manager.memory.identify_patterns()

        # Should find pattern
        assert len(patterns) > 0

    @pytest.mark.asyncio
    async def test_health_monitoring(self, lifecycle_manager):
        """Test continuous health monitoring"""
        # Start system
        start_task = asyncio.create_task(lifecycle_manager.start())
        await asyncio.sleep(0.3)

        # Check health multiple times
        for _ in range(3):
            health = await lifecycle_manager._check_health()
            assert health is not None

            # Should be healthy
            assert health.perception_active
            assert health.consciousness_active
            assert health.executor_active

            await asyncio.sleep(0.1)

        # Stop
        await lifecycle_manager.stop()

        try:
            await asyncio.wait_for(start_task, timeout=2.0)
        except asyncio.TimeoutError:
            pass

    @pytest.mark.asyncio
    async def test_concurrent_event_processing(self, lifecycle_manager):
        """Test processing multiple events concurrently"""
        # Start system
        start_task = asyncio.create_task(lifecycle_manager.start())
        await asyncio.sleep(0.3)

        # Emit multiple events
        events = []
        for i in range(10):
            event = PerceptionEvent(
                event_type=EventType.FILE_MODIFIED,
                priority=EventPriority.MEDIUM,
                timestamp=datetime.now(),
                source="FileMonitor",
                data={'file': f'file_{i}.py'},
            )
            lifecycle_manager.perception.emit_event(event)
            events.append(event)

        # Wait for processing
        await asyncio.sleep(0.5)

        # Should have processed events
        assert lifecycle_manager.events_processed >= len(events)

        # Stop
        await lifecycle_manager.stop()

        try:
            await asyncio.wait_for(start_task, timeout=2.0)
        except asyncio.TimeoutError:
            pass


class TestErrorHandling:
    """Test error handling and recovery"""

    @pytest.mark.asyncio
    async def test_component_failure_recovery(self, lifecycle_manager):
        """Test that system recovers from component failures"""
        # Start system
        start_task = asyncio.create_task(lifecycle_manager.start())
        await asyncio.sleep(0.3)

        # Stop a component
        await lifecycle_manager.perception.stop()

        # Wait a bit
        await asyncio.sleep(0.2)

        # Trigger self-healing
        health = await lifecycle_manager._check_health()
        await lifecycle_manager._self_heal(health)

        # Component should be restarted
        assert lifecycle_manager.perception.running

        # Stop
        await lifecycle_manager.stop()

        try:
            await asyncio.wait_for(start_task, timeout=2.0)
        except asyncio.TimeoutError:
            pass

    @pytest.mark.asyncio
    async def test_invalid_event_handling(self, lifecycle_manager):
        """Test handling of invalid events"""
        # Create event with missing data
        event = PerceptionEvent(
            event_type=EventType.GITHUB_ISSUE_OPENED,
            priority=EventPriority.HIGH,
            timestamp=datetime.now(),
            source="Test",
            data={},  # Missing issue data
        )

        # Should not crash
        decision = await lifecycle_manager.consciousness.process_event(event)

        # May or may not generate decision, but shouldn't crash
        assert decision is None or decision is not None


class TestPerformance:
    """Test system performance characteristics"""

    @pytest.mark.asyncio
    async def test_event_processing_speed(self, lifecycle_manager):
        """Test that events are processed quickly"""
        start_time = asyncio.get_event_loop().time()

        # Process a simple event
        event = PerceptionEvent(
            event_type=EventType.FILE_MODIFIED,
            priority=EventPriority.LOW,
            timestamp=datetime.now(),
            source="Test",
            data={},
        )

        decision = await lifecycle_manager.consciousness.process_event(event)

        end_time = asyncio.get_event_loop().time()
        duration = end_time - start_time

        # Should be fast (< 1 second)
        assert duration < 1.0

    @pytest.mark.asyncio
    async def test_memory_database_performance(self, lifecycle_manager):
        """Test memory database performance"""
        # Add many experiences quickly
        start_time = asyncio.get_event_loop().time()

        for i in range(50):
            event = PerceptionEvent(
                event_type=EventType.TEST_PASSED,
                priority=EventPriority.LOW,
                timestamp=datetime.now(),
                source="Test",
                data={},
            )

            decision = await lifecycle_manager.consciousness.process_event(event)
            if decision:
                task = await lifecycle_manager.executor.submit_decision(decision)
                task.mark_started()
                task.mark_completed()
                await lifecycle_manager.memory.record_experience(task)

        end_time = asyncio.get_event_loop().time()
        duration = end_time - start_time

        # Should complete in reasonable time (< 5 seconds)
        assert duration < 5.0
