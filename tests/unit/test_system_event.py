from unittest.mock import Mock

from openhands.server.system_event import (
    SystemEventHandler,
    SystemEventListener,
    SystemEventType,
)


def test_event_forwarding():
    """Test that events are forwarded to all listeners."""
    handler = SystemEventHandler()
    mock_listener1 = Mock(spec=SystemEventListener)
    mock_listener2 = Mock(spec=SystemEventListener)

    handler.add_listener(mock_listener1)
    handler.add_listener(mock_listener2)

    session_id = 'test_session'
    event_type = SystemEventType.CONVERSATION_START

    handler.on_event(event_type, session_id)

    expected_data = {'session_id': session_id}
    mock_listener1.on_event.assert_called_once_with(event_type, expected_data)
    mock_listener2.on_event.assert_called_once_with(event_type, expected_data)


def test_exception_handling():
    """Test that exceptions from listeners are caught and don't affect other listeners."""
    handler = SystemEventHandler()
    mock_listener1 = Mock(spec=SystemEventListener)
    mock_listener1.on_event.side_effect = Exception('Test error')

    mock_listener2 = Mock(spec=SystemEventListener)

    handler.add_listener(mock_listener1)
    handler.add_listener(mock_listener2)

    session_id = 'test_session'
    event_type = SystemEventType.AGENT_STATUS_ERROR

    # Should not raise an exception
    handler.on_event(event_type, session_id)

    # Second listener should still be called
    expected_data = {'session_id': session_id}
    mock_listener2.on_event.assert_called_once_with(event_type, expected_data)
