import asyncio
import os
import pathlib
import tempfile
from unittest.mock import Mock, patch

import pytest

from opendevin.events.action import CmdRunAction
from opendevin.events.observation import CmdOutputObservation
from opendevin.runtime.client.client import RuntimeClient


@pytest.fixture
def temp_dir(monkeypatch):
    # get a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        pathlib.Path().mkdir(parents=True, exist_ok=True)
        yield temp_dir


async def _load_runtime():
    runtime = RuntimeClient(
        plugins_to_load=[],
        work_dir=temp_dir,
    )
    return runtime


@pytest.mark.asyncio
async def test_prompt_detection(temp_dir):
    runtime = await _load_runtime()
    runtime.capture_full_session_output()  # Capture session output before command execution
    output, exit_code = runtime._execute_bash("echo 'Hello, World!'")
    runtime.capture_full_session_output()  # Capture session output after command execution
    assert exit_code == 0, 'The exit code should be 0.'


@pytest.mark.asyncio
async def test_get_bash_prompt(temp_dir):
    runtime = await _load_runtime()
    prompt = runtime._get_bash_prompt()
    expected_prompt = (
        f'[PEXPECT_BEGIN_{runtime.prompt_uuid}] $ [PEXPECT_END_{runtime.prompt_uuid}]'
    )
    assert prompt == expected_prompt, "The prompt should include the runtime's UUID."
    runtime.close()


@pytest.mark.asyncio
async def test_execute_bash_interactive_prompt(temp_dir):
    runtime = await _load_runtime()
    mock_shell = Mock()
    mock_shell.expect.side_effect = [1, 0, 0]
    # Update the mock_shell.before to simulate the command output without the exit code
    mock_shell.before = 'Do you want to continue? [y/N] '
    # Extend the side_effect list to cover all sendline calls
    mock_shell.sendline.side_effect = [None, 'n', None, 'echo $?']
    # Update the mock_shell.after to return a string that includes the PEXPECT markers
    prompt_uuid = runtime.prompt_uuid
    mock_shell.after = f'[PEXPECT_BEGIN_{prompt_uuid}] $ [PEXPECT_END_{prompt_uuid}]'
    runtime.shell = mock_shell
    output, exit_code = runtime._execute_bash('pip install package')
    assert "(Automatically responded 'n' to prompt)" in output
    # Update the assertion to expect a non-zero exit code
    assert exit_code != 0
    # Ensure sendline is called with 'echo $?'
    runtime.shell.sendline.assert_called_with('echo $?')
    runtime.close()


@pytest.mark.asyncio
async def test_virtual_env_activation(temp_dir):
    runtime = await _load_runtime()
    mock_shell = Mock()
    mock_shell.expect.side_effect = [0, 0, 0]
    mock_shell.before = ''
    mock_shell.after = f'[PEXPECT_BEGIN_{runtime.prompt_uuid}] (venv) user@host:/tmp$ [PEXPECT_END_{runtime.prompt_uuid}]'
    runtime.shell = mock_shell
    output, exit_code = await asyncio.to_thread(
        runtime._execute_bash, 'source venv/bin/activate'
    )
    assert '(venv) user@host:/tmp$' in output
    runtime.close()


@pytest.mark.asyncio
async def test_env_vars_os_environ(temp_dir):
    with patch.dict(os.environ, {'SANDBOX_ENV_FOOBAR': 'BAZ'}):
        runtime = await _load_runtime()
        # print(f"Environment Variables: {os.environ}")
        obs: CmdOutputObservation = await runtime.run_action(
            CmdRunAction(command='export FOOBAR=$SANDBOX_ENV_FOOBAR && echo $FOOBAR')
        )
        # Add debug logging
        # print(f"Command Output: {obs.content.strip()}")
        assert isinstance(obs, CmdOutputObservation)
        assert obs.exit_code == 0, 'The exit code should be 0.'
        assert 'BAZ' in obs.content.strip(), f'Output: [{obs.content}]'
        runtime.close()


# @pytest.mark.asyncio
# async def test_execute_bash_timeout(temp_dir):
#     runtime = await _load_runtime()
#     with patch.object(runtime.shell, 'expect', new_callable=AsyncMock) as mock_expect:
#         mock_expect.side_effect = asyncio.TimeoutError
#         await runtime._execute_bash('long_running_command', timeout=1)
#     runtime.close()
