import os
import pathlib
import tempfile
from unittest.mock import patch

import pytest

from opendevin.core.config import config
from opendevin.runtime.docker.local_box import LocalBox
from opendevin.runtime.docker.ssh_box import DockerSSHBox, split_bash_commands
from opendevin.runtime.plugins import AgentSkillsRequirement, JupyterRequirement


@pytest.fixture
def temp_dir(monkeypatch):
    # get a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        pathlib.Path().mkdir(parents=True, exist_ok=True)
        yield temp_dir


def test_env_vars(temp_dir):
    os.environ['SANDBOX_ENV_FOOBAR'] = 'BAZ'
    for box_class in [DockerSSHBox, LocalBox]:
        box = box_class()
        box.add_to_env('QUUX', 'abc"def')
        assert box._env['FOOBAR'] == 'BAZ'
        assert box._env['QUUX'] == 'abc"def'
        exit_code, output = box.execute('echo $FOOBAR $QUUX')
        assert exit_code == 0, 'The exit code should be 0.'
        assert output.strip() == 'BAZ abc"def', f'Output: {output} for {box_class}'


def test_split_commands():
    cmds = [
        'ls -l',
        'echo -e "hello\nworld"',
        """
echo -e 'hello it\\'s me'
""".strip(),
        """
echo \\
    -e 'hello' \\
    -v
""".strip(),
        """
echo -e 'hello\\nworld\\nare\\nyou\\nthere?'
""".strip(),
        """
echo -e 'hello
world
are
you\\n
there?'
""".strip(),
        """
echo -e 'hello
world "
'
""".strip(),
        """
kubectl apply -f - <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: busybox-sleep
spec:
  containers:
  - name: busybox
    image: busybox:1.28
    args:
    - sleep
    - "1000000"
EOF
""".strip(),
    ]
    joined_cmds = '\n'.join(cmds)
    split_cmds = split_bash_commands(joined_cmds)
    for s in split_cmds:
        print('\nCMD')
        print(s)
    cmds = [
        c.replace('\\\n', '') for c in cmds
    ]  # The function strips escaped newlines, but this shouldn't matter
    assert (
        split_cmds == cmds
    ), 'The split commands should be the same as the input commands.'


def test_ssh_box_run_as_devin(temp_dir):
    # get a temporary directory
    with patch.object(config, 'workspace_base', new=temp_dir), patch.object(
        config, 'workspace_mount_path', new=temp_dir
    ), patch.object(config, 'run_as_devin', new='true'), patch.object(
        config.sandbox, 'box_type', new='ssh'
    ):
        for box in [
            DockerSSHBox()
        ]:  # FIXME: permission error on mkdir test for exec box
            exit_code, output = box.execute('ls -l')
            assert exit_code == 0, (
                'The exit code should be 0 for ' + box.__class__.__name__
            )
            assert output.strip() == 'total 0'

            assert config.workspace_base == temp_dir
            exit_code, output = box.execute('ls -l')
            assert exit_code == 0, 'The exit code should be 0.'
            assert output.strip() == 'total 0'

            exit_code, output = box.execute('mkdir test')
            assert exit_code == 0, 'The exit code should be 0.'
            assert output.strip() == ''

            exit_code, output = box.execute('ls -l')
            assert exit_code == 0, 'The exit code should be 0.'
            assert (
                'opendevin' in output
            ), "The output should contain username 'opendevin'"
            assert 'test' in output, 'The output should contain the test directory'

            exit_code, output = box.execute('touch test/foo.txt')
            assert exit_code == 0, 'The exit code should be 0.'
            assert output.strip() == ''

            exit_code, output = box.execute('ls -l test')
            assert exit_code == 0, 'The exit code should be 0.'
            assert 'foo.txt' in output, 'The output should contain the foo.txt file'
            box.close()


def test_ssh_box_multi_line_cmd_run_as_devin(temp_dir):
    # get a temporary directory
    with patch.object(config, 'workspace_base', new=temp_dir), patch.object(
        config, 'workspace_mount_path', new=temp_dir
    ), patch.object(config, 'run_as_devin', new='true'), patch.object(
        config.sandbox, 'box_type', new='ssh'
    ):
        box = DockerSSHBox()
        exit_code, output = box.execute('pwd && ls -l')
        assert exit_code == 0, 'The exit code should be 0 for ' + box.__class__.__name__
        expected_lines = ['/workspace', 'total 0']
        line_sep = '\r\n' if isinstance(box, DockerSSHBox) else '\n'
        assert output == line_sep.join(expected_lines), (
            'The output should be the same as the input for ' + box.__class__.__name__
        )
        box.close()


