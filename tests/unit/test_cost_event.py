import pytest
from openhands.events.cost import CostEvent
from openhands.events.event import EventSource
from openhands.events.stream import EventStream
from openhands.storage.files import FileStore


class MockFileStore(FileStore):
    def __init__(self):
        self.files = {}

    def write(self, path: str, contents: str) -> None:
        self.files[path] = contents

    def read(self, path: str) -> str:
        if path not in self.files:
            raise FileNotFoundError(path)
        return self.files[path]

    def list(self, path: str) -> list[str]:
        return [k for k in self.files.keys() if k.startswith(path)]

    def delete(self, path: str) -> None:
        self.files = {k: v for k, v in self.files.items() if not k.startswith(path)}


@pytest.fixture
def event_stream():
    file_store = MockFileStore()
    return EventStream("test", file_store)


def test_cost_event(event_stream):
    # Create a cost event
    cost_event = CostEvent(step_cost=0.1, total_cost=0.5, description="Test step")
    
    # Add the event to the stream
    event_stream.add_event(cost_event, EventSource.ENVIRONMENT)
    
    # Get the latest event
    latest_event = event_stream.get_latest_event()
    
    # Verify the event was added correctly
    assert isinstance(latest_event, CostEvent)
    assert latest_event.step_cost == 0.1
    assert latest_event.total_cost == 0.5
    assert latest_event.description == "Test step"
