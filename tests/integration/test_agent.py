import asyncio
import os
import shutil
import subprocess

import pytest

from opendevin.core.main import main

workspace_base = os.getenv('WORKSPACE_BASE')


@pytest.mark.skipif(
    os.getenv('AGENT') == 'CodeActAgent'
    and os.getenv('SANDBOX_TYPE').lower() == 'exec',
    reason='CodeActAgent does not support exec sandbox since exec sandbox is NOT stateful',
)
def test_write_simple_script():
    task = "Write a shell script 'hello.sh' that prints 'hello'. Do not ask me for confirmation at any point."
    controller = asyncio.run(main(task))
    asyncio.run(controller.close())

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
    controller = asyncio.run(main(task))
    asyncio.run(controller.close())

    # Verify bad.txt has been fixed
    text = """This is a stupid typo.
Really?
No more typos!
Enjoy!
"""
    with open(os.path.join(workspace_base, 'bad.txt'), 'r') as f:
        content = f.read()
    assert content.strip() == text.strip()
