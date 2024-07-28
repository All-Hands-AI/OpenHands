import os
import pathlib
import tempfile

import pytest

from opendevin.core.config import AppConfig, SandboxConfig
from opendevin.runtime.docker.ssh_box import DockerSSHBox
from opendevin.runtime.plugins import AgentSkillsRequirement, JupyterRequirement


def create_docker_box_from_app_config(
    path: str, config: AppConfig | None = None
) -> DockerSSHBox:
    if config is None:
        config = AppConfig(
            sandbox=SandboxConfig(
                box_type='ssh',
            ),
            persist_sandbox=False,
        )
    return DockerSSHBox(
        config=config.sandbox,
        persist_sandbox=config.persist_sandbox,
        workspace_mount_path=path,
        sandbox_workspace_dir=config.workspace_mount_path_in_sandbox,
        cache_dir=config.cache_dir,
        run_as_devin=True,
        ssh_hostname=config.ssh_hostname,
        ssh_password=config.ssh_password,
        ssh_port=config.ssh_port,
    )


@pytest.fixture
def temp_dir(monkeypatch):
    # get a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        pathlib.Path().mkdir(parents=True, exist_ok=True)
        yield temp_dir


def test_ssh_box_run_as_devin(temp_dir):
    # get a temporary directory
    for box in [
        create_docker_box_from_app_config(temp_dir),
    ]:  # FIXME: permission error on mkdir test for exec box
        exit_code, output = box.execute('ls -l')
        assert exit_code == 0, 'The exit code should be 0 for ' + box.__class__.__name__
        assert output.strip() == 'total 0'

        assert box.workspace_mount_path == temp_dir
        exit_code, output = box.execute('ls -l')
        assert exit_code == 0, 'The exit code should be 0.'
        assert output.strip() == 'total 0'

        exit_code, output = box.execute('mkdir test')
        assert exit_code == 0, 'The exit code should be 0.'
        assert output.strip() == ''

        exit_code, output = box.execute('ls -l')
        assert exit_code == 0, 'The exit code should be 0.'
        assert 'opendevin' in output, "The output should contain username 'opendevin'"
        assert 'test' in output, 'The output should contain the test directory'

        exit_code, output = box.execute('touch test/foo.txt')
        assert exit_code == 0, 'The exit code should be 0.'
        assert output.strip() == ''

        exit_code, output = box.execute('ls -l test')
        assert exit_code == 0, 'The exit code should be 0.'
        assert 'foo.txt' in output, 'The output should contain the foo.txt file'
        box.close()


def test_ssh_box_multi_line_cmd_run_as_devin(temp_dir):
    box = create_docker_box_from_app_config(temp_dir)
    exit_code, output = box.execute('pwd && ls -l')
    assert exit_code == 0, 'The exit code should be 0 for ' + box.__class__.__name__
    expected_lines = ['/workspace', 'total 0']
    line_sep = '\r\n' if isinstance(box, DockerSSHBox) else '\n'
    assert output == line_sep.join(expected_lines), (
        'The output should be the same as the input for ' + box.__class__.__name__
    )
    box.close()


def test_ssh_box_stateful_cmd_run_as_devin(temp_dir):
    box = create_docker_box_from_app_config(temp_dir)
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
    box = create_docker_box_from_app_config(temp_dir)
    exit_code, output = box.execute('non_existing_command')
    assert exit_code != 0, (
        'The exit code should not be 0 for a failed command for '
        + box.__class__.__name__
    )
    box.close()


def test_single_multiline_command(temp_dir):
    box = create_docker_box_from_app_config(temp_dir)
    exit_code, output = box.execute('echo \\\n -e "foo"')
    assert exit_code == 0, 'The exit code should be 0 for ' + box.__class__.__name__
    # FIXME: why is there a `>` in the output? Probably PS2?
    assert output == '> foo', (
        'The output should be the same as the input for ' + box.__class__.__name__
    )
    box.close()


