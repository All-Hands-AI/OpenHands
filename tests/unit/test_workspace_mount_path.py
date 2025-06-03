from unittest.mock import MagicMock, patch

import pytest
from litellm import ChatCompletionMessageToolCall

from openhands.agenthub.codeact_agent.function_calling import response_to_actions
from openhands.core.config import AppConfig
from openhands.events import EventStream
from openhands.events.action import FileEditAction
from openhands.runtime.impl.docker.docker_runtime import DockerRuntime


@pytest.fixture
def mock_docker_client():
    with patch('docker.from_env') as mock_client:
        container_mock = MagicMock()
        container_mock.status = 'running'
        container_mock.attrs = {
            'Config': {
                'Env': ['port=12345', 'VSCODE_PORT=54321'],
                'ExposedPorts': {'12345/tcp': {}, '54321/tcp': {}},
            }
        }
        mock_client.return_value.containers.get.return_value = container_mock
        mock_client.return_value.containers.run.return_value = container_mock
        # Mock version info for BuildKit check
        mock_client.return_value.version.return_value = {
            'Version': '20.10.0',
            'Components': [{'Name': 'Engine', 'Version': '20.10.0'}],
        }  # Ensure version is >= 18.09
        yield mock_client.return_value


@pytest.fixture
def config():
    config = AppConfig()
    config.sandbox.keep_runtime_alive = False
    return config


@pytest.fixture
def event_stream():
    return MagicMock(spec=EventStream)


