import os
import pathlib
import shutil
import tempfile
import time
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


@pytest.fixture(autouse=True)
def reset_docker_ssh_box():
    DockerSSHBox._instance = None
    yield
    if DockerSSHBox._instance:
        DockerSSHBox._instance.close()
        DockerSSHBox._instance = None
        time.sleep(1)


def test_env_vars(temp_dir):
    os.environ['SANDBOX_ENV_FOOBAR'] = 'BAZ'  # outside sandbox!
    for box_class in [DockerSSHBox, LocalBox]:
        box = box_class()
        box.initialize()
        try:
            # assert 'FOOBAR' in os.environ, 'FOOBAR not found in os.environ'
            # assert (
            #     os.environ['FOOBAR'] == 'BAZ'
            # ), f'FOOBAR in os.environ has wrong value for {box_class.__name__}'

            assert (
                'FOOBAR' in box._env
            ), f'FOOBAR not found in _env for {box_class.__name__}'
            assert (
                box._env['FOOBAR'] == 'BAZ'
            ), f'FOOBAR in _env has wrong value for {box_class.__name__}'

            box.add_to_env('QUUX', 'abc"def')

            assert (
                'QUUX' in box._env
            ), f'QUUX not found in _env for {box_class.__name__}'
            assert (
                box._env['QUUX'] == 'abc"def'
            ), f'QUUX not set correctly in _env for {box_class.__name__}'

            exit_code, output = box.execute('echo $FOOBAR $QUUX')
            assert (
                exit_code == 0
            ), f'The exit code should be 0 for {box_class.__name__}.'
            assert (
                output.strip() == 'BAZ abc"def'
            ), f'Unexpected output: {output.strip()} for {box_class.__name__}'

        finally:
            box.close()

    del os.environ['SANDBOX_ENV_FOOBAR']


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
    ), patch.object(config, 'run_as_devin', new='true'):
        for box_class in [DockerSSHBox, LocalBox]:
            # Clean up the test directory before each iteration
            test_dir = os.path.join(temp_dir, 'test')
            if os.path.exists(test_dir):
                shutil.rmtree(test_dir)

            box = box_class()
            box.initialize()
            try:
                # Ensure we're in the correct directory for both box types
                if isinstance(box, LocalBox):
                    os.chdir(config.workspace_base)
                    box._env['PWD'] = config.workspace_base

                err_suffix = f'The exit code should be 0 for {box.__class__.__name__}'
                exit_code, output = box.execute('ls -l')
                assert exit_code == 0, err_suffix
                assert (
                    output.strip() == 'total 0'
                ), f'The output should be "total 0" for {box.__class__.__name__}'

                assert config.workspace_base == temp_dir
                exit_code, output = box.execute('ls -l')
                print(output)
                assert exit_code == 0, err_suffix

                exit_code, output = box.execute('mkdir test')
                assert exit_code == 0, err_suffix
                assert output.strip() == ''

                exit_code, output = box.execute('ls -l')
                assert exit_code == 0, err_suffix
                if isinstance(box, DockerSSHBox):
                    assert (
                        'opendevin' in output
                    ), f"The output should contain username 'opendevin' for {box.__class__.__name__}"
                assert (
                    'test' in output
                ), f'The output should contain the test directory for {box.__class__.__name__}'

                exit_code, output = box.execute('touch test/foo.txt')
                assert exit_code == 0, err_suffix
                assert (
                    output.strip() == ''
                ), f'The output should be empty for {box.__class__.__name__}'

                exit_code, output = box.execute('ls -l test')
                assert exit_code == 0, err_suffix
                assert (
                    'foo.txt' in output
                ), f'The output should contain the foo.txt file for {box.__class__.__name__}'
            finally:
                box.close()


