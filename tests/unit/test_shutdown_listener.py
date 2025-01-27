import signal
from types import FrameType
from unittest.mock import MagicMock, patch
from uuid import UUID

import pytest

from openhands.utils.shutdown_listener import (
    _register_signal_handler,
    _register_signal_handlers,
    _shutdown_listeners,
    add_shutdown_listener,
    remove_shutdown_listener,
    should_continue,
)


@pytest.fixture(autouse=True)
def cleanup_listeners():
    _shutdown_listeners.clear()
    global _should_exit
    _should_exit = False
    yield
    _shutdown_listeners.clear()
    _should_exit = False

@pytest.fixture(autouse=True)
def mock_register_handlers(monkeypatch):
    def mock_register_all():
        pass
    monkeypatch.setattr('openhands.utils.shutdown_listener._register_signal_handlers', mock_register_all)

@pytest.fixture(autouse=True)
def mock_should_continue(monkeypatch):
    def mock_continue():
        return not _should_exit
    monkeypatch.setattr('openhands.utils.shutdown_listener.should_continue', mock_continue)

@pytest.fixture(autouse=True)
def mock_signal(monkeypatch):
    def mock_signal_handler(sig, handler):
        handler(sig, None)  # Call the handler immediately
        return None
    monkeypatch.setattr('signal.signal', mock_signal_handler)


def test_add_shutdown_listener():
    mock_callable = MagicMock()
    listener_id = add_shutdown_listener(mock_callable)

    assert isinstance(listener_id, UUID)
    assert listener_id in _shutdown_listeners
    assert _shutdown_listeners[listener_id] == mock_callable


def test_remove_shutdown_listener():
    mock_callable = MagicMock()
    listener_id = add_shutdown_listener(mock_callable)

    # Test successful removal
    assert remove_shutdown_listener(listener_id) is True
    assert listener_id not in _shutdown_listeners

    # Test removing non-existent listener
    assert remove_shutdown_listener(listener_id) is False


def test_signal_handler_calls_listeners():
    mock_callable1 = MagicMock()
    mock_callable2 = MagicMock()
    add_shutdown_listener(mock_callable1)
    add_shutdown_listener(mock_callable2)

    # Register and trigger signal handler
    handler = _register_signal_handler(signal.SIGTERM)
    mock_frame = MagicMock(spec=FrameType)
    handler(signal.SIGTERM, mock_frame)

    # Verify both listeners were called
    mock_callable1.assert_called_once()
    mock_callable2.assert_called_once()

    # Verify should_continue returns False after shutdown
    assert should_continue() is False


def test_listeners_called_only_once():
    mock_callable = MagicMock()
    add_shutdown_listener(mock_callable)

    # Register and trigger signal handler multiple times
    handler = _register_signal_handler(signal.SIGTERM)
    mock_frame = MagicMock(spec=FrameType)
    handler(signal.SIGTERM, mock_frame)
    handler(signal.SIGTERM, mock_frame)

    # Verify listener was called only once
    assert mock_callable.call_count == 1


def test_remove_listener_during_shutdown():
    mock_callable1 = MagicMock()
    mock_callable2 = MagicMock()
    
    # Second listener removes the first listener when called
    listener1_id = add_shutdown_listener(mock_callable1)
    def remove_other_listener():
        remove_shutdown_listener(listener1_id)
        mock_callable2()
    
    add_shutdown_listener(remove_other_listener)

    # Register and trigger signal handler
    handler = _register_signal_handler(signal.SIGTERM)
    mock_frame = MagicMock(spec=FrameType)
    handler(signal.SIGTERM, mock_frame)

    # Both listeners should still be called
    assert mock_callable1.call_count == 1
    assert mock_callable2.call_count == 1