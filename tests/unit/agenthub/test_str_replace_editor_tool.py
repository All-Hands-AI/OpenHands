"""Tests for str_replace_editor tool workspace path detection."""

import os
import sys
from unittest.mock import patch, mock_open

import pytest

# Import the functions directly to avoid dependency issues
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

try:
    from openhands.agenthub.codeact_agent.tools.str_replace_editor import (
        _is_running_in_container,
        _get_workspace_mount_path_from_env,
        create_str_replace_editor_tool,
    )
except ImportError:
    # If import fails due to dependencies, skip these tests
    pytest.skip("Cannot import str_replace_editor due to missing dependencies", allow_module_level=True)


class TestContainerDetection:
    """Test container detection logic."""

    def test_dockerenv_detection(self):
        """Test detection via /.dockerenv file."""
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = True
            assert _is_running_in_container() is True

    def test_cgroup_docker_detection(self):
        """Test detection via cgroup with docker."""
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = False
            with patch('builtins.open', mock_open(read_data='12:memory:/docker/container123\n')):
                assert _is_running_in_container() is True

    def test_cgroup_containerd_detection(self):
        """Test detection via cgroup with containerd."""
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = False
            with patch('builtins.open', mock_open(read_data='12:memory:/containerd/container123\n')):
                assert _is_running_in_container() is True

    def test_no_container_detection(self):
        """Test when not running in container."""
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = False
            with patch('builtins.open', mock_open(read_data='12:memory:/\n')):
                assert _is_running_in_container() is False

    def test_cgroup_read_error(self):
        """Test when cgroup file cannot be read."""
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = False
            with patch('builtins.open', side_effect=FileNotFoundError()):
                assert _is_running_in_container() is False


class TestWorkspacePathDetection:
    """Test workspace path detection logic."""

    def test_docker_runtime_ignores_sandbox_volumes(self):
        """Test that DockerRuntime ignores SANDBOX_VOLUMES and uses /workspace."""
        with patch('openhands.agenthub.codeact_agent.tools.str_replace_editor._is_running_in_container', return_value=True):
            with patch.dict(os.environ, {'SANDBOX_VOLUMES': '/host/app:/workspace:rw'}):
                result = _get_workspace_mount_path_from_env()
                assert result == '/workspace'

    def test_local_runtime_uses_sandbox_volumes(self):
        """Test that LocalRuntime uses host path from SANDBOX_VOLUMES."""
        with patch('openhands.agenthub.codeact_agent.tools.str_replace_editor._is_running_in_container', return_value=False):
            with patch.dict(os.environ, {'SANDBOX_VOLUMES': '/host/app:/workspace:rw'}):
                result = _get_workspace_mount_path_from_env()
                assert result == '/host/app'

    def test_local_runtime_multiple_mounts(self):
        """Test LocalRuntime with multiple mounts, finds /workspace mount."""
        with patch('openhands.agenthub.codeact_agent.tools.str_replace_editor._is_running_in_container', return_value=False):
            with patch.dict(os.environ, {'SANDBOX_VOLUMES': '/tmp:/tmp:rw,/home/user/project:/workspace:rw,/var:/var:rw'}):
                result = _get_workspace_mount_path_from_env()
                assert result == '/home/user/project'

    def test_local_runtime_no_workspace_mount(self):
        """Test LocalRuntime with no /workspace mount falls back to default."""
        with patch('openhands.agenthub.codeact_agent.tools.str_replace_editor._is_running_in_container', return_value=False):
            with patch.dict(os.environ, {'SANDBOX_VOLUMES': '/tmp:/tmp:rw,/var:/var:rw'}):
                result = _get_workspace_mount_path_from_env()
                assert result == '/workspace'

    def test_local_runtime_no_sandbox_volumes(self):
        """Test LocalRuntime with no SANDBOX_VOLUMES falls back to default."""
        with patch('openhands.agenthub.codeact_agent.tools.str_replace_editor._is_running_in_container', return_value=False):
            with patch.dict(os.environ, {}, clear=True):
                result = _get_workspace_mount_path_from_env()
                assert result == '/workspace'

    def test_local_runtime_empty_sandbox_volumes(self):
        """Test LocalRuntime with empty SANDBOX_VOLUMES falls back to default."""
        with patch('openhands.agenthub.codeact_agent.tools.str_replace_editor._is_running_in_container', return_value=False):
            with patch.dict(os.environ, {'SANDBOX_VOLUMES': ''}):
                result = _get_workspace_mount_path_from_env()
                assert result == '/workspace'

    def test_relative_path_conversion(self):
        """Test that relative paths in SANDBOX_VOLUMES are converted to absolute."""
        with patch('openhands.agenthub.codeact_agent.tools.str_replace_editor._is_running_in_container', return_value=False):
            with patch.dict(os.environ, {'SANDBOX_VOLUMES': './relative/path:/workspace:rw'}):
                result = _get_workspace_mount_path_from_env()
                # Should be converted to absolute path
                assert os.path.isabs(result)
                assert result.endswith('relative/path')


