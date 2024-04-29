import os
import pytest
import pathlib
import tempfile

@pytest.fixture
def ssh_box():
    # get a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        pathlib.Path().mkdir(parents=True, exist_ok=True)
        os.environ['WORKSPACE_BASE'] = temp_dir
        os.environ['RUN_AS_DEVIN'] = 'true'
        os.environ['SANDBOX_TYPE'] = 'ssh'
        from opendevin.sandbox.docker.ssh_box import DockerSSHBox
        ssh_box = DockerSSHBox()
        yield ssh_box

    # cleanup the environment variables
    del os.environ['WORKSPACE_BASE']
    del os.environ['SANDBOX_TYPE']


def test_ssh_box_run_as_devin(ssh_box):
    # test the ssh box
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


def test_ssh_box_multi_line_cmd_run_as_devin(ssh_box):
    # test the ssh box
    exit_code, output = ssh_box.execute('pwd\nls -l')
    assert exit_code == 0, 'The exit code should be 0.'
    expected_lines = ['/workspacels -l', 'total 0']
    assert output.strip().splitlines() == expected_lines

def test_ssh_box_stateful_cmd_run_as_devin(ssh_box):
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

def test_ssh_box_failed_cmd_run_as_devin(ssh_box):
    # test the ssh box with a command that fails
    exit_code, output = ssh_box.execute('non_existing_command')
    assert exit_code != 0, 'The exit code should not be 0 for a failed command.'
