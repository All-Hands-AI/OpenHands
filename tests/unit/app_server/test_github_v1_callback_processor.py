"""
Tests for the GithubV1CallbackProcessor.

This module tests the GitHub V1 callback processor, focusing on event handling,
agent communication, and GitHub API integration.
"""

import os
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import httpx
import pytest

from openhands.app_server.app_conversation.app_conversation_models import (
    AppConversationInfo,
)
from openhands.app_server.event_callback.event_callback_models import EventCallback
from openhands.app_server.event_callback.event_callback_result_models import (
    EventCallbackResultStatus,
)
from openhands.app_server.event_callback.github_v1_callback_processor import (
    GithubV1CallbackProcessor,
)
from openhands.app_server.sandbox.sandbox_models import (
    ExposedUrl,
    SandboxInfo,
    SandboxStatus,
)
from openhands.events.action.message import MessageAction
from openhands.sdk.event import ConversationStateUpdateEvent


@pytest.fixture
def github_callback_processor():
    """Create a GithubV1CallbackProcessor instance for testing."""
    return GithubV1CallbackProcessor(
        github_view_data={
            'installation_id': 12345,
            'full_repo_name': 'test-owner/test-repo',
            'issue_number': 42,
        },
        should_request_summary=True,
        should_extract=True,
        inline_pr_comment=False,
    )


@pytest.fixture
def github_callback_processor_inline():
    """Create a GithubV1CallbackProcessor instance for inline PR comments."""
    return GithubV1CallbackProcessor(
        github_view_data={
            'installation_id': 12345,
            'full_repo_name': 'test-owner/test-repo',
            'issue_number': 42,
            'comment_id': 'comment_123',
        },
        should_request_summary=True,
        should_extract=True,
        inline_pr_comment=True,
    )


@pytest.fixture
def conversation_state_update_event():
    """Create a ConversationStateUpdateEvent for testing."""
    return ConversationStateUpdateEvent(
        key='execution_status',
        value='finished',
    )


@pytest.fixture
def wrong_event():
    """Create a different event type for testing."""
    return MessageAction(
        content='Hello world',
    )


@pytest.fixture
def wrong_state_event():
    """Create a ConversationStateUpdateEvent with wrong key/value."""
    return ConversationStateUpdateEvent(
        key='execution_status',
        value='running',
    )


@pytest.fixture
def event_callback():
    """Create an EventCallback for testing."""
    return EventCallback(
        id=uuid4(),
        conversation_id=uuid4(),
        processor=GithubV1CallbackProcessor(),
        event_kind='ConversationStateUpdateEvent',
    )


@pytest.fixture
def mock_app_conversation_info():
    """Create a mock AppConversationInfo."""
    return AppConversationInfo(
        conversation_id=uuid4(),
        sandbox_id='sandbox_123',
        title='Test Conversation',
        created_by_user_id='test_user_123',
    )


@pytest.fixture
def mock_sandbox_info():
    """Create a mock SandboxInfo."""
    return SandboxInfo(
        id='sandbox_123',
        status=SandboxStatus.RUNNING,
        session_api_key='test_api_key',
        created_by_user_id='test_user_123',
        sandbox_spec_id='spec_123',
        exposed_urls=[
            ExposedUrl(name='AGENT_SERVER', url='http://localhost:8000', port=8000),
        ],
    )


# Removed mock_services fixture to avoid conflicts with individual test patches