class TestToolCreation:
    """Test tool creation with dynamic workspace paths."""

    def test_tool_creation_docker_runtime(self):
        """Test tool creation in DockerRuntime shows /workspace in description."""
        with patch('openhands.agenthub.codeact_agent.tools.str_replace_editor._is_running_in_container', return_value=True):
            with patch.dict(os.environ, {'SANDBOX_VOLUMES': '/host/app:/workspace:rw'}):
                tool = create_str_replace_editor_tool()
                path_description = tool['function']['parameters']['properties']['path']['description']
                assert '/workspace/file.py' in path_description
                assert '/workspace`.' in path_description
                # Should not contain host paths
                assert '/host/app' not in path_description

    def test_tool_creation_local_runtime(self):
        """Test tool creation in LocalRuntime shows host path in description."""
        with patch('openhands.agenthub.codeact_agent.tools.str_replace_editor._is_running_in_container', return_value=False):
            with patch.dict(os.environ, {'SANDBOX_VOLUMES': '/host/app:/workspace:rw'}):
                tool = create_str_replace_editor_tool()
                path_description = tool['function']['parameters']['properties']['path']['description']
                assert '/host/app/file.py' in path_description
                assert '/host/app`.' in path_description

    def test_tool_creation_explicit_workspace_path(self):
        """Test tool creation with explicitly provided workspace path."""
        tool = create_str_replace_editor_tool(workspace_mount_path_in_sandbox='/custom/path')
        path_description = tool['function']['parameters']['properties']['path']['description']
        assert '/custom/path/file.py' in path_description
        assert '/custom/path`.' in path_description

    def test_tool_creation_short_description(self):
        """Test tool creation with short description still has correct path."""
        with patch('openhands.agenthub.codeact_agent.tools.str_replace_editor._is_running_in_container', return_value=False):
            with patch.dict(os.environ, {'SANDBOX_VOLUMES': '/host/app:/workspace:rw'}):
                tool = create_str_replace_editor_tool(use_short_description=True)
                path_description = tool['function']['parameters']['properties']['path']['description']
                assert '/host/app/file.py' in path_description
                assert '/host/app`.' in path_description


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_malformed_sandbox_volumes(self):
        """Test handling of malformed SANDBOX_VOLUMES."""
        with patch('openhands.agenthub.codeact_agent.tools.str_replace_editor._is_running_in_container', return_value=False):
            # Missing colon separator
            with patch.dict(os.environ, {'SANDBOX_VOLUMES': '/host/app/workspace'}):
                result = _get_workspace_mount_path_from_env()
                assert result == '/workspace'

            # Only one part
            with patch.dict(os.environ, {'SANDBOX_VOLUMES': '/host/app:'}):
                result = _get_workspace_mount_path_from_env()
                assert result == '/workspace'

    def test_workspace_mount_with_different_permissions(self):
        """Test /workspace mount with different permission strings."""
        with patch('openhands.agenthub.codeact_agent.tools.str_replace_editor._is_running_in_container', return_value=False):
            test_cases = [
                '/host/app:/workspace:ro',
                '/host/app:/workspace:rw',
                '/host/app:/workspace',  # No permissions
                '/host/app:/workspace:rw,size=100m',  # Extra options
            ]
            
            for sandbox_volumes in test_cases:
                with patch.dict(os.environ, {'SANDBOX_VOLUMES': sandbox_volumes}):
                    result = _get_workspace_mount_path_from_env()
                    assert result == '/host/app', f"Failed for: {sandbox_volumes}"