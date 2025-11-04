"""
Tests for perception layer base components
"""

import asyncio
from datetime import datetime

import pytest

from openhands.autonomous.perception.base import (
    BaseMonitor,
    EventPriority,
    EventType,
    PerceptionEvent,
    PerceptionLayer,
)


class TestPerceptionEvent:
    """Tests for PerceptionEvent class"""

    def test_create_event(self):
        """Test creating a perception event"""
        event = PerceptionEvent(
            event_type=EventType.TEST_FAILED,
            priority=EventPriority.HIGH,
            timestamp=datetime.now(),
            source="TestMonitor",
            data={'test': 'value'},
        )

        assert event.event_type == EventType.TEST_FAILED
        assert event.priority == EventPriority.HIGH
        assert event.source == "TestMonitor"
        assert event.data == {'test': 'value'}
        assert not event.processed
        assert event.actions_taken == []
        assert event.id.startswith('evt_')

    def test_event_to_dict(self, sample_perception_event):
        """Test serializing event to dict"""
        data = sample_perception_event.to_dict()

        assert data['event_type'] == 'test_failed'
        assert data['priority'] == EventPriority.HIGH.value
        assert data['source'] == 'TestMonitor'
        assert 'timestamp' in data
        assert 'id' in data

    def test_event_from_dict(self, sample_perception_event):
        """Test deserializing event from dict"""
        data = sample_perception_event.to_dict()
        event = PerceptionEvent.from_dict(data)

        assert event.event_type == sample_perception_event.event_type
        assert event.priority == sample_perception_event.priority
        assert event.source == sample_perception_event.source


class TestBaseMonitor:
    """Tests for BaseMonitor class"""

    class DummyMonitor(BaseMonitor):
        """Dummy monitor for testing"""

        def __init__(self):
            super().__init__(name="DummyMonitor", check_interval=0.1)
            self.check_count = 0

        async def check(self):
            self.check_count += 1
            return [
                PerceptionEvent(
                    event_type=EventType.TEST_PASSED,
                    priority=EventPriority.LOW,
                    timestamp=datetime.now(),
                    source=self.name,
                    data={'count': self.check_count},
                )
            ]

    @pytest.mark.asyncio
    async def test_monitor_start_stop(self):
        """Test starting and stopping a monitor"""
        monitor = self.DummyMonitor()

        assert not monitor.running

        # Start monitor
        await monitor.start()
        assert monitor.running

        # Wait for a few checks
        await asyncio.sleep(0.3)
        assert monitor.check_count >= 2

        # Stop monitor
        await monitor.stop()
        assert not monitor.running

        # Count should not increase after stop
        count_before = monitor.check_count
        await asyncio.sleep(0.3)
        assert monitor.check_count == count_before

    @pytest.mark.asyncio
    async def test_monitor_double_start(self):
        """Test that starting a running monitor is safe"""
        monitor = self.DummyMonitor()

        await monitor.start()
        await monitor.start()  # Should not raise

        await monitor.stop()


class TestPerceptionLayer:
    """Tests for PerceptionLayer class"""

    @pytest.mark.asyncio
    async def test_create_layer(self, perception_layer):
        """Test creating perception layer"""
        assert perception_layer.monitors == []
        assert not perception_layer.running

    @pytest.mark.asyncio
    async def test_register_monitor(self, perception_layer):
        """Test registering a monitor"""

        class DummyMonitor(BaseMonitor):
            async def check(self):
                return []

        monitor = DummyMonitor(name="Test", check_interval=1)
        perception_layer.register_monitor(monitor)

        assert len(perception_layer.monitors) == 1
        assert perception_layer.monitors[0] == monitor

    @pytest.mark.asyncio
    async def test_start_stop_layer(self, perception_layer):
        """Test starting and stopping perception layer"""

        class DummyMonitor(BaseMonitor):
            async def check(self):
                return []

        monitor = DummyMonitor(name="Test", check_interval=1)
        perception_layer.register_monitor(monitor)

        # Start
        await perception_layer.start()
        assert perception_layer.running
        assert monitor.running

        # Stop
        await perception_layer.stop()
        assert not perception_layer.running
        assert not monitor.running

    @pytest.mark.asyncio
    async def test_emit_and_get_event(self, perception_layer, sample_perception_event):
        """Test emitting and receiving events"""
        # Emit event
        perception_layer.emit_event(sample_perception_event)

        # Get event
        event = await perception_layer.get_next_event(timeout=1.0)
        assert event == sample_perception_event

    @pytest.mark.asyncio
    async def test_get_event_timeout(self, perception_layer):
        """Test getting event with timeout"""
        event = await perception_layer.get_next_event(timeout=0.1)
        assert event is None

    @pytest.mark.asyncio
    async def test_get_events_batch(self, perception_layer):
        """Test getting a batch of events"""
        # Emit multiple events
        events = [
            PerceptionEvent(
                event_type=EventType.TEST_PASSED,
                priority=EventPriority.LOW,
                timestamp=datetime.now(),
                source="Test",
                data={'i': i},
            )
            for i in range(5)
        ]

        for event in events:
            perception_layer.emit_event(event)

        # Get batch
        batch = await perception_layer.get_events_batch(max_events=3, timeout=0.1)
        assert len(batch) == 3

        # Get remaining
        batch2 = await perception_layer.get_events_batch(max_events=10, timeout=0.1)
        assert len(batch2) == 2

    @pytest.mark.asyncio
    async def test_get_empty_batch(self, perception_layer):
        """Test getting empty batch"""
        batch = await perception_layer.get_events_batch(max_events=10, timeout=0.1)
        assert batch == []
