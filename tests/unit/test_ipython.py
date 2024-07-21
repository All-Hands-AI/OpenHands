import pathlib
import tempfile

import pytest

from opendevin.core.config import SandboxConfig
from opendevin.runtime.docker.ssh_box import DockerSSHBox
from opendevin.runtime.plugins import JupyterRequirement


@pytest.fixture
def temp_dir(monkeypatch):
    # get a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        pathlib.Path().mkdir(parents=True, exist_ok=True)
        yield temp_dir


@pytest.mark.asyncio
async def test_sandbox_jupyter_plugin_backticks(temp_dir):
    box = DockerSSHBox(
        config=SandboxConfig(),
        persist_sandbox=False,
        workspace_mount_path=temp_dir,
        sandbox_workspace_dir='/workspace',
        cache_dir='/tmp/cache',
        run_as_devin=True,
    )
    await box.initialize()
    await box._init_plugins_async([JupyterRequirement])
    test_code = "print('Hello, `World`!')"
    expected_write_command = (
        "cat > /tmp/opendevin_jupyter_temp.py <<'EOL'\n" f'{test_code}\n' 'EOL'
    )
    expected_execute_command = 'cat /tmp/opendevin_jupyter_temp.py | execute_cli'
    exit_code, output = await box.execute_async(expected_write_command)
    exit_code, output = await box.execute_async(expected_execute_command)
    print(output)
    assert exit_code == 0, 'The exit code should be 0 for ' + box.__class__.__name__
    assert output.strip() == 'Hello, `World`!', (
        'The output should be the same as the input for ' + box.__class__.__name__
    )
    await box.close()