class TestGithubV1CallbackProcessor:
    """Test the GithubV1CallbackProcessor class."""

    async def test_call_with_wrong_event_type(
        self,
        github_callback_processor,
        wrong_event,
        event_callback,
    ):
        """Test that non-ConversationStateUpdateEvent events are ignored."""
        conversation_id = uuid4()

        result = await github_callback_processor(
            conversation_id=conversation_id,
            callback=event_callback,
            event=wrong_event,
        )

        assert result is None

    async def test_call_with_wrong_state_event(
        self,
        github_callback_processor,
        wrong_state_event,
        event_callback,
    ):
        """Test that ConversationStateUpdateEvent with wrong key/value is ignored."""
        conversation_id = uuid4()

        result = await github_callback_processor(
            conversation_id=conversation_id,
            callback=event_callback,
            event=wrong_state_event,
        )

        assert result is None

    async def test_call_should_request_summary_false(
        self,
        github_callback_processor,
        conversation_state_update_event,
        event_callback,
    ):
        """Test that callback returns None when should_request_summary is False."""
        github_callback_processor.should_request_summary = False
        conversation_id = uuid4()

        result = await github_callback_processor(
            conversation_id=conversation_id,
            callback=event_callback,
            event=conversation_state_update_event,
        )

        assert result is None

    @patch.dict(
        os.environ,
        {
            'GITHUB_APP_CLIENT_ID': 'test_client_id',
            'GITHUB_APP_PRIVATE_KEY': 'test_private_key',
        },
    )
    @patch('openhands.app_server.config.get_app_conversation_info_service')
    @patch('openhands.app_server.config.get_sandbox_service')
    @patch('openhands.app_server.config.get_httpx_client')
    @patch(
        'openhands.app_server.event_callback.github_v1_callback_processor.get_prompt_template'
    )
    @patch(
        'openhands.app_server.event_callback.github_v1_callback_processor.GithubIntegration'
    )
    @patch('openhands.app_server.event_callback.github_v1_callback_processor.Github')
    async def test_successful_callback_execution(
        self,
        mock_github,
        mock_github_integration,
        mock_get_prompt_template,
        mock_get_httpx_client,
        mock_get_sandbox_service,
        mock_get_app_conversation_info_service,
        github_callback_processor,
        conversation_state_update_event,
        event_callback,
        mock_app_conversation_info,
        mock_sandbox_info,
    ):
        """Test successful callback execution with all mocked dependencies."""
        conversation_id = uuid4()

        # Mock services
        mock_app_conversation_info_service = AsyncMock()
        mock_app_conversation_info_service.get_app_conversation_info.return_value = (
            mock_app_conversation_info
        )
        mock_get_app_conversation_info_service.return_value.__aenter__.return_value = (
            mock_app_conversation_info_service
        )

        mock_sandbox_service = AsyncMock()
        mock_sandbox_service.get_sandbox.return_value = mock_sandbox_info
        mock_get_sandbox_service.return_value.__aenter__.return_value = (
            mock_sandbox_service
        )

        mock_httpx_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {'response': 'Test summary from agent'}
        mock_response.raise_for_status.return_value = None
        mock_httpx_client.post.return_value = mock_response
        mock_get_httpx_client.return_value.__aenter__.return_value = mock_httpx_client

        # Mock prompt template
        mock_get_prompt_template.return_value = 'Please provide a summary'

        # Mock GitHub integration
        mock_token_data = MagicMock()
        mock_token_data.token = 'test_access_token'
        mock_integration_instance = MagicMock()
        mock_integration_instance.get_access_token.return_value = mock_token_data
        mock_github_integration.return_value = mock_integration_instance

        # Mock GitHub client
        mock_github_client = MagicMock()
        mock_repo = MagicMock()
        mock_issue = MagicMock()
        mock_repo.get_issue.return_value = mock_issue
        mock_github_client.get_repo.return_value = mock_repo
        mock_github.return_value.__enter__.return_value = mock_github_client

        # Execute the callback
        result = await github_callback_processor(
            conversation_id=conversation_id,
            callback=event_callback,
            event=conversation_state_update_event,
        )

        # Verify the result
        assert result is not None
        assert result.status == EventCallbackResultStatus.SUCCESS
        assert result.event_callback_id == event_callback.id
        assert result.event_id == conversation_state_update_event.id
        assert result.conversation_id == conversation_id
        assert result.detail == 'Test summary from agent'

        # Verify should_request_summary was set to False
        assert github_callback_processor.should_request_summary is False

        # Verify GitHub integration was called correctly
        mock_github_integration.assert_called_once_with(
            'test_client_id', 'test_private_key'
        )
        mock_integration_instance.get_access_token.assert_called_once_with(12345)

        # Verify GitHub API calls
        mock_github.assert_called_once_with('test_access_token')
        mock_github_client.get_repo.assert_called_once_with('test-owner/test-repo')
        mock_repo.get_issue.assert_called_once_with(number=42)
        mock_issue.create_comment.assert_called_once_with('Test summary from agent')

        # Verify agent server communication
        mock_httpx_client.post.assert_called_once()
        call_args = mock_httpx_client.post.call_args
        # Check if URL is in positional args (first argument) or keyword args
        if len(call_args[0]) > 0:
            assert 'ask_agent' in call_args[0][0]  # URL is first positional argument
        else:
            assert 'ask_agent' in call_args[1]['url']  # URL is keyword argument
        assert call_args[1]['headers']['X-Session-API-Key'] == 'test_api_key'
        assert call_args[1]['json']['question'] == 'Please provide a summary'

    @patch.dict(
        os.environ,
        {
            'GITHUB_APP_CLIENT_ID': 'test_client_id',
            'GITHUB_APP_PRIVATE_KEY': 'test_private_key',
        },
    )
    @patch('openhands.app_server.config.get_app_conversation_info_service')
    @patch('openhands.app_server.config.get_sandbox_service')
    @patch('openhands.app_server.config.get_httpx_client')
    @patch(
        'openhands.app_server.event_callback.github_v1_callback_processor.get_prompt_template'
    )
    @patch(
        'openhands.app_server.event_callback.github_v1_callback_processor.GithubIntegration'
    )
    @patch('openhands.app_server.event_callback.github_v1_callback_processor.Github')
    async def test_successful_inline_pr_comment(
        self,
        mock_github,
        mock_github_integration,
        mock_get_prompt_template,
        mock_get_httpx_client,
        mock_get_sandbox_service,
        mock_get_app_conversation_info_service,
        github_callback_processor_inline,
        conversation_state_update_event,
        event_callback,
        mock_app_conversation_info,
        mock_sandbox_info,
    ):
        """Test successful callback execution with inline PR comment."""
        conversation_id = uuid4()

        # Mock services (same as above)
        mock_app_conversation_info_service = AsyncMock()
        mock_app_conversation_info_service.get_app_conversation_info.return_value = (
            mock_app_conversation_info
        )
        mock_get_app_conversation_info_service.return_value.__aenter__.return_value = (
            mock_app_conversation_info_service
        )

        mock_sandbox_service = AsyncMock()
        mock_sandbox_service.get_sandbox.return_value = mock_sandbox_info
        mock_get_sandbox_service.return_value.__aenter__.return_value = (
            mock_sandbox_service
        )

        mock_httpx_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {'response': 'Test summary from agent'}
        mock_response.raise_for_status.return_value = None
        mock_httpx_client.post.return_value = mock_response
        mock_get_httpx_client.return_value.__aenter__.return_value = mock_httpx_client

        mock_get_prompt_template.return_value = 'Please provide a summary'

        # Mock GitHub integration
        mock_token_data = MagicMock()
        mock_token_data.token = 'test_access_token'
        mock_integration_instance = MagicMock()
        mock_integration_instance.get_access_token.return_value = mock_token_data
        mock_github_integration.return_value = mock_integration_instance

        # Mock GitHub client for PR comment
        mock_github_client = MagicMock()
        mock_repo = MagicMock()
        mock_pr = MagicMock()
        mock_repo.get_pull.return_value = mock_pr
        mock_github_client.get_repo.return_value = mock_repo
        mock_github.return_value.__enter__.return_value = mock_github_client

        # Execute the callback
        result = await github_callback_processor_inline(
            conversation_id=conversation_id,
            callback=event_callback,
            event=conversation_state_update_event,
        )

        # Verify the result
        assert result is not None
        assert result.status == EventCallbackResultStatus.SUCCESS

        # Verify PR comment was created instead of issue comment
        mock_repo.get_pull.assert_called_once_with(42)
        mock_pr.create_review_comment_reply.assert_called_once_with(
            comment_id='comment_123', body='Test summary from agent'
        )

    @patch('openhands.app_server.config.get_httpx_client')
    @patch('openhands.app_server.config.get_sandbox_service')
    @patch('openhands.app_server.config.get_app_conversation_info_service')
    async def test_missing_installation_id(
        self,
        mock_get_app_conversation_info_service,
        mock_get_sandbox_service,
        mock_get_httpx_client,
        conversation_state_update_event,
        event_callback,
        mock_app_conversation_info,
        mock_sandbox_info,
    ):
        """Test error handling when installation_id is missing."""
        processor = GithubV1CallbackProcessor(
            github_view_data={},  # Missing installation_id
            should_request_summary=True,
        )
        conversation_id = uuid4()

        # Mock services to avoid database calls
        mock_app_conversation_info_service = AsyncMock()
        mock_app_conversation_info_service.get_app_conversation_info.return_value = (
            mock_app_conversation_info
        )
        mock_get_app_conversation_info_service.return_value.__aenter__.return_value = (
            mock_app_conversation_info_service
        )

        mock_sandbox_service = AsyncMock()
        mock_sandbox_service.get_sandbox.return_value = mock_sandbox_info
        mock_get_sandbox_service.return_value.__aenter__.return_value = (
            mock_sandbox_service
        )

        mock_httpx_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {'response': 'Test summary from agent'}
        mock_response.raise_for_status.return_value = None
        mock_httpx_client.post.return_value = mock_response
        mock_get_httpx_client.return_value.__aenter__.return_value = mock_httpx_client

        result = await processor(
            conversation_id=conversation_id,
            callback=event_callback,
            event=conversation_state_update_event,
        )

        assert result is not None
        assert result.status == EventCallbackResultStatus.ERROR
        assert 'Missing installation ID' in result.detail

    @patch.dict(os.environ, {}, clear=True)  # Clear environment variables
    @patch('openhands.app_server.config.get_httpx_client')
    @patch('openhands.app_server.config.get_sandbox_service')
    @patch('openhands.app_server.config.get_app_conversation_info_service')
    async def test_missing_github_credentials(
        self,
        mock_get_app_conversation_info_service,
        mock_get_sandbox_service,
        mock_get_httpx_client,
        github_callback_processor,
        conversation_state_update_event,
        event_callback,
        mock_app_conversation_info,
        mock_sandbox_info,
    ):
        """Test error handling when GitHub credentials are missing."""
        conversation_id = uuid4()

        # Mock services to avoid database calls
        mock_app_conversation_info_service = AsyncMock()
        mock_app_conversation_info_service.get_app_conversation_info.return_value = (
            mock_app_conversation_info
        )
        mock_get_app_conversation_info_service.return_value.__aenter__.return_value = (
            mock_app_conversation_info_service
        )

        mock_sandbox_service = AsyncMock()
        mock_sandbox_service.get_sandbox.return_value = mock_sandbox_info
        mock_get_sandbox_service.return_value.__aenter__.return_value = (
            mock_sandbox_service
        )

        mock_httpx_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {'response': 'Test summary from agent'}
        mock_response.raise_for_status.return_value = None
        mock_httpx_client.post.return_value = mock_response
        mock_get_httpx_client.return_value.__aenter__.return_value = mock_httpx_client

        result = await github_callback_processor(
            conversation_id=conversation_id,
            callback=event_callback,
            event=conversation_state_update_event,
        )

        assert result is not None
        assert result.status == EventCallbackResultStatus.ERROR
        assert 'GitHub App credentials are not configured' in result.detail

    @patch.dict(
        os.environ,
        {
            'GITHUB_APP_CLIENT_ID': 'test_client_id',
            'GITHUB_APP_PRIVATE_KEY': 'test_private_key',
        },
    )
    @patch('openhands.app_server.config.get_app_conversation_info_service')
    async def test_conversation_not_found(
        self,
        mock_get_app_conversation_info_service,
        github_callback_processor,
        conversation_state_update_event,
        event_callback,
    ):
        """Test error handling when conversation is not found."""
        conversation_id = uuid4()

        # Mock service to return None (conversation not found)
        mock_app_conversation_info_service = AsyncMock()
        mock_app_conversation_info_service.get_app_conversation_info.return_value = None
        mock_get_app_conversation_info_service.return_value.__aenter__.return_value = (
            mock_app_conversation_info_service
        )

        result = await github_callback_processor(
            conversation_id=conversation_id,
            callback=event_callback,
            event=conversation_state_update_event,
        )

        assert result is not None
        assert result.status == EventCallbackResultStatus.ERROR
        assert f'Conversation not found: {conversation_id}' in result.detail

    @patch.dict(
        os.environ,
        {
            'GITHUB_APP_CLIENT_ID': 'test_client_id',
            'GITHUB_APP_PRIVATE_KEY': 'test_private_key',
        },
    )
    @patch('openhands.app_server.config.get_app_conversation_info_service')
    @patch('openhands.app_server.config.get_sandbox_service')
    async def test_sandbox_not_running(
        self,
        mock_get_sandbox_service,
        mock_get_app_conversation_info_service,
        github_callback_processor,
        conversation_state_update_event,
        event_callback,
        mock_app_conversation_info,
    ):
        """Test error handling when sandbox is not running."""
        conversation_id = uuid4()

        # Mock services
        mock_app_conversation_info_service = AsyncMock()
        mock_app_conversation_info_service.get_app_conversation_info.return_value = (
            mock_app_conversation_info
        )
        mock_get_app_conversation_info_service.return_value.__aenter__.return_value = (
            mock_app_conversation_info_service
        )

        # Mock sandbox service to return non-running sandbox
        mock_sandbox_info = SandboxInfo(
            id='sandbox_123',
            status=SandboxStatus.PAUSED,  # Not running
            session_api_key='test_api_key',
            created_by_user_id='test_user_123',
            sandbox_spec_id='spec_123',
        )
        mock_sandbox_service = AsyncMock()
        mock_sandbox_service.get_sandbox.return_value = mock_sandbox_info
        mock_get_sandbox_service.return_value.__aenter__.return_value = (
            mock_sandbox_service
        )

        result = await github_callback_processor(
            conversation_id=conversation_id,
            callback=event_callback,
            event=conversation_state_update_event,
        )

        assert result is not None
        assert result.status == EventCallbackResultStatus.ERROR
        assert 'Sandbox not running' in result.detail

    @patch.dict(
        os.environ,
        {
            'GITHUB_APP_CLIENT_ID': 'test_client_id',
            'GITHUB_APP_PRIVATE_KEY': 'test_private_key',
        },
    )
    @patch('openhands.app_server.config.get_app_conversation_info_service')
    @patch('openhands.app_server.config.get_sandbox_service')
    @patch('openhands.app_server.config.get_httpx_client')
    @patch(
        'openhands.app_server.event_callback.github_v1_callback_processor.get_prompt_template'
    )
    async def test_agent_server_http_error(
        self,
        mock_get_prompt_template,
        mock_get_httpx_client,
        mock_get_sandbox_service,
        mock_get_app_conversation_info_service,
        github_callback_processor,
        conversation_state_update_event,
        event_callback,
        mock_app_conversation_info,
        mock_sandbox_info,
    ):
        """Test error handling when agent server returns HTTP error."""
        conversation_id = uuid4()

        # Mock services
        mock_app_conversation_info_service = AsyncMock()
        mock_app_conversation_info_service.get_app_conversation_info.return_value = (
            mock_app_conversation_info
        )
        mock_get_app_conversation_info_service.return_value.__aenter__.return_value = (
            mock_app_conversation_info_service
        )

        mock_sandbox_service = AsyncMock()
        mock_sandbox_service.get_sandbox.return_value = mock_sandbox_info
        mock_get_sandbox_service.return_value.__aenter__.return_value = (
            mock_sandbox_service
        )

        # Mock httpx client to raise HTTP error
        mock_httpx_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = 'Internal Server Error'
        mock_response.headers = {}
        mock_error = httpx.HTTPStatusError(
            'HTTP 500 error', request=MagicMock(), response=mock_response
        )
        mock_httpx_client.post.side_effect = mock_error
        mock_get_httpx_client.return_value.__aenter__.return_value = mock_httpx_client

        mock_get_prompt_template.return_value = 'Please provide a summary'

        result = await github_callback_processor(
            conversation_id=conversation_id,
            callback=event_callback,
            event=conversation_state_update_event,
        )

        assert result is not None
        assert result.status == EventCallbackResultStatus.ERROR
        assert 'Failed to send message to agent server' in result.detail

    @patch.dict(
        os.environ,
        {
            'GITHUB_APP_CLIENT_ID': 'test_client_id',
            'GITHUB_APP_PRIVATE_KEY': 'test_private_key',
        },
    )
    @patch('openhands.app_server.config.get_app_conversation_info_service')
    @patch('openhands.app_server.config.get_sandbox_service')
    @patch('openhands.app_server.config.get_httpx_client')
    @patch(
        'openhands.app_server.event_callback.github_v1_callback_processor.get_prompt_template'
    )
    async def test_agent_server_timeout(
        self,
        mock_get_prompt_template,
        mock_get_httpx_client,
        mock_get_sandbox_service,
        mock_get_app_conversation_info_service,
        github_callback_processor,
        conversation_state_update_event,
        event_callback,
        mock_app_conversation_info,
        mock_sandbox_info,
    ):
        """Test error handling when agent server request times out."""
        conversation_id = uuid4()

        # Mock services
        mock_app_conversation_info_service = AsyncMock()
        mock_app_conversation_info_service.get_app_conversation_info.return_value = (
            mock_app_conversation_info
        )
        mock_get_app_conversation_info_service.return_value.__aenter__.return_value = (
            mock_app_conversation_info_service
        )

        mock_sandbox_service = AsyncMock()
        mock_sandbox_service.get_sandbox.return_value = mock_sandbox_info
        mock_get_sandbox_service.return_value.__aenter__.return_value = (
            mock_sandbox_service
        )

        # Mock httpx client to raise timeout error
        mock_httpx_client = AsyncMock()
        mock_httpx_client.post.side_effect = httpx.TimeoutException('Request timeout')
        mock_get_httpx_client.return_value.__aenter__.return_value = mock_httpx_client

        mock_get_prompt_template.return_value = 'Please provide a summary'

        result = await github_callback_processor(
            conversation_id=conversation_id,
            callback=event_callback,
            event=conversation_state_update_event,
        )

        assert result is not None
        assert result.status == EventCallbackResultStatus.ERROR
        assert 'Request timeout after 30 seconds' in result.detail

    def test_get_installation_access_token_missing_id(self):
        """Test _get_installation_access_token with missing installation_id."""
        processor = GithubV1CallbackProcessor(
            github_view_data={},  # Missing installation_id
        )

        with pytest.raises(ValueError, match='Missing installation ID'):
            processor._get_installation_access_token()

    @patch.dict(os.environ, {}, clear=True)  # Clear environment variables
    def test_get_installation_access_token_missing_credentials(
        self, github_callback_processor
    ):
        """Test _get_installation_access_token with missing GitHub credentials."""
        with pytest.raises(
            ValueError, match='GitHub App credentials are not configured'
        ):
            github_callback_processor._get_installation_access_token()

    @patch.dict(
        os.environ,
        {
            'GITHUB_APP_CLIENT_ID': 'test_client_id',
            'GITHUB_APP_PRIVATE_KEY': 'test_private_key\\nwith_newlines',
        },
    )
    @patch(
        'openhands.app_server.event_callback.github_v1_callback_processor.GithubIntegration'
    )
    def test_get_installation_access_token_success(
        self, mock_github_integration, github_callback_processor
    ):
        """Test successful _get_installation_access_token."""
        # Mock GitHub integration
        mock_token_data = MagicMock()
        mock_token_data.token = 'test_access_token'
        mock_integration_instance = MagicMock()
        mock_integration_instance.get_access_token.return_value = mock_token_data
        mock_github_integration.return_value = mock_integration_instance

        token = github_callback_processor._get_installation_access_token()

        assert token == 'test_access_token'
        mock_github_integration.assert_called_once_with(
            'test_client_id', 'test_private_key\nwith_newlines'
        )
        mock_integration_instance.get_access_token.assert_called_once_with(12345)

    @patch('openhands.app_server.event_callback.github_v1_callback_processor.Github')
    async def test_post_summary_to_github_issue_comment(
        self, mock_github, github_callback_processor
    ):
        """Test _post_summary_to_github for regular issue comment."""
        # Mock GitHub client
        mock_github_client = MagicMock()
        mock_repo = MagicMock()
        mock_issue = MagicMock()
        mock_repo.get_issue.return_value = mock_issue
        mock_github_client.get_repo.return_value = mock_repo
        mock_github.return_value.__enter__.return_value = mock_github_client

        # Mock the token method
        with patch.object(
            github_callback_processor,
            '_get_installation_access_token',
            return_value='test_token',
        ):
            await github_callback_processor._post_summary_to_github('Test summary')

        # Verify GitHub API calls
        mock_github.assert_called_once_with('test_token')
        mock_github_client.get_repo.assert_called_once_with('test-owner/test-repo')
        mock_repo.get_issue.assert_called_once_with(number=42)
        mock_issue.create_comment.assert_called_once_with('Test summary')

    @patch('openhands.app_server.event_callback.github_v1_callback_processor.Github')
    async def test_post_summary_to_github_pr_comment(
        self, mock_github, github_callback_processor_inline
    ):
        """Test _post_summary_to_github for inline PR comment."""
        # Mock GitHub client
        mock_github_client = MagicMock()
        mock_repo = MagicMock()
        mock_pr = MagicMock()
        mock_repo.get_pull.return_value = mock_pr
        mock_github_client.get_repo.return_value = mock_repo
        mock_github.return_value.__enter__.return_value = mock_github_client

        # Mock the token method
        with patch.object(
            github_callback_processor_inline,
            '_get_installation_access_token',
            return_value='test_token',
        ):
            await github_callback_processor_inline._post_summary_to_github(
                'Test summary'
            )

        # Verify GitHub API calls
        mock_github.assert_called_once_with('test_token')
        mock_github_client.get_repo.assert_called_once_with('test-owner/test-repo')
        mock_repo.get_pull.assert_called_once_with(42)
        mock_pr.create_review_comment_reply.assert_called_once_with(
            comment_id='comment_123', body='Test summary'
        )

    async def test_post_summary_to_github_missing_token(
        self, github_callback_processor
    ):
        """Test _post_summary_to_github with missing token."""
        with patch.object(
            github_callback_processor, '_get_installation_access_token', return_value=''
        ):
            with pytest.raises(RuntimeError, match='Missing GitHub credentials'):
                await github_callback_processor._post_summary_to_github('Test summary')

    @patch.dict(
        os.environ,
        {
            'GITHUB_APP_CLIENT_ID': 'test_client_id',
            'GITHUB_APP_PRIVATE_KEY': 'test_private_key',
            'WEB_HOST': 'test.example.com',
        },
    )
    @patch('openhands.app_server.config.get_httpx_client')
    @patch('openhands.app_server.config.get_sandbox_service')
    @patch('openhands.app_server.config.get_app_conversation_info_service')
    async def test_exception_handling_posts_error_to_github(
        self,
        mock_get_app_conversation_info_service,
        mock_get_sandbox_service,
        mock_get_httpx_client,
        github_callback_processor,
        conversation_state_update_event,
        event_callback,
        mock_app_conversation_info,
        mock_sandbox_info,
    ):
        """Test that exceptions during processing result in error messages posted to GitHub."""
        conversation_id = uuid4()

        # Mock services
        mock_app_conversation_info_service = AsyncMock()
        mock_app_conversation_info_service.get_app_conversation_info.return_value = (
            mock_app_conversation_info
        )
        mock_get_app_conversation_info_service.return_value.__aenter__.return_value = (
            mock_app_conversation_info_service
        )

        mock_sandbox_service = AsyncMock()
        mock_sandbox_service.get_sandbox.return_value = mock_sandbox_info
        mock_get_sandbox_service.return_value.__aenter__.return_value = (
            mock_sandbox_service
        )

        # Mock httpx client to simulate failure during summary request
        mock_httpx_client = AsyncMock()
        mock_httpx_client.post.side_effect = Exception('Simulated agent server error')
        mock_get_httpx_client.return_value.__aenter__.return_value = mock_httpx_client

        # Mock GitHub integration for error posting
        with patch(
            'openhands.app_server.event_callback.github_v1_callback_processor.GithubIntegration'
        ) as mock_github_integration:
            mock_integration = MagicMock()
            mock_github_integration.return_value = mock_integration
            mock_integration.get_access_token.return_value.token = 'test_token'

            with patch(
                'openhands.app_server.event_callback.github_v1_callback_processor.Github'
            ) as mock_github:
                mock_gh = MagicMock()
                mock_github.return_value.__enter__.return_value = mock_gh
                mock_repo = MagicMock()
                mock_gh.get_repo.return_value = mock_repo
                mock_issue = MagicMock()
                mock_repo.get_issue.return_value = mock_issue

                result = await github_callback_processor(
                    conversation_id=conversation_id,
                    callback=event_callback,
                    event=conversation_state_update_event,
                )

        # Verify the result indicates an error
        assert result is not None
        assert result.status == EventCallbackResultStatus.ERROR
        assert 'Simulated agent server error' in result.detail

        # Verify that an error message was posted to GitHub
        mock_issue.create_comment.assert_called_once()
        # Get the comment body from either positional or keyword arguments
        call_args = mock_issue.create_comment.call_args
        if call_args[1]:  # keyword arguments
            error_comment = (
                call_args[1]['body'] if 'body' in call_args[1] else call_args[0][0]
            )
        else:  # positional arguments
            error_comment = call_args[0][0]

        assert (
            'OpenHands encountered an error: **Simulated agent server error**'
            in error_comment
        )
        assert (
            f'conversations/{conversation_id}' in error_comment
        )  # Check for conversation ID in URL
        assert 'for more information.' in error_comment
