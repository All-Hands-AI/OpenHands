import pathlib
import tempfile

import pytest

from opendevin.core.config import AppConfig, SandboxConfig
from opendevin.runtime.docker.ssh_box import DockerSSHBox
from opendevin.runtime.plugins import JupyterRequirement


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