def test_ssh_box_stateful_cmd_run_as_devin(temp_dir):
    # get a temporary directory
    with patch.object(config, 'workspace_base', new=temp_dir), patch.object(
        config, 'workspace_mount_path', new=temp_dir
    ), patch.object(config, 'run_as_devin', new='true'), patch.object(
        config.sandbox, 'box_type', new='ssh'
    ):
        box = DockerSSHBox()
        exit_code, output = box.execute('mkdir test')
        assert exit_code == 0, 'The exit code should be 0.'
        assert output.strip() == ''

        exit_code, output = box.execute('cd test')
        assert exit_code == 0, 'The exit code should be 0 for ' + box.__class__.__name__
        assert output.strip() == '', (
            'The output should be empty for ' + box.__class__.__name__
        )

        exit_code, output = box.execute('pwd')
        assert exit_code == 0, 'The exit code should be 0 for ' + box.__class__.__name__
        assert output.strip() == '/workspace/test', (
            'The output should be /workspace for ' + box.__class__.__name__
        )
        box.close()


def test_ssh_box_failed_cmd_run_as_devin(temp_dir):
    # get a temporary directory
    with patch.object(config, 'workspace_base', new=temp_dir), patch.object(
        config, 'workspace_mount_path', new=temp_dir
    ), patch.object(config, 'run_as_devin', new='true'), patch.object(
        config.sandbox, 'box_type', new='ssh'
    ):
        box = DockerSSHBox()
        exit_code, output = box.execute('non_existing_command')
        assert exit_code != 0, (
            'The exit code should not be 0 for a failed command for '
            + box.__class__.__name__
        )
        box.close()


def test_single_multiline_command(temp_dir):
    with patch.object(config, 'workspace_base', new=temp_dir), patch.object(
        config, 'workspace_mount_path', new=temp_dir
    ), patch.object(config, 'run_as_devin', new='true'), patch.object(
        config.sandbox, 'box_type', new='ssh'
    ):
        box = DockerSSHBox()
        exit_code, output = box.execute('echo \\\n -e "foo"')
        assert exit_code == 0, 'The exit code should be 0 for ' + box.__class__.__name__
        # FIXME: why is there a `>` in the output? Probably PS2?
        assert output == '> foo', (
            'The output should be the same as the input for ' + box.__class__.__name__
        )
        box.close()


def test_multiline_echo(temp_dir):
    with patch.object(config, 'workspace_base', new=temp_dir), patch.object(
        config, 'workspace_mount_path', new=temp_dir
    ), patch.object(config, 'run_as_devin', new='true'), patch.object(
        config.sandbox, 'box_type', new='ssh'
    ):
        box = DockerSSHBox()
        exit_code, output = box.execute('echo -e "hello\nworld"')
        assert exit_code == 0, 'The exit code should be 0 for ' + box.__class__.__name__
        # FIXME: why is there a `>` in the output?
        assert output == '> hello\r\nworld', (
            'The output should be the same as the input for ' + box.__class__.__name__
        )
        box.close()


def test_sandbox_whitespace(temp_dir):
    # get a temporary directory
    with patch.object(config, 'workspace_base', new=temp_dir), patch.object(
        config, 'workspace_mount_path', new=temp_dir
    ), patch.object(config, 'run_as_devin', new='true'), patch.object(
        config.sandbox, 'box_type', new='ssh'
    ):
        box = DockerSSHBox()
        exit_code, output = box.execute('echo -e "\\n\\n\\n"')
        assert exit_code == 0, 'The exit code should be 0 for ' + box.__class__.__name__
        assert output == '\r\n\r\n\r\n', (
            'The output should be the same as the input for ' + box.__class__.__name__
        )
        box.close()


def test_sandbox_jupyter_plugin(temp_dir):
    # get a temporary directory
    with patch.object(config, 'workspace_base', new=temp_dir), patch.object(
        config, 'workspace_mount_path', new=temp_dir
    ), patch.object(config, 'run_as_devin', new='true'), patch.object(
        config.sandbox, 'box_type', new='ssh'
    ):
        box = DockerSSHBox()
        box.init_plugins([JupyterRequirement])
        exit_code, output = box.execute('echo "print(1)" | execute_cli')
        print(output)
        assert exit_code == 0, 'The exit code should be 0 for ' + box.__class__.__name__
        assert output == '1\r\n', (
            'The output should be the same as the input for ' + box.__class__.__name__
        )
        box.close()


