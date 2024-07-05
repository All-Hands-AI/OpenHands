import pathlib
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from opendevin.core.config import config
from opendevin.core.schema import CancellableStream
from opendevin.runtime.docker.exec_box import DockerExecBox
from opendevin.runtime.docker.local_box import LocalBox
from opendevin.runtime.docker.ssh_box import DockerSSHBox


@pytest.fixture
def temp_dir(monkeypatch):
    # get a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        pathlib.Path().mkdir(parents=True, exist_ok=True)
        yield temp_dir


@pytest.fixture
def mock_ssh():
    mock = MagicMock()
    mock.read_nonblocking.side_effect = [b'output1\n', b'output2\n', Exception('EOF')]
    return mock


def test_streaming_execution(temp_dir, mock_ssh):
    with patch.object(config, 'workspace_base', new=temp_dir), patch.object(
        config, 'workspace_mount_path', new=temp_dir
    ), patch.object(config, 'run_as_devin', new='true'), patch.object(
        config, 'sandbox_type', new='ssh'
    ), patch('opendevin.runtime.docker.ssh_box.pxssh.pxssh', return_value=mock_ssh):
        box = DockerSSHBox()
        exit_code, output = box.execute('echo "Hello, World!"', stream=True)

        assert exit_code == 0, 'The exit code should be 0.'
        assert isinstance(
            output, CancellableStream
        ), 'Output should be a CancellableStream'

        streamed_output = ''.join(output)
        assert (
            'output1\noutput2\n' in streamed_output
        ), 'Streamed output should contain expected content'

        box.close()


def test_streaming_execution_with_error(temp_dir, mock_ssh):
    mock_ssh.read_nonblocking.side_effect = [b'error output\n', Exception('EOF')]
    mock_ssh.before = b'error output\n'
    mock_ssh.exitstatus = 1

    with patch.object(config, 'workspace_base', new=temp_dir), patch.object(
        config, 'workspace_mount_path', new=temp_dir
    ), patch.object(config, 'run_as_devin', new='true'), patch.object(
        config, 'sandbox_type', new='ssh'
    ), patch('opendevin.runtime.docker.ssh_box.pxssh.pxssh', return_value=mock_ssh):
        box = DockerSSHBox()
        exit_code, output = box.execute('non_existing_command', stream=True)

        assert exit_code != 0, 'The exit code should not be 0 for a failed command.'
        assert isinstance(
            output, CancellableStream
        ), 'Output should be a CancellableStream'

        streamed_output = ''.join(output)
        assert (
            'error output\n' in streamed_output
        ), 'Streamed output should contain error message'

        box.close()


def test_streaming_execution_timeout(temp_dir, mock_ssh):
    mock_ssh.read_nonblocking.side_effect = [b'partial output\n', Exception('TIMEOUT')]

    with patch.object(config, 'workspace_base', new=temp_dir), patch.object(
        config, 'workspace_mount_path', new=temp_dir
    ), patch.object(config, 'run_as_devin', new='true'), patch.object(
        config, 'sandbox_type', new='ssh'
    ), patch('opendevin.runtime.docker.ssh_box.pxssh.pxssh', return_value=mock_ssh):
        box = DockerSSHBox()
        exit_code, output = box.execute('sleep 10', stream=True, timeout=1)

        assert isinstance(
            output, CancellableStream
        ), 'Output should be a CancellableStream'

        streamed_output = ''.join(output)
        assert (
            'partial output\n' in streamed_output
        ), 'Streamed output should contain partial output'

        box.close()


@pytest.mark.parametrize('box_class', [DockerSSHBox, DockerExecBox, LocalBox])
def test_streaming_execution_across_boxes(temp_dir, box_class):
    with patch.object(config, 'workspace_base', new=temp_dir), patch.object(
        config, 'workspace_mount_path', new=temp_dir
    ), patch.object(config, 'run_as_devin', new='true'), patch.object(
        config, 'sandbox_type', new='ssh'
    ):
        box = box_class()
        exit_code, output = box.execute(
            'for i in {1..5}; do echo $i; sleep 0.1; done', stream=True
        )

        assert exit_code == 0, f'The exit code should be 0 for {box_class.__name__}.'
        assert isinstance(
            output, CancellableStream
        ), f'Output should be a CancellableStream for {box_class.__name__}'

        streamed_output = ''.join(output)
        expected_output = '1\n2\n3\n4\n5\n'
        assert (
            expected_output in streamed_output
        ), f'Streamed output should contain expected content for {box_class.__name__}'

        box.close()


def test_streaming_execution_cancellation(temp_dir, mock_ssh):
    mock_ssh.read_nonblocking.side_effect = [
        b'output1\n',
        b'output2\n',
        Exception('EOF'),
    ]

    with patch.object(config, 'workspace_base', new=temp_dir), patch.object(
        config, 'workspace_mount_path', new=temp_dir
    ), patch.object(config, 'run_as_devin', new='true'), patch.object(
        config, 'sandbox_type', new='ssh'
    ), patch('opendevin.runtime.docker.ssh_box.pxssh.pxssh', return_value=mock_ssh):
        box = DockerSSHBox()
        exit_code, output = box.execute('long_running_command', stream=True)

        assert isinstance(
            output, CancellableStream
        ), 'Output should be a CancellableStream'

        # Read part of the output
        partial_output = next(output)
        assert 'output1\n' in partial_output, 'First part of output should be received'

        # Cancel the stream
        output.close()

        # Attempt to read more should not yield any results
        with pytest.raises(StopIteration):
            next(output)

        box.close()


def test_streaming_execution_large_output(temp_dir):
    large_output = 'x' * 1024 * 1024  # 1 MB of data

    with patch.object(config, 'workspace_base', new=temp_dir), patch.object(
        config, 'workspace_mount_path', new=temp_dir
    ), patch.object(config, 'run_as_devin', new='true'), patch.object(
        config, 'sandbox_type', new='ssh'
    ):
        box = DockerSSHBox()
        exit_code, output = box.execute(f'echo "{large_output}"', stream=True)

        assert exit_code == 0, 'The exit code should be 0.'
        assert isinstance(
            output, CancellableStream
        ), 'Output should be a CancellableStream'

        streamed_output = ''.join(output)
        assert len(streamed_output) >= len(
            large_output
        ), 'All output should be streamed'

        box.close()


if __name__ == '__main__':
    pytest.main([__file__])