def test_multiline_echo(temp_dir):
    box = create_docker_box_from_app_config(temp_dir)
    exit_code, output = box.execute('echo -e "hello\nworld"')
    assert exit_code == 0, 'The exit code should be 0 for ' + box.__class__.__name__
    # FIXME: why is there a `>` in the output?
    assert output == '> hello\r\nworld', (
        'The output should be the same as the input for ' + box.__class__.__name__
    )
    box.close()


def test_sandbox_whitespace(temp_dir):
    box = create_docker_box_from_app_config(temp_dir)
    exit_code, output = box.execute('echo -e "\\n\\n\\n"')
    assert exit_code == 0, 'The exit code should be 0 for ' + box.__class__.__name__
    assert output == '\r\n\r\n\r\n', (
        'The output should be the same as the input for ' + box.__class__.__name__
    )
    box.close()


def test_sandbox_jupyter_plugin(temp_dir):
    box = create_docker_box_from_app_config(temp_dir)
    box.init_plugins([JupyterRequirement])
    exit_code, output = box.execute('echo "print(1)" | execute_cli')
    print(output)
    assert exit_code == 0, 'The exit code should be 0 for ' + box.__class__.__name__
    assert output == '1\r\n', (
        'The output should be the same as the input for ' + box.__class__.__name__
    )
    box.close()


def _test_sandbox_jupyter_agentskills_fileop_pwd_impl(box, config: AppConfig):
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

    if config.sandbox.enable_auto_lint:
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
/workspace/test/hello.py:1:3: E999 IndentationError: unexpected indent
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
    config = AppConfig(
        sandbox=SandboxConfig(
            box_type='ssh',
            enable_auto_lint=False,
        ),
        persist_sandbox=False,
    )
    assert not config.sandbox.enable_auto_lint
    box = create_docker_box_from_app_config(temp_dir, config)
    _test_sandbox_jupyter_agentskills_fileop_pwd_impl(box, config)


@pytest.mark.skipif(
    os.getenv('TEST_IN_CI') != 'true',
    reason='The unittest need to download image, so only run on CI',
)
def test_agnostic_sandbox_jupyter_agentskills_fileop_pwd(temp_dir):
    for base_sandbox_image in ['ubuntu:22.04', 'debian:11']:
        config = AppConfig(
            sandbox=SandboxConfig(
                box_type='ssh',
                container_image=base_sandbox_image,
                enable_auto_lint=False,
            ),
            persist_sandbox=False,
        )
        assert not config.sandbox.enable_auto_lint
        box = create_docker_box_from_app_config(temp_dir, config)
        _test_sandbox_jupyter_agentskills_fileop_pwd_impl(box, config)


def test_sandbox_jupyter_plugin_backticks(temp_dir):
    config = AppConfig(
        sandbox=SandboxConfig(
            box_type='ssh',
        ),
        persist_sandbox=False,
    )
    box = DockerSSHBox(
        config=config.sandbox,
        persist_sandbox=config.persist_sandbox,
        workspace_mount_path=temp_dir,
        sandbox_workspace_dir=config.workspace_mount_path_in_sandbox,
        cache_dir=config.cache_dir,
        run_as_devin=True,
        ssh_hostname=config.ssh_hostname,
        ssh_password=config.ssh_password,
        ssh_port=config.ssh_port,
    )
    box.init_plugins([JupyterRequirement])
    test_code = "print('Hello, `World`!')"
    expected_write_command = (
        "cat > /tmp/opendevin_jupyter_temp.py <<'EOL'\n" f'{test_code}\n' 'EOL'
    )
    expected_execute_command = 'cat /tmp/opendevin_jupyter_temp.py | execute_cli'
    exit_code, output = box.execute(expected_write_command)
    exit_code, output = box.execute(expected_execute_command)
    print(output)
    assert exit_code == 0, 'The exit code should be 0 for ' + box.__class__.__name__
    assert output.strip() == 'Hello, `World`!', (
        'The output should be the same as the input for ' + box.__class__.__name__
    )
    box.close()
