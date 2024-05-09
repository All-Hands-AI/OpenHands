import os
import pathlib
import tempfile
from unittest.mock import patch

import pytest

from opendevin.core.config import AppConfig, config
from opendevin.runtime.docker.exec_box import DockerExecBox
from opendevin.runtime.docker.local_box import LocalBox
from opendevin.runtime.docker.ssh_box import DockerSSHBox


@pytest.fixture
def temp_dir(monkeypatch):
    # get a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        pathlib.Path().mkdir(parents=True, exist_ok=True)
        yield temp_dir

    # make sure os.environ is clean
    monkeypatch.delenv('RUN_AS_DEVIN', raising=False)
    monkeypatch.delenv('SANDBOX_TYPE', raising=False)
    monkeypatch.delenv('WORKSPACE_BASE', raising=False)

    # make sure config is clean
    AppConfig.reset()


def test_env_vars(temp_dir):
    os.environ['SANDBOX_ENV_FOOBAR'] = 'BAZ'
    for box_class in [DockerSSHBox, DockerExecBox, LocalBox]:
        box = box_class()
        box.add_to_env('QUUX', 'abc"def')
        assert box._env['FOOBAR'] == 'BAZ'
        assert box._env['QUUX'] == 'abc"def'
        exit_code, output = box.execute('echo $FOOBAR $QUUX')
        assert exit_code == 0, 'The exit code should be 0.'
        assert output.strip() == 'BAZ abc"def', f'Output: {output} for {box_class}'


def test_ssh_box_run_as_devin(temp_dir):
    # get a temporary directory
    with patch.object(config, 'workspace_base', new=temp_dir), patch.object(
        config, 'workspace_mount_path', new=temp_dir
    ), patch.object(config, 'run_as_devin', new='true'), patch.object(
        config, 'sandbox_type', new='ssh'
    ):
        ssh_box = DockerSSHBox()

        # test the ssh box
        assert config.workspace_base == temp_dir
        exit_code, output = ssh_box.execute('ls -l')
        assert exit_code == 0, 'The exit code should be 0.'
        assert output.strip() == 'total 0'

        exit_code, output = ssh_box.execute('mkdir test')
        assert exit_code == 0, 'The exit code should be 0.'
        assert output.strip() == ''

        exit_code, output = ssh_box.execute('ls -l')
        assert exit_code == 0, 'The exit code should be 0.'
        assert 'opendevin' in output, "The output should contain username 'opendevin'"
        assert 'test' in output, 'The output should contain the test directory'

        exit_code, output = ssh_box.execute('touch test/foo.txt')
        assert exit_code == 0, 'The exit code should be 0.'
        assert output.strip() == ''

        exit_code, output = ssh_box.execute('ls -l test')
        assert exit_code == 0, 'The exit code should be 0.'
        assert 'foo.txt' in output, 'The output should contain the foo.txt file'


def test_ssh_box_multi_line_cmd_run_as_devin(temp_dir):
    # get a temporary directory
    with patch.object(config, 'workspace_base', new=temp_dir), patch.object(
        config, 'workspace_mount_path', new=temp_dir
    ), patch.object(config, 'run_as_devin', new='true'), patch.object(
        config, 'sandbox_type', new='ssh'
    ):
        ssh_box = DockerSSHBox()

        # test the ssh box
        exit_code, output = ssh_box.execute('pwd\nls -l')
        assert exit_code == 0, 'The exit code should be 0.'
        expected_lines = ['/workspacels -l', 'total 0']
        assert output.strip().splitlines() == expected_lines


def test_ssh_box_stateful_cmd_run_as_devin(temp_dir):
    # get a temporary directory
    with patch.object(config, 'workspace_base', new=temp_dir), patch.object(
        config, 'workspace_mount_path', new=temp_dir
    ), patch.object(config, 'run_as_devin', new='true'), patch.object(
        config, 'sandbox_type', new='ssh'
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
    with patch.object(config, 'workspace_base', new=temp_dir), patch.object(
        config, 'workspace_mount_path', new=temp_dir
    ), patch.object(config, 'run_as_devin', new='true'), patch.object(
        config, 'sandbox_type', new='ssh'
    ):
        ssh_box = DockerSSHBox()

        # test the ssh box with a command that fails
        exit_code, output = ssh_box.execute('non_existing_command')
        assert exit_code != 0, 'The exit code should not be 0 for a failed command.'
