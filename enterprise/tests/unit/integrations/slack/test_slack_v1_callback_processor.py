"""
Tests for the SlackV1CallbackProcessor.

Covers:
- Event filtering
- Successful summary + Slack posting
- Error conditions (missing credentials, conversation/sandbox issues)
- Agent server HTTP/timeout errors
- Low-level helper methods
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import httpx
import pytest
from integrations.slack.slack_v1_callback_processor import (
    SlackV1CallbackProcessor,
)

from openhands.app_server.app_conversation.app_conversation_models import (
    AppConversationInfo,
)
from openhands.app_server.event_callback.event_callback_models import EventCallback
from openhands.app_server.event_callback.event_callback_result_models import (
    EventCallbackResultStatus,
)
from openhands.app_server.sandbox.sandbox_models import (
    ExposedUrl,
    SandboxInfo,
    SandboxStatus,
)
from openhands.events.action.message import MessageAction
from openhands.sdk.event import ConversationStateUpdateEvent

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def slack_callback_processor():
    return SlackV1CallbackProcessor(
        slack_view_data={
            'channel_id': 'C1234567890',
            'message_ts': '1234567890.123456',
            'slack_team_id': 'T1234567890',
            'bot_access_token': 'xoxb-test-token',
        },
        should_request_summary=True,
        should_extract=True,
    )


@pytest.fixture
def conversation_state_update_event():
    return ConversationStateUpdateEvent(key='execution_status', value='finished')


@pytest.fixture
def wrong_event():
    return MessageAction(content='Hello world')


@pytest.fixture
def wrong_state_event():
    return ConversationStateUpdateEvent(key='execution_status', value='running')


@pytest.fixture
def event_callback():
    return EventCallback(
        id=uuid4(),
        conversation_id=uuid4(),
        processor=SlackV1CallbackProcessor(),
        event_kind='ConversationStateUpdateEvent',
    )


@pytest.fixture
def mock_app_conversation_info():
    return AppConversationInfo(
        id=uuid4(),
        created_by_user_id='test-user-123',
        sandbox_id=str(uuid4()),
        title='Test Conversation',
    )


@pytest.fixture
def mock_sandbox_info():
    return SandboxInfo(
        id=str(uuid4()),
        created_by_user_id='test-user-123',
        sandbox_spec_id='test-spec-123',
        status=SandboxStatus.RUNNING,
        session_api_key='test-session-key',
        exposed_urls=[
            ExposedUrl(
                url='http://localhost:8000',
                name='AGENT_SERVER',
                port=8000,
            )
        ],
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestSlackV1CallbackProcessor:
    """Test the SlackV1CallbackProcessor class."""

    async def test_call_with_wrong_event_type(
        self, slack_callback_processor, wrong_event, event_callback
    ):
        """Test that the processor ignores events it shouldn't process."""
        result = await slack_callback_processor(uuid4(), event_callback, wrong_event)
        assert result is None

    async def test_call_with_wrong_state_event(
        self, slack_callback_processor, wrong_state_event, event_callback
    ):
        """Test that the processor ignores state events it shouldn't process."""
        result = await slack_callback_processor(
            uuid4(), event_callback, wrong_state_event
        )
        assert result is None

    async def test_call_should_request_summary_false(
        self, conversation_state_update_event, event_callback
    ):
        """Test that the processor does nothing when should_request_summary is False."""
        processor = SlackV1CallbackProcessor(
            slack_view_data={
                'channel_id': 'C1234567890',
                'message_ts': '1234567890.123456',
                'slack_team_id': 'T1234567890',
                'bot_access_token': 'xoxb-test-token',
            },
            should_request_summary=False,
        )
        result = await processor(
            uuid4(), event_callback, conversation_state_update_event
        )
        assert result is None

    @patch('openhands.app_server.config.get_httpx_client')
    @patch('openhands.app_server.config.get_sandbox_service')
    @patch('openhands.app_server.config.get_app_conversation_info_service')
    @patch('integrations.slack.slack_v1_callback_processor.get_prompt_template')
    @patch('integrations.slack.slack_v1_callback_processor.WebClient')
    async def test_successful_callback_execution(
        self,
        mock_web_client,
        mock_get_prompt_template,
        mock_get_app_conversation_info_service,
        mock_get_sandbox_service,
        mock_get_httpx_client,
        slack_callback_processor,
        conversation_state_update_event,
        event_callback,
        mock_app_conversation_info,
        mock_sandbox_info,
    ):
        """Test successful callback execution with summary generation and Slack posting."""
        conversation_id = uuid4()

        # Mock prompt template
        mock_get_prompt_template.return_value = 'Please provide a summary'

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
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.post.return_value = mock_response
        mock_get_httpx_client.return_value.__aenter__.return_value = mock_httpx_client

        # Mock Slack WebClient
        mock_slack_client = MagicMock()
        mock_slack_client.chat_postMessage.return_value = {'ok': True}
        mock_web_client.return_value = mock_slack_client

        # Execute
        result = await slack_callback_processor(
            conversation_id, event_callback, conversation_state_update_event
        )

        # Verify result
        assert result is not None
        assert result.status == EventCallbackResultStatus.SUCCESS
        assert result.conversation_id == conversation_id
        assert result.detail == 'Test summary from agent'

        # Verify Slack posting
        mock_slack_client.chat_postMessage.assert_called_once_with(
            channel='C1234567890',
            text='Test summary from agent',
            thread_ts='1234567890.123456',
            unfurl_links=False,
            unfurl_media=False,
        )

    async def test_missing_bot_token(
        self, conversation_state_update_event, event_callback
    ):
        """Test error handling when bot access token is missing."""
        processor = SlackV1CallbackProcessor(
            slack_view_data={
                'channel_id': 'C1234567890',
                'message_ts': '1234567890.123456',
                'slack_team_id': 'T1234567890',
                # Missing bot_access_token
            },
            should_request_summary=True,
        )

        with patch('openhands.app_server.config.get_httpx_client'), patch(
            'openhands.app_server.config.get_sandbox_service'
        ), patch('openhands.app_server.config.get_app_conversation_info_service'):
            # Mock successful summary generation
            with patch.object(
                processor, '_request_summary', return_value='Test summary'
            ):
                result = await processor(
                    uuid4(), event_callback, conversation_state_update_event
                )

        assert result is not None
        assert result.status == EventCallbackResultStatus.ERROR
        assert 'Missing Slack bot access token' in result.detail

    @patch('integrations.slack.slack_v1_callback_processor.WebClient')
    async def test_slack_api_error(
        self,
        mock_web_client,
        slack_callback_processor,
        conversation_state_update_event,
        event_callback,
    ):
        """Test error handling when Slack API returns an error."""
        # Mock Slack WebClient with error response
        mock_slack_client = MagicMock()
        mock_slack_client.chat_postMessage.return_value = {
            'ok': False,
            'error': 'channel_not_found',
        }
        mock_web_client.return_value = mock_slack_client

        with patch('openhands.app_server.config.get_httpx_client'), patch(
            'openhands.app_server.config.get_sandbox_service'
        ), patch('openhands.app_server.config.get_app_conversation_info_service'):
            # Mock successful summary generation
            with patch.object(
                slack_callback_processor,
                '_request_summary',
                return_value='Test summary',
            ):
                result = await slack_callback_processor(
                    uuid4(), event_callback, conversation_state_update_event
                )

        assert result is not None
        assert result.status == EventCallbackResultStatus.ERROR
        assert 'Slack API error: channel_not_found' in result.detail

    @patch('openhands.app_server.config.get_httpx_client')
    @patch('openhands.app_server.config.get_sandbox_service')
    @patch('openhands.app_server.config.get_app_conversation_info_service')
    @patch('integrations.slack.slack_v1_callback_processor.get_prompt_template')
    async def test_agent_server_http_error(
        self,
        mock_get_prompt_template,
        mock_get_app_conversation_info_service,
        mock_get_sandbox_service,
        mock_get_httpx_client,
        slack_callback_processor,
        conversation_state_update_event,
        event_callback,
        mock_app_conversation_info,
        mock_sandbox_info,
    ):
        """Test error handling when agent server returns HTTP error."""
        conversation_id = uuid4()

        # Mock prompt template
        mock_get_prompt_template.return_value = 'Please provide a summary'

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

        # Mock HTTP error
        mock_httpx_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = 'Internal Server Error'
        mock_response.headers = {}
        http_error = httpx.HTTPStatusError(
            'Server error', request=MagicMock(), response=mock_response
        )
        mock_httpx_client.post.side_effect = http_error
        mock_get_httpx_client.return_value.__aenter__.return_value = mock_httpx_client

        # Execute
        result = await slack_callback_processor(
            conversation_id, event_callback, conversation_state_update_event
        )

        # Verify error result
        assert result is not None
        assert result.status == EventCallbackResultStatus.ERROR
        assert 'Failed to send message to agent server' in result.detail

    @patch('openhands.app_server.config.get_httpx_client')
    @patch('openhands.app_server.config.get_sandbox_service')
    @patch('openhands.app_server.config.get_app_conversation_info_service')
    @patch('integrations.slack.slack_v1_callback_processor.get_prompt_template')
    async def test_agent_server_timeout(
        self,
        mock_get_prompt_template,
        mock_get_app_conversation_info_service,
        mock_get_sandbox_service,
        mock_get_httpx_client,
        slack_callback_processor,
        conversation_state_update_event,
        event_callback,
        mock_app_conversation_info,
        mock_sandbox_info,
    ):
        """Test error handling when agent server request times out."""
        conversation_id = uuid4()

        # Mock prompt template
        mock_get_prompt_template.return_value = 'Please provide a summary'

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

        # Mock timeout error
        mock_httpx_client = AsyncMock()
        mock_httpx_client.post.side_effect = httpx.TimeoutException('Request timeout')
        mock_get_httpx_client.return_value.__aenter__.return_value = mock_httpx_client

        # Execute
        result = await slack_callback_processor(
            conversation_id, event_callback, conversation_state_update_event
        )

        # Verify error result
        assert result is not None
        assert result.status == EventCallbackResultStatus.ERROR
        assert 'Request timeout after 30 seconds' in result.detail
