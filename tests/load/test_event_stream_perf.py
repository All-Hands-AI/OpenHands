import os
import tempfile
import time
import uuid
from dataclasses import dataclass
from typing import List

import pytest

from openhands.events.event import Event, EventSource
from openhands.events.stream import EventStream
from openhands.storage.local import LocalFileStore


@dataclass
class TestEvent(Event):
    """Simple event class for testing."""
    action: str = "message"  # Makes it an action event
    message: str = ""
    content: str = ""  # Required for message actions


def create_test_events(count: int) -> List[TestEvent]:
    """Create a list of test events."""
    return [
        TestEvent(
            action="message",
            message=f"Test message {i}",
            content=f"Test content {i}"
        )
        for i in range(count)
    ]


class TestEventStreamPerformance:
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for the test."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def event_stream(self, temp_dir):
        """Create an event stream with a local file store."""
        file_store = LocalFileStore(temp_dir)
        stream = EventStream(sid=str(uuid.uuid4()), file_store=file_store)
        return stream

    def test_event_stream_performance(self, event_stream):
        """Test performance of event stream operations."""
        NUM_EVENTS = 150
        source = EventSource.ENVIRONMENT  # Using ENVIRONMENT as the source for testing
        events = create_test_events(NUM_EVENTS)

        # Test write performance
        write_start = time.time()
        for event in events:
            event_stream.add_event(event, source)
        write_time = time.time() - write_start
        print(f"\nWrite performance:")
        print(f"- Added {NUM_EVENTS} events in {write_time:.3f} seconds")
        print(f"- Average time per write: {write_time/NUM_EVENTS*1000:.2f} ms")

        # Test read by ID performance
        read_start = time.time()
        read_count = 50  # Number of random reads to perform
        for i in range(read_count):
            event_id = i % NUM_EVENTS  # Cycle through events
            event = event_stream.get_event(event_id)
            assert isinstance(event, Event)
            assert event.content == f"Test content {event_id}"
        read_time = time.time() - read_start
        print(f"\nRead by ID performance:")
        print(f"- Read {read_count} events by ID in {read_time:.3f} seconds")
        print(f"- Average time per read: {read_time/read_count*1000:.2f} ms")

        # Test get_events() performance (full scan)
        scan_start = time.time()
        events_list = list(event_stream.get_events())
        scan_time = time.time() - scan_start
        assert len(events_list) == NUM_EVENTS
        print(f"\nFull scan performance:")
        print(f"- Retrieved all {NUM_EVENTS} events in {scan_time:.3f} seconds")

        # Test filtered scan performance
        filter_start = time.time()
        filtered_events = list(event_stream.get_events(start_id=50, end_id=100))
        filter_time = time.time() - filter_start
        assert len(filtered_events) == 51  # 50 to 100 inclusive
        print(f"\nFiltered scan performance:")
        print(f"- Retrieved filtered events in {filter_time:.3f} seconds")
        print(f"- Number of events in range: {len(filtered_events)}")

        # Test reverse scan performance
        reverse_start = time.time()
        reverse_events = list(event_stream.get_events(reverse=True))
        reverse_time = time.time() - reverse_start
        assert len(reverse_events) == NUM_EVENTS
        print(f"\nReverse scan performance:")
        print(f"- Retrieved all events in reverse in {reverse_time:.3f} seconds")

        # Verify file size
        events_file = os.path.join(event_stream.file_store.root, 
                                 f"sessions/{event_stream.sid}/events.json")
        file_size = os.path.getsize(events_file)
        print(f"\nStorage metrics:")
        print(f"- Events file size: {file_size/1024:.2f} KB")
        print(f"- Average bytes per event: {file_size/NUM_EVENTS:.1f} bytes")

