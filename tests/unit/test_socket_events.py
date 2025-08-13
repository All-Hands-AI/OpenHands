from unittest.mock import AsyncMock, patch

import pytest

from openhands.server.listen_socket import oh_action, oh_user_action


@pytest.mark.asyncio
async def test_oh_user_action():
    """Test that oh_user_action correctly forwards data to the conversation manager."""
    connection_id = 'test_connection_id'
    test_data = {'action': 'test_action', 'data': 'test_data'}

    # Mock the conversation_manager
    with patch('openhands.server.listen_socket.conversation_manager') as mock_manager:
        mock_manager.send_to_event_stream = AsyncMock()

        # Call the function
        await oh_user_action(connection_id, test_data)

        # Verify the conversation manager was called with the correct arguments
        mock_manager.send_to_event_stream.assert_called_once_with(
            connection_id, test_data
        )


@pytest.mark.asyncio
async def test_oh_action():
    """Test that oh_action (legacy handler) correctly forwards data to the conversation manager."""
    connection_id = 'test_connection_id'
    test_data = {'action': 'test_action', 'data': 'test_data'}

    # Mock the conversation_manager
    with patch('openhands.server.listen_socket.conversation_manager') as mock_manager:
        mock_manager.send_to_event_stream = AsyncMock()

        # Call the function
        await oh_action(connection_id, test_data)

        # Verify the conversation manager was called with the correct arguments
        mock_manager.send_to_event_stream.assert_called_once_with(
            connection_id, test_data
        )