def _test_sandbox_jupyter_agentskills_fileop_pwd_impl(box):
    box.init_plugins([AgentSkillsRequirement, JupyterRequirement])
    exit_code, output = box.execute('mkdir test')
    print(output)
    assert exit_code == 0, 'The exit code should be 0 for ' + box.__class__.__name__

    exit_code, output = box.execute('echo "create_file(\'hello.py\')" | execute_cli')
    print(output)
    assert exit_code == 0, 'The exit code should be 0 for ' + box.__class__.__name__
    assert output.strip().split('\r\n') == (
        '[File: /workspace/hello.py (1 lines total)]\r\n'
        '(this is the beginning of the file)\r\n'
        '1|\r\n'
        '(this is the end of the file)\r\n'
        '[File hello.py created.]\r\n'
    ).strip().split('\r\n')

    exit_code, output = box.execute('cd test')
    print(output)
    assert exit_code == 0, 'The exit code should be 0 for ' + box.__class__.__name__

    exit_code, output = box.execute('echo "create_file(\'hello.py\')" | execute_cli')
    print(output)
    assert exit_code == 0, 'The exit code should be 0 for ' + box.__class__.__name__
    assert output.strip().split('\r\n') == (
        '[File: /workspace/test/hello.py (1 lines total)]\r\n'
        '(this is the beginning of the file)\r\n'
        '1|\r\n'
        '(this is the end of the file)\r\n'
        '[File hello.py created.]\r\n'
    ).strip().split('\r\n')

    if config.enable_auto_lint:
        # edit file, but make a mistake in indentation
        exit_code, output = box.execute(
            'echo "insert_content_at_line(\'hello.py\', 1, \'  print(\\"hello world\\")\')" | execute_cli'
        )
        print(output)
        assert exit_code == 0, 'The exit code should be 0 for ' + box.__class__.__name__
        assert output.strip().split('\r\n') == (
            """
[Your proposed edit has introduced new syntax error(s). Please understand the errors and retry your edit command.]
ERRORS:
hello.py:1:3: E999 IndentationError: unexpected indent
[This is how your edit would have looked if applied]
-------------------------------------------------
(this is the beginning of the file)
1|  print("hello world")
(this is the end of the file)
-------------------------------------------------

[This is the original code before your edit]
-------------------------------------------------
(this is the beginning of the file)
1|
(this is the end of the file)
-------------------------------------------------
Your changes have NOT been applied. Please fix your edit command and try again.
You either need to 1) Specify the correct start/end line arguments or 2) Correct your edit code.
DO NOT re-run the same failed edit command. Running it again will lead to the same error.
"""
        ).strip().split('\n')

    # edit file with correct indentation
    exit_code, output = box.execute(
        'echo "insert_content_at_line(\'hello.py\', 1, \'print(\\"hello world\\")\')" | execute_cli'
    )
    print(output)
    assert exit_code == 0, 'The exit code should be 0 for ' + box.__class__.__name__
    assert output.strip().split('\r\n') == (
        """
[File: /workspace/test/hello.py (1 lines total after edit)]
(this is the beginning of the file)
1|print("hello world")
(this is the end of the file)
[File updated (edited at line 1). Please review the changes and make sure they are correct (correct indentation, no duplicate lines, etc). Edit the file again if necessary.]
"""
    ).strip().split('\n')

    exit_code, output = box.execute('rm -rf /workspace/*')
    assert exit_code == 0, 'The exit code should be 0 for ' + box.__class__.__name__
    box.close()


def test_sandbox_jupyter_agentskills_fileop_pwd(temp_dir):
    # get a temporary directory
    with patch.object(config, 'workspace_base', new=temp_dir), patch.object(
        config, 'workspace_mount_path', new=temp_dir
    ), patch.object(config, 'run_as_devin', new='true'), patch.object(
        config.sandbox, 'box_type', new='ssh'
    ), patch.object(config, 'enable_auto_lint', new=True):
        assert config.enable_auto_lint
        box = DockerSSHBox()
        _test_sandbox_jupyter_agentskills_fileop_pwd_impl(box)


@pytest.mark.skipif(
    os.getenv('TEST_IN_CI') != 'true',
    reason='The unittest need to download image, so only run on CI',
)
def test_agnostic_sandbox_jupyter_agentskills_fileop_pwd(temp_dir):
    for base_sandbox_image in ['ubuntu:22.04', 'debian:11']:
        # get a temporary directory
        with patch.object(config, 'workspace_base', new=temp_dir), patch.object(
            config, 'workspace_mount_path', new=temp_dir
        ), patch.object(config, 'run_as_devin', new=True), patch.object(
            config.sandbox, 'box_type', new='ssh'
        ), patch.object(
            config.sandbox, 'container_image', new=base_sandbox_image
        ), patch.object(config, 'enable_auto_lint', new=False):
            assert not config.enable_auto_lint
            box = DockerSSHBox()
            _test_sandbox_jupyter_agentskills_fileop_pwd_impl(box)
