from unittest.mock import AsyncMock, patch

import pytest

from openhands.integrations.service_types import GitService
from openhands.server.routes.mcp import get_conversation_link, save_pr_metadata
from openhands.server.types import AppMode
from openhands.storage.data_models.conversation_metadata import ConversationMetadata


@pytest.mark.asyncio
async def test_get_conversation_link_non_saas_mode():
    """Test get_conversation_link in non-SAAS mode."""
    # Mock GitService
    mock_service = AsyncMock(spec=GitService)

    # Test with non-SAAS mode
    with patch('openhands.server.routes.mcp.server_config') as mock_config:
        mock_config.app_mode = AppMode.OSS

        # Call the function
        result = await get_conversation_link(
            service=mock_service, conversation_id='test-convo-id', body='Original body'
        )

        # Verify the result
        assert result == 'Original body'
        # Verify that get_user was not called
        mock_service.get_user.assert_not_called()


@pytest.mark.asyncio
async def test_get_conversation_link_saas_mode():
    """Test get_conversation_link in SAAS mode."""
    # Mock GitService and user
    mock_service = AsyncMock(spec=GitService)
    mock_user = AsyncMock()
    mock_user.login = 'testuser'
    mock_service.get_user.return_value = mock_user

    # Test with SAAS mode
    with (
        patch('openhands.server.routes.mcp.server_config') as mock_config,
        patch(
            'openhands.server.routes.mcp.CONVERSATION_URL',
            'https://test.example.com/conversations/{}',
        ),
    ):
        mock_config.app_mode = AppMode.SAAS

        # Call the function
        result = await get_conversation_link(
            service=mock_service, conversation_id='test-convo-id', body='Original body'
        )

        # Verify the result
        expected_link = '@testuser can click here to [continue refining the PR](https://test.example.com/conversations/test-convo-id)'
        assert result == f'Original body\n\n{expected_link}'

        # Verify that get_user was called
        mock_service.get_user.assert_called_once()


@pytest.mark.asyncio
async def test_get_conversation_link_empty_body():
    """Test get_conversation_link with an empty body."""
    # Mock GitService and user
    mock_service = AsyncMock(spec=GitService)
    mock_user = AsyncMock()
    mock_user.login = 'testuser'
    mock_service.get_user.return_value = mock_user

    # Test with SAAS mode and empty body
    with (
        patch('openhands.server.routes.mcp.server_config') as mock_config,
        patch(
            'openhands.server.routes.mcp.CONVERSATION_URL',
            'https://test.example.com/conversations/{}',
        ),
    ):
        mock_config.app_mode = AppMode.SAAS

        # Call the function
        result = await get_conversation_link(
            service=mock_service, conversation_id='test-convo-id', body=''
        )

        # Verify the result
        expected_link = '@testuser can click here to [continue refining the PR](https://test.example.com/conversations/test-convo-id)'
        assert result == f'\n\n{expected_link}'

        # Verify that get_user was called
        mock_service.get_user.assert_called_once()


@pytest.mark.asyncio
async def test_save_pr_metadata_github_pr():
    """Test save_pr_metadata correctly updates PR number and selected branch for GitHub PR."""
    # Mock conversation store and metadata
    mock_conversation_store = AsyncMock()
    mock_conversation = ConversationMetadata(
        conversation_id='test-convo-id',
        selected_repository='test/repo',
        selected_branch='main',
        pr_number=[],
    )
    mock_conversation_store.get_metadata.return_value = mock_conversation
    mock_conversation_store.save_metadata = AsyncMock()

    # Mock the ConversationStoreImpl.get_instance
    with patch('openhands.server.routes.mcp.ConversationStoreImpl') as mock_store_impl:
        mock_store_impl.get_instance.return_value = mock_conversation_store

        # Test with GitHub PR URL containing PR number
        tool_result = 'https://github.com/test/repo/pull/123'
        source_branch = 'feature/new-feature'

        await save_pr_metadata(
            'test-user',
            'test-convo-id',
            tool_result,
            source_branch,
        )

        # Verify that the conversation metadata was updated correctly
        assert mock_conversation.pr_number == [123]
        assert mock_conversation.selected_branch == 'feature/new-feature'

        # Verify that save_metadata was called
        mock_conversation_store.save_metadata.assert_called_once_with(mock_conversation)


@pytest.mark.asyncio
async def test_save_pr_metadata_gitlab_mr():
    """Test save_pr_metadata correctly updates PR number and selected branch for GitLab MR."""
    # Mock conversation store and metadata
    mock_conversation_store = AsyncMock()
    mock_conversation = ConversationMetadata(
        conversation_id='test-convo-id',
        selected_repository='test/repo',
        selected_branch='main',
        pr_number=[],
    )
    mock_conversation_store.get_metadata.return_value = mock_conversation
    mock_conversation_store.save_metadata = AsyncMock()

    # Mock the ConversationStoreImpl.get_instance
    with patch('openhands.server.routes.mcp.ConversationStoreImpl') as mock_store_impl:
        mock_store_impl.get_instance.return_value = mock_conversation_store

        # Test with GitLab MR URL containing MR number
        tool_result = 'https://gitlab.com/test/repo/-/merge_requests/456'
        source_branch = 'feature/gitlab-feature'

        await save_pr_metadata(
            'test-user',
            'test-convo-id',
            tool_result,
            source_branch,
        )

        # Verify that the conversation metadata was updated correctly
        assert mock_conversation.pr_number == [456]
        assert mock_conversation.selected_branch == 'feature/gitlab-feature'

        # Verify that save_metadata was called
        mock_conversation_store.save_metadata.assert_called_once_with(mock_conversation)


@pytest.mark.asyncio
async def test_save_pr_metadata_no_pr_number():
    """Test save_pr_metadata still updates selected branch even when PR number is not found."""
    # Mock conversation store and metadata
    mock_conversation_store = AsyncMock()
    mock_conversation = ConversationMetadata(
        conversation_id='test-convo-id',
        selected_repository='test/repo',
        selected_branch='main',
        pr_number=[],
    )
    mock_conversation_store.get_metadata.return_value = mock_conversation
    mock_conversation_store.save_metadata = AsyncMock()

    # Mock the ConversationStoreImpl.get_instance
    with patch('openhands.server.routes.mcp.ConversationStoreImpl') as mock_store_impl:
        mock_store_impl.get_instance.return_value = mock_conversation_store

        # Test with tool result that doesn't contain a PR number
        tool_result = 'PR created successfully but no URL provided'
        source_branch = 'feature/no-url-feature'

        await save_pr_metadata(
            'test-user',
            'test-convo-id',
            tool_result,
            source_branch,
        )

        # Verify that the conversation metadata was updated correctly
        assert mock_conversation.pr_number == []  # No PR number found
        assert (
            mock_conversation.selected_branch == 'feature/no-url-feature'
        )  # Branch still updated

        # Verify that save_metadata was called
        mock_conversation_store.save_metadata.assert_called_once_with(mock_conversation)
