"""Test to verify that event_to_memory function can be safely removed."""

from openhands.events.action import MessageAction
from openhands.events.serialization import (
    event_to_dict,
    event_to_trajectory,
)


def test_event_serialization_without_event_to_memory():
    """Test that we can serialize events without using event_to_memory."""
    # Create a simple message action
    action = MessageAction(content="Test message")
    
    # Serialize using event_to_dict
    serialized_dict = event_to_dict(action)
    assert serialized_dict["action"] == "message"
    assert serialized_dict["args"]["content"] == "Test message"
    
    # Serialize using event_to_trajectory
    serialized_trajectory = event_to_trajectory(action)
    assert serialized_trajectory["action"] == "message"
    assert serialized_trajectory["args"]["content"] == "Test message"
    
    # Verify that we can still create the necessary memory representation
    # without using event_to_memory
    memory_dict = event_to_dict(action)
    memory_dict.pop('id', None)
    memory_dict.pop('cause', None)
    memory_dict.pop('timestamp', None)
    memory_dict.pop('message', None)
    memory_dict.pop('image_urls', None)
    
    if 'args' in memory_dict:
        memory_dict['args'].pop('blocking', None)
        memory_dict['args'].pop('confirmation_state', None)
    
    # Verify the memory dict has the expected structure
    assert memory_dict["action"] == "message"
    assert memory_dict["args"]["content"] == "Test message"