class TestWorkspaceMountPath:
    """Tests for workspace_mount_path_in_sandbox and workspace_mount_path_in_sandbox_store_in_session behavior."""

    def test_workspace_mount_path_when_store_in_session_true(
        self, mock_docker_client, config, event_stream
    ):
        """Test that workspace_mount_path is modified when workspace_mount_path_in_sandbox_store_in_session is True."""
        # Arrange
        sid = 'test-sid'
        config.workspace_mount_path = '/path/to/workspace'
        config.workspace_mount_path_in_sandbox = '/workspace'
        config.workspace_mount_path_in_sandbox_store_in_session = True

        # Mock the container creation
        container_mock = MagicMock()
        container_mock.status = 'running'
        mock_docker_client.containers.run.return_value = container_mock

        # Mock find_available_port to return a fixed port
        with patch(
            'openhands.runtime.utils.find_available_tcp_port', return_value=12345
        ):
            # Act
            runtime = DockerRuntime(config, event_stream, sid=sid)
            # Call _init_container() to trigger the path modifications
            runtime._init_container()

        # Check that both paths are modified to include the session ID
        assert runtime.config.workspace_mount_path == '/path/to/workspace/test-sid'
        assert runtime.config.workspace_mount_path_in_sandbox == '/workspace/test-sid'

    def test_workspace_mount_path_when_store_in_session_false(
        self, mock_docker_client, config, event_stream
    ):
        """Test that workspace_mount_path is not modified when workspace_mount_path_in_sandbox_store_in_session is False."""
        # Arrange
        sid = 'test-sid'
        config.workspace_mount_path = '/path/to/workspace'
        config.workspace_mount_path_in_sandbox = '/workspace'
        config.workspace_mount_path_in_sandbox_store_in_session = False

        # Mock the container creation
        container_mock = MagicMock()
        container_mock.status = 'running'
        mock_docker_client.containers.run.return_value = container_mock

        # Mock find_available_port to return a fixed port
        with patch(
            'openhands.runtime.utils.find_available_tcp_port', return_value=12345
        ):
            # Act
            runtime = DockerRuntime(config, event_stream, sid=sid)
            # Call _init_container() to trigger the path modifications
            runtime._init_container()

        # Check that the paths were not modified
        assert runtime.config.workspace_mount_path == '/path/to/workspace'
        assert runtime.config.workspace_mount_path_in_sandbox == '/workspace'

    @patch('openhands.agenthub.codeact_agent.function_calling.ToolCallMetadata')
    def test_path_modification_in_function_calling_when_store_in_session_true(
        self, mock_tool_call_metadata
    ):
        """Test that path is modified in function_calling when workspace_mount_path_in_sandbox_store_in_session is True."""
        # Arrange
        sid = 'test-sid'
        workspace_mount_path_in_sandbox_store_in_session = True

        # Create a mock response with a tool call that includes a path
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    tool_calls=[
                        ChatCompletionMessageToolCall(
                            function={
                                'name': 'edit_file',
                                'arguments': '{"path": "/workspace/path/to/file/file.txt", "content": "test"}',
                            },
                            id='test-id',
                        )
                    ]
                )
            )
        ]

        # Mock the ToolCallMetadata to return a valid instance
        mock_metadata = MagicMock()
        mock_tool_call_metadata.return_value = mock_metadata

        # Act
        actions = response_to_actions(
            mock_response,
            sid=sid,
            workspace_mount_path_in_sandbox_store_in_session=workspace_mount_path_in_sandbox_store_in_session,
        )

        # Assert
        assert len(actions) > 0
        assert isinstance(actions[0], FileEditAction)
        assert actions[0].path == '/workspace/test-sid/path/to/file/file.txt'

    @patch('openhands.agenthub.codeact_agent.function_calling.ToolCallMetadata')
    def test_path_modification_in_function_calling_when_store_in_session_false(
        self, mock_tool_call_metadata
    ):
        """Test that path is not modified in function_calling when workspace_mount_path_in_sandbox_store_in_session is False."""
        # Arrange
        sid = 'test-sid'
        workspace_mount_path_in_sandbox_store_in_session = False

        # Create a mock response with a tool call that includes a path
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    tool_calls=[
                        ChatCompletionMessageToolCall(
                            function={
                                'name': 'edit_file',
                                'arguments': '{"path": "/workspace/path/to/file/file.txt", "content": "test"}',
                            },
                            id='test-id',
                        )
                    ]
                )
            )
        ]

        # Mock the ToolCallMetadata to return a valid instance
        mock_metadata = MagicMock()
        mock_tool_call_metadata.return_value = mock_metadata

        # Act
        actions = response_to_actions(
            mock_response,
            sid=sid,
            workspace_mount_path_in_sandbox_store_in_session=workspace_mount_path_in_sandbox_store_in_session,
        )

        # Assert
        assert len(actions) > 0
        assert isinstance(actions[0], FileEditAction)
        assert actions[0].path == '/workspace/path/to/file/file.txt'

    @patch('openhands.agenthub.codeact_agent.function_calling.ToolCallMetadata')
    def test_path_not_modified_when_sid_already_in_path(self, mock_tool_call_metadata):
        """Test that path is not modified when sid is already in the path."""
        # Arrange
        sid = 'test-sid'
        workspace_mount_path_in_sandbox_store_in_session = True

        # Create a mock response with a tool call that includes a path with sid already in it
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    tool_calls=[
                        ChatCompletionMessageToolCall(
                            function={
                                'name': 'edit_file',
                                'arguments': f'{{"path": "/workspace/path/to/file/{sid}/file.txt", "content": "test"}}',
                            },
                            id='test-id',
                        )
                    ]
                )
            )
        ]

        # Mock the ToolCallMetadata to return a valid instance
        mock_metadata = MagicMock()
        mock_tool_call_metadata.return_value = mock_metadata

        # Act
        actions = response_to_actions(
            mock_response,
            sid=sid,
            workspace_mount_path_in_sandbox_store_in_session=workspace_mount_path_in_sandbox_store_in_session,
        )

        # Assert
        assert len(actions) > 0
        assert isinstance(actions[0], FileEditAction)
        assert actions[0].path == f'/workspace/path/to/file/{sid}/file.txt'

    @patch('openhands.agenthub.codeact_agent.function_calling.ToolCallMetadata')
    def test_str_replace_editor_tool_path_modification_when_store_in_session_true(
        self, mock_tool_call_metadata
    ):
        """Test that path is modified in str_replace_editor_tool when workspace_mount_path_in_sandbox_store_in_session is True."""
        # Arrange
        sid = 'test-sid'
        workspace_mount_path_in_sandbox_store_in_session = True

        # Create a mock response with a tool call that includes a path
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    tool_calls=[
                        ChatCompletionMessageToolCall(
                            function={
                                'name': 'str_replace_editor',
                                'arguments': '{"path": "/workspace/path/to/file/file.txt", "command": "edit", "content": "test"}',
                            },
                            id='test-id',
                        )
                    ]
                )
            )
        ]

        # Mock the ToolCallMetadata to return a valid instance
        mock_metadata = MagicMock()
        mock_tool_call_metadata.return_value = mock_metadata

        # Act
        actions = response_to_actions(
            mock_response,
            sid=sid,
            workspace_mount_path_in_sandbox_store_in_session=workspace_mount_path_in_sandbox_store_in_session,
        )

        # Assert
        assert len(actions) > 0
        assert isinstance(actions[0], FileEditAction)
        assert actions[0].path == '/workspace/test-sid/path/to/file/file.txt'

    @patch('openhands.agenthub.codeact_agent.function_calling.ToolCallMetadata')
    def test_str_replace_editor_tool_path_modification_when_store_in_session_false(
        self, mock_tool_call_metadata
    ):
        """Test that path is not modified in str_replace_editor_tool when workspace_mount_path_in_sandbox_store_in_session is False."""
        # Arrange
        sid = 'test-sid'
        workspace_mount_path_in_sandbox_store_in_session = False

        # Create a mock response with a tool call that includes a path
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    tool_calls=[
                        ChatCompletionMessageToolCall(
                            function={
                                'name': 'str_replace_editor',
                                'arguments': '{"path": "/workspace/path/to/file/file.txt", "command": "edit", "content": "test"}',
                            },
                            id='test-id',
                        )
                    ]
                )
            )
        ]

        # Mock the ToolCallMetadata to return a valid instance
        mock_metadata = MagicMock()
        mock_tool_call_metadata.return_value = mock_metadata

        # Act
        actions = response_to_actions(
            mock_response,
            sid=sid,
            workspace_mount_path_in_sandbox_store_in_session=workspace_mount_path_in_sandbox_store_in_session,
        )

        # Assert
        assert len(actions) > 0
        assert isinstance(actions[0], FileEditAction)
        assert actions[0].path == '/workspace/path/to/file/file.txt'

    @patch('openhands.agenthub.codeact_agent.function_calling.ToolCallMetadata')
    def test_str_replace_editor_tool_path_not_modified_when_sid_already_in_path(
        self, mock_tool_call_metadata
    ):
        """Test that path is not modified in str_replace_editor_tool when sid is already in the path."""
        # Arrange
        sid = 'test-sid'
        workspace_mount_path_in_sandbox_store_in_session = True

        # Create a mock response with a tool call that includes a path with sid already in it
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    tool_calls=[
                        ChatCompletionMessageToolCall(
                            function={
                                'name': 'str_replace_editor',
                                'arguments': f'{{"path": "/workspace/path/to/file/{sid}/file.txt", "command": "edit", "content": "test"}}',
                            },
                            id='test-id',
                        )
                    ]
                )
            )
        ]

        # Mock the ToolCallMetadata to return a valid instance
        mock_metadata = MagicMock()
        mock_tool_call_metadata.return_value = mock_metadata

        # Act
        actions = response_to_actions(
            mock_response,
            sid=sid,
            workspace_mount_path_in_sandbox_store_in_session=workspace_mount_path_in_sandbox_store_in_session,
        )

        # Assert
        assert len(actions) > 0
        assert isinstance(actions[0], FileEditAction)
        assert actions[0].path == f'/workspace/path/to/file/{sid}/file.txt'
