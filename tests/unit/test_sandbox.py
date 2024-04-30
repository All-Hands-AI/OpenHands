import pathlib
import tempfile
from unittest.mock import patch

import pytest

from opendevin import config
from opendevin.sandbox.docker.ssh_box import DockerSSHBox
from opendevin.sandbox.docker.exec_box import DockerExecBox


@pytest.fixture
def temp_dir():
    # get a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        pathlib.Path().mkdir(parents=True, exist_ok=True)
        yield temp_dir


def test_ssh_box_run_as_devin(temp_dir):
    # get a temporary directory
    with patch.dict(
        config.config,
        {
            config.ConfigType.WORKSPACE_BASE: temp_dir,
            config.ConfigType.RUN_AS_DEVIN: 'true',
            config.ConfigType.SANDBOX_TYPE: 'ssh',
        },
        clear=True
    ):
        for box in [DockerSSHBox(), DockerExecBox()]:

            # test the ssh box
            exit_code, output = box.execute('ls -l')
            assert exit_code == 0, 'The exit code should be 0 for ' + box.__class__.__name__
            assert output.strip() == 'total 0'

            exit_code, output = box.execute('mkdir test')
            assert exit_code == 0, 'The exit code should be 0 for ' + box.__class__.__name__
            assert output.strip() == ''

            exit_code, output = box.execute('ls -l')
            assert exit_code == 0, 'The exit code should be 0.'
            assert 'opendevin' in output, "The output should contain username 'opendevin' for " + box.__class__.__name__
            assert 'test' in output, 'The output should contain the test directory for ' + box.__class__.__name__

            exit_code, output = box.execute('touch test/foo.txt')
            assert exit_code == 0, 'The exit code should be 0. for ' + box.__class__.__name__
            assert output.strip() == ''

            exit_code, output = box.execute('ls -l test')
            assert exit_code == 0, 'The exit code should be 0. for ' + box.__class__.__name__
            assert 'foo.txt' in output, 'The output should contain the foo.txt file for ' + box.__class__.__name__


def test_ssh_box_multi_line_cmd_run_as_devin(temp_dir):
    # get a temporary directory
    with patch.dict(
        config.config,
        {
            config.ConfigType.WORKSPACE_BASE: temp_dir,
            config.ConfigType.RUN_AS_DEVIN: 'true',
            config.ConfigType.SANDBOX_TYPE: 'ssh',
        },
        clear=True
    ):
        ssh_box = DockerSSHBox()

        # test the ssh box
        exit_code, output = ssh_box.execute('pwd\nls -l')
        assert exit_code == 0, 'The exit code should be 0.'
        expected_lines = ['/workspacels -l', 'total 0']
        assert output == '\r\n'.join(expected_lines)

def test_ssh_box_stateful_cmd_run_as_devin(temp_dir):
    # get a temporary directory
    with patch.dict(
        config.config,
        {
            config.ConfigType.WORKSPACE_BASE: temp_dir,
            config.ConfigType.RUN_AS_DEVIN: 'true',
            config.ConfigType.SANDBOX_TYPE: 'ssh',
        },
        clear=True
    ):
        ssh_box = DockerSSHBox()

        # test the ssh box
        exit_code, output = ssh_box.execute('mkdir test')
        assert exit_code == 0, 'The exit code should be 0.'
        assert output.strip() == ''

        exit_code, output = ssh_box.execute('cd test')
        assert exit_code == 0, 'The exit code should be 0.'
        assert output.strip() == ''

        exit_code, output = ssh_box.execute('pwd')
        assert exit_code == 0, 'The exit code should be 0.'
        assert output.strip() == '/workspace/test'

def test_ssh_box_failed_cmd_run_as_devin(temp_dir):
    # get a temporary directory
    with patch.dict(
        config.config,
        {
            config.ConfigType.WORKSPACE_BASE: temp_dir,
            config.ConfigType.RUN_AS_DEVIN: 'true',
            config.ConfigType.SANDBOX_TYPE: 'ssh',
        },
        clear=True
    ):
        ssh_box = DockerSSHBox()

        # test the ssh box with a command that fails
        exit_code, output = ssh_box.execute('non_existing_command')
        assert exit_code != 0, 'The exit code should not be 0 for a failed command.'


def test_sandbox_whitespace(temp_dir):
    # get a temporary directory
    with patch.dict(
        config.config,
        {
            config.ConfigType.WORKSPACE_BASE: temp_dir,
            config.ConfigType.RUN_AS_DEVIN: 'true',
            config.ConfigType.SANDBOX_TYPE: 'ssh',
        },
        clear=True
    ):
        for box in [DockerSSHBox(), DockerExecBox()]:

            # test the ssh box
            exit_code, output = box.execute('echo -e "\n\n\n"')
            assert exit_code == 0, 'The exit code should be 0 for ' + box.__class__.__name__
            if isinstance(box, DockerExecBox):
                assert output == '\n\n\n', 'The output should be the same as the input for ' + box.__class__.__name__
            else:
                # FIXME: why are there extra '>' characters? Can we remove \r?
                assert output == '> \r\n> \r\n> ', 'The output should be the same as the input for ' + box.__class__.__name__
