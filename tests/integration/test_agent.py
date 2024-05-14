import asyncio
import os
import shutil
import subprocess

import pytest

from opendevin.core.main import main
from opendevin.core.schema import AgentState

workspace_base = os.getenv('WORKSPACE_BASE')


@pytest.mark.skipif(
    os.getenv('AGENT') == 'CodeActAgent'
    and os.getenv('SANDBOX_TYPE').lower() == 'exec',
    reason='CodeActAgent does not support exec sandbox since exec sandbox is NOT stateful',
)
def test_write_simple_script():
    task = "Write a shell script 'hello.sh' that prints 'hello'. Do not ask me for confirmation at any point."
    final_agent_state = asyncio.run(main(task, exit_on_message=True))
    assert final_agent_state == AgentState.FINISHED

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
    os.getenv('AGENT') == 'CodeActAgent'
    and os.getenv('SANDBOX_TYPE').lower() == 'exec',
    reason='CodeActAgent does not support exec sandbox since exec sandbox is NOT stateful',
)
@pytest.mark.skipif(
    os.getenv('AGENT') == 'SWEAgent',
    reason='SWEAgent is not capable of this task right now',
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
    final_agent_state = asyncio.run(main(task, exit_on_message=True))
    assert final_agent_state == AgentState.FINISHED

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
    final_agent_state = asyncio.run(main(task, exit_on_message=True))
    assert final_agent_state == AgentState.FINISHED

    # Verify the file exists
    file_path = os.path.join(workspace_base, 'test.txt')
    assert os.path.exists(file_path), 'The file "test.txt" does not exist'

    # Verify the file contains the expected content
    with open(file_path, 'r') as f:
        content = f.read()
    assert (
        content.strip() == 'hello world'
    ), f'Expected content "hello world", but got "{content.strip()}"'
