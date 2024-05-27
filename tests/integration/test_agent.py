import asyncio
import os
import shutil
import subprocess

import pytest

from opendevin.controller.state.state import State
from opendevin.core.main import main
from opendevin.core.schema import AgentState
from opendevin.events.action import (
    AgentFinishAction,
    MessageAction,
)

workspace_base = os.getenv('WORKSPACE_BASE')


@pytest.mark.skipif(
    os.getenv('AGENT') == 'BrowsingAgent',
    reason='BrowsingAgent is a specialized agent',
)
@pytest.mark.skipif(
    os.getenv('AGENT') == 'CodeActAgent' and os.getenv('SANDBOX_TYPE').lower() != 'ssh',
    reason='CodeActAgent only supports ssh sandbox which is stateful',
)
def test_write_simple_script():
    task = "Write a shell script 'hello.sh' that prints 'hello'. Do not ask me for confirmation at any point."
    final_state: State = asyncio.run(main(task, exit_on_message=True))
    assert final_state.agent_state == AgentState.STOPPED

    # Verify the script file exists
    script_path = os.path.join(workspace_base, 'hello.sh')
    assert os.path.exists(script_path), 'The file "hello.sh" does not exist'

    # Run the script and capture the output
    result = subprocess.run(['bash', script_path], capture_output=True, text=True)

    # Verify the output from the script
    assert (
        result.stdout.strip() == 'hello'
    ), f'Expected output "hello", but got "{result.stdout.strip()}"'


@pytest.mark.skipif(
    os.getenv('AGENT') == 'BrowsingAgent',
    reason='BrowsingAgent is a specialized agent',
)
@pytest.mark.skipif(
    os.getenv('AGENT') == 'CodeActAgent' and os.getenv('SANDBOX_TYPE').lower() != 'ssh',
    reason='CodeActAgent only supports ssh sandbox which is stateful',
)
@pytest.mark.skipif(
    os.getenv('AGENT') == 'MonologueAgent' or os.getenv('AGENT') == 'PlannerAgent',
    reason='We only keep basic tests for MonologueAgent and PlannerAgent',
)
@pytest.mark.skipif(
    os.getenv('SANDBOX_TYPE') == 'local',
    reason='local sandbox shows environment-dependent absolute path for pwd command',
)
def test_edits():
    # Move workspace artifacts to workspace_base location
    source_dir = os.path.join(os.path.dirname(__file__), 'workspace/test_edits/')
    files = os.listdir(source_dir)
    for file in files:
        dest_file = os.path.join(workspace_base, file)
        if os.path.exists(dest_file):
            os.remove(dest_file)
        shutil.copy(os.path.join(source_dir, file), dest_file)

    # Execute the task
    task = 'Fix typos in bad.txt. Do not ask me for confirmation at any point.'
    final_state: State = asyncio.run(main(task, exit_on_message=True))
    assert final_state.agent_state == AgentState.STOPPED

    # Verify bad.txt has been fixed
    text = """This is a stupid typo.
Really?
No more typos!
Enjoy!
"""
    with open(os.path.join(workspace_base, 'bad.txt'), 'r') as f:
        content = f.read()
    assert content.strip() == text.strip()


@pytest.mark.skipif(
    os.getenv('AGENT') != 'CodeActAgent',
    reason='currently only CodeActAgent defaults to have IPython (Jupyter) execution',
)
@pytest.mark.skipif(
    os.getenv('SANDBOX_TYPE') != 'ssh',
    reason='Currently, only ssh sandbox supports stateful tasks',
)
def test_ipython():
    # Execute the task
    task = "Use Jupyter IPython to write a text file containing 'hello world' to '/workspace/test.txt'. Do not ask me for confirmation at any point."
    final_state: State = asyncio.run(main(task, exit_on_message=True))
    assert final_state.agent_state == AgentState.STOPPED

    # Verify the file exists
    file_path = os.path.join(workspace_base, 'test.txt')
    assert os.path.exists(file_path), 'The file "test.txt" does not exist'

    # Verify the file contains the expected content
    with open(file_path, 'r') as f:
        content = f.read()
    assert (
        content.strip() == 'hello world'
    ), f'Expected content "hello world", but got "{content.strip()}"'


@pytest.mark.skipif(
    os.getenv('AGENT') != 'CodeActAgent',
    reason='currently only CodeActAgent defaults to have IPython (Jupyter) execution',
)
@pytest.mark.skipif(
    os.getenv('SANDBOX_TYPE') != 'ssh',
    reason='Currently, only ssh sandbox supports stateful tasks',
)
def test_ipython_module():
    # Execute the task
    task = "Install and import pymsgbox==1.0.9 and print it's version in /workspace/test.txt. Do not ask me for confirmation at any point."
    final_state: State = asyncio.run(main(task, exit_on_message=True))
    assert final_state.agent_state == AgentState.STOPPED

    # Verify the file exists
    file_path = os.path.join(workspace_base, 'test.txt')
    assert os.path.exists(file_path), 'The file "test.txt" does not exist'

    # Verify the file contains the expected content
    with open(file_path, 'r') as f:
        content = f.read()
    assert (
        content.strip() == '1.0.9'
    ), f'Expected content "1.0.9", but got "{content.strip()}"'


@pytest.mark.skipif(
    os.getenv('AGENT') != 'BrowsingAgent',
    reason='currently only BrowsingAgent is capable of searching the internet',
)
def test_browse_internet(http_server):
    # Execute the task
    task = 'Browse localhost:8000, and tell me the ultimate answer to life. Do not ask me for confirmation at any point.'
    final_state: State = asyncio.run(main(task, exit_on_message=True))
    assert final_state.agent_state == AgentState.STOPPED
    assert isinstance(final_state.history[-1][0], AgentFinishAction)
    assert isinstance(final_state.history[-2][0], MessageAction)
    assert 'OpenDevin is all you need!' in final_state.history[-2][0].content
