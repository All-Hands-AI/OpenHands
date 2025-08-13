from unittest.mock import AsyncMock, patch

import pytest

from openhands.integrations.service_types import GitService
from openhands.server.routes.mcp import get_convo_link
from openhands.server.types import AppMode


@pytest.mark.asyncio
async def test_get_convo_link_non_saas_mode():
    """Test get_convo_link in non-SAAS mode."""
    # Mock GitService
    mock_service = AsyncMock(spec=GitService)

    # Test with non-SAAS mode
    with patch('openhands.server.routes.mcp.server_config') as mock_config:
        mock_config.app_mode = AppMode.OSS

        # Call the function
        result = await get_convo_link(
            service=mock_service, conversation_id='test-convo-id', body='Original body'
        )

        # Verify the result
        assert result == 'Original body'
        # Verify that get_user was not called
        mock_service.get_user.assert_not_called()


@pytest.mark.asyncio
async def test_get_convo_link_saas_mode():
    """Test get_convo_link in SAAS mode."""
    # Mock GitService and user
    mock_service = AsyncMock(spec=GitService)
    mock_user = AsyncMock()
    mock_user.login = 'testuser'
    mock_service.get_user.return_value = mock_user

    # Test with SAAS mode
    with (
        patch('openhands.server.routes.mcp.server_config') as mock_config,
        patch(
            'openhands.server.routes.mcp.CONVO_URL',
            'https://test.example.com/conversations/{}',
        ),
    ):
        mock_config.app_mode = AppMode.SAAS

        # Call the function
        result = await get_convo_link(
            service=mock_service, conversation_id='test-convo-id', body='Original body'
        )

        # Verify the result
        expected_link = '@testuser can click here to [continue refining the PR](https://test.example.com/conversations/test-convo-id)'
        assert result == f'Original body\n\n{expected_link}'

        # Verify that get_user was called
        mock_service.get_user.assert_called_once()


@pytest.mark.asyncio
async def test_get_convo_link_empty_body():
    """Test get_convo_link with an empty body."""
    # Mock GitService and user
    mock_service = AsyncMock(spec=GitService)
    mock_user = AsyncMock()
    mock_user.login = 'testuser'
    mock_service.get_user.return_value = mock_user

    # Test with SAAS mode and empty body
    with (
        patch('openhands.server.routes.mcp.server_config') as mock_config,
        patch(
            'openhands.server.routes.mcp.CONVO_URL',
            'https://test.example.com/conversations/{}',
        ),
    ):
        mock_config.app_mode = AppMode.SAAS

        # Call the function
        result = await get_convo_link(
            service=mock_service, conversation_id='test-convo-id', body=''
        )

        # Verify the result
        expected_link = '@testuser can click here to [continue refining the PR](https://test.example.com/conversations/test-convo-id)'
        assert result == f'\n\n{expected_link}'

        # Verify that get_user was called
        mock_service.get_user.assert_called_once()