def test_ssh_box_multi_line_cmd_run_as_devin(temp_dir):
    # get a temporary directory
    with patch.object(config, 'workspace_base', new=temp_dir), patch.object(
        config, 'workspace_mount_path', new=temp_dir
    ), patch.object(config, 'run_as_devin', new='true'):
        box = DockerSSHBox()
        box.initialize()
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
    ), patch.object(config, 'run_as_devin', new='true'):
        box = DockerSSHBox()
        box.initialize()
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
    ), patch.object(config, 'run_as_devin', new='true'):
        box = DockerSSHBox()
        box.initialize()
        exit_code, output = box.execute('non_existing_command')
        assert exit_code != 0, (
            'The exit code should not be 0 for a failed command for '
            + box.__class__.__name__
        )
        box.close()


def test_single_multiline_command(temp_dir):
    with patch.object(config, 'workspace_base', new=temp_dir), patch.object(
        config, 'workspace_mount_path', new=temp_dir
    ), patch.object(config, 'run_as_devin', new='true'):
        box = DockerSSHBox()
        box.initialize()
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
    ), patch.object(config, 'run_as_devin', new='true'):
        box = DockerSSHBox()
        box.initialize()
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
    ), patch.object(config, 'run_as_devin', new='true'):
        box = DockerSSHBox()
        box.initialize()
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
    ), patch.object(config, 'run_as_devin', new='true'):
        box = DockerSSHBox()
        box.initialize()
        box.init_plugins([JupyterRequirement])
        exit_code, output = box.execute('echo "print(1)" | execute_cli')
        print(output)
        assert exit_code == 0, 'The exit code should be 0 for ' + box.__class__.__name__
        assert output == '1\r\n', (
            'The output should be the same as the input for ' + box.__class__.__name__
        )
        box.close()


async def _test_sandbox_jupyter_agentskills_fileop_pwd_impl(box):
    exit_code, output = await box.execute('mkdir test')
    print(output)
    assert exit_code == 0, 'The exit code should be 0 for ' + box.__class__.__name__

    exit_code, output = await box.execute(
        'echo "create_file(\'hello.py\')" | execute_cli'
    )
    print(output)
    assert exit_code == 0, 'The exit code should be 0 for ' + box.__class__.__name__
    assert output.strip().split('\r\n') == (
        '[File: /workspace/hello.py (1 lines total)]\r\n'
        '(this is the beginning of the file)\r\n'
        '1|\r\n'
        '(this is the end of the file)\r\n'
        '[File hello.py created.]\r\n'
    ).strip().split('\r\n')

    exit_code, output = await box.execute('cd test')
    print(output)
    assert exit_code == 0, 'The exit code should be 0 for ' + box.__class__.__name__

    exit_code, output = await box.execute(
        'echo "create_file(\'hello.py\')" | execute_cli'
    )
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
        exit_code, output = await box.execute(
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
    exit_code, output = await box.execute(
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

    exit_code, output = await box.execute('ls /workspace')
    assert exit_code == 0, 'The exit code should be 0 for ' + box.__class__.__name__
    await box.close()


@pytest.mark.skipif(True, reason='This test is outdated!')
@pytest.mark.asyncio
async def test_sandbox_jupyter_agentskills_fileop_pwd(temp_dir):
    # get a temporary directory
    with patch.object(config, 'workspace_base', new=temp_dir), patch.object(
        config, 'workspace_mount_path', new=temp_dir
    ), patch.object(config, 'run_as_devin', new='true'), patch.object(
        config, 'enable_auto_lint', new=True
    ):
        assert config.enable_auto_lint
        box = DockerSSHBox()
        await box.initialize()
        await box.init_plugins([AgentSkillsRequirement, JupyterRequirement])
        await _test_sandbox_jupyter_agentskills_fileop_pwd_impl(box)


@pytest.mark.skipif(True, reason='This test is outdated!')
@pytest.mark.asyncio
async def test_agnostic_sandbox_jupyter_agentskills_fileop_pwd(temp_dir):
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
            await box.initialize()
            await box.init_plugins([AgentSkillsRequirement, JupyterRequirement])
            await _test_sandbox_jupyter_agentskills_fileop_pwd_impl(box)
