import asyncio
import os
import shutil
import subprocess

import pytest

from opendevin.controller.agent import Agent
from opendevin.controller.state.state import State
from opendevin.core.config import parse_arguments
from opendevin.core.main import run_agent_controller
from opendevin.core.schema import AgentState
from opendevin.events.action import (
    AgentFinishAction,
    AgentRejectAction,
)
from opendevin.events.observation.browse import BrowserOutputObservation
from opendevin.events.observation.delegate import AgentDelegateObservation
from opendevin.llm.llm import LLM

workspace_base = os.getenv('WORKSPACE_BASE')
workspace_mount_path = os.getenv('WORKSPACE_MOUNT_PATH')
workspace_mount_path_in_sandbox = os.getenv('WORKSPACE_MOUNT_PATH_IN_SANDBOX')

print('\nPaths used:')
print(f'workspace_base: {workspace_base}')
print(f'workspace_mount_path: {workspace_mount_path}')
print(f'workspace_mount_path_in_sandbox: {workspace_mount_path_in_sandbox}')


@pytest.mark.skipif(
    os.getenv('AGENT') == 'BrowsingAgent',
    reason='BrowsingAgent is a specialized agent',
)
@pytest.mark.skipif(
    (os.getenv('AGENT') == 'CodeActAgent' or os.getenv('AGENT') == 'CodeActSWEAgent')
    and os.getenv('SANDBOX_BOX_TYPE', '').lower() != 'ssh',
    reason='CodeActAgent/CodeActSWEAgent only supports ssh sandbox which is stateful',
)
@pytest.mark.skipif(
    os.getenv('AGENT') == 'ManagerAgent',
    reason='Manager agent is not capable of finishing this in reasonable steps yet',
)
def test_write_simple_script():
    task = "Write a shell script 'hello.sh' that prints 'hello'. Do not ask me for confirmation at any point."
    args = parse_arguments()

    # Create the agent
    agent = Agent.get_cls(args.agent_cls)(llm=LLM(args.model_name))

    final_state: State | None = asyncio.run(
        run_agent_controller(agent, task, exit_on_message=True)
    )
    assert final_state.agent_state == AgentState.STOPPED
    assert final_state.last_error is None

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
    (os.getenv('AGENT') == 'CodeActAgent' or os.getenv('AGENT') == 'CodeActSWEAgent')
    and os.getenv('SANDBOX_BOX_TYPE', '').lower() != 'ssh',
    reason='CodeActAgent/CodeActSWEAgent only supports ssh sandbox which is stateful',
)
@pytest.mark.skipif(
    os.getenv('AGENT') == 'MonologueAgent' or os.getenv('AGENT') == 'PlannerAgent',
    reason='We only keep basic tests for MonologueAgent and PlannerAgent',
)
@pytest.mark.skipif(
    os.getenv('SANDBOX_BOX_TYPE') == 'local',
    reason='local sandbox shows environment-dependent absolute path for pwd command',
)
def test_edits():
    args = parse_arguments()
    # Copy workspace artifacts to workspace_base location
    source_dir = os.path.join(os.path.dirname(__file__), 'workspace/test_edits/')
    files = os.listdir(source_dir)
    for file in files:
        dest_file = os.path.join(workspace_base, file)
        if os.path.exists(dest_file):
            os.remove(dest_file)
        shutil.copy(os.path.join(source_dir, file), dest_file)

    # Create the agent
    agent = Agent.get_cls(args.agent_cls)(llm=LLM(args.model_name))

    # Execute the task
    task = 'Fix typos in bad.txt. Do not ask me for confirmation at any point.'
    final_state: State | None = asyncio.run(
        run_agent_controller(agent, task, exit_on_message=True)
    )
    assert final_state.agent_state == AgentState.STOPPED
    assert final_state.last_error is None

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
    os.getenv('AGENT') != 'CodeActAgent' and os.getenv('AGENT') != 'CodeActSWEAgent',
    reason='currently only CodeActAgent and CodeActSWEAgent have IPython (Jupyter) execution by default',
)
@pytest.mark.skipif(
    os.getenv('SANDBOX_BOX_TYPE') != 'ssh',
    reason='Currently, only ssh sandbox supports stateful tasks',
)
def test_ipython():
    args = parse_arguments()

    # Create the agent
    agent = Agent.get_cls(args.agent_cls)(llm=LLM(args.model_name))

    # Execute the task
    task = "Use Jupyter IPython to write a text file containing 'hello world' to '/workspace/test.txt'. Do not ask me for confirmation at any point."
    final_state: State | None = asyncio.run(
        run_agent_controller(agent, task, exit_on_message=True)
    )
    assert final_state.agent_state == AgentState.STOPPED
    assert final_state.last_error is None

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
    os.getenv('AGENT') != 'ManagerAgent',
    reason='Currently, only ManagerAgent supports task rejection',
)
@pytest.mark.skipif(
    os.getenv('SANDBOX_BOX_TYPE') == 'local',
    reason='FIXME: local sandbox does not capture stderr',
)
def test_simple_task_rejection():
    args = parse_arguments()

    # Create the agent
    agent = Agent.get_cls(args.agent_cls)(llm=LLM(args.model_name))

    # Give an impossible task to do: cannot write a commit message because
    # the workspace is not a git repo
    task = 'Write a git commit message for the current staging area. Do not ask me for confirmation at any point.'
    final_state: State | None = asyncio.run(run_agent_controller(agent, task))
    assert final_state.agent_state == AgentState.STOPPED
    assert final_state.last_error is None
    assert isinstance(final_state.history.get_last_action(), AgentRejectAction)


@pytest.mark.skipif(
    os.getenv('AGENT') != 'CodeActAgent' and os.getenv('AGENT') != 'CodeActSWEAgent',
    reason='currently only CodeActAgent and CodeActSWEAgent have IPython (Jupyter) execution by default',
)
@pytest.mark.skipif(
    os.getenv('SANDBOX_BOX_TYPE') != 'ssh',
    reason='Currently, only ssh sandbox supports stateful tasks',
)
def test_ipython_module():
    args = parse_arguments()

    # Create the agent
    agent = Agent.get_cls(args.agent_cls)(llm=LLM(args.model_name))

    # Execute the task
    task = "Install and import pymsgbox==1.0.9 and print it's version in /workspace/test.txt. Do not ask me for confirmation at any point."
    final_state: State | None = asyncio.run(
        run_agent_controller(agent, task, exit_on_message=True)
    )
    assert final_state.agent_state == AgentState.STOPPED
    assert final_state.last_error is None

    # Verify the file exists
    file_path = os.path.join(workspace_base, 'test.txt')
    assert os.path.exists(file_path), 'The file "test.txt" does not exist'

    # Verify the file contains the expected content
    with open(file_path, 'r') as f:
        content = f.read()
        print(content)
    assert (
        content.strip().split(' ')[-1] == '1.0.9'
    ), f'Expected content "1.0.9", but got "{content.strip()}"'


@pytest.mark.skipif(
    os.getenv('AGENT') != 'BrowsingAgent' and os.getenv('AGENT') != 'CodeActAgent',
    reason='currently only BrowsingAgent and CodeActAgent are capable of searching the internet',
)
@pytest.mark.skipif(
    (os.getenv('AGENT') == 'CodeActAgent' or os.getenv('AGENT') == 'CodeActSWEAgent')
    and os.getenv('SANDBOX_BOX_TYPE', '').lower() != 'ssh',
    reason='CodeActAgent/CodeActSWEAgent only supports ssh sandbox which is stateful',
)
def test_browse_internet(http_server):
    args = parse_arguments()

    # Create the agent
    agent = Agent.get_cls(args.agent_cls)(llm=LLM(args.model_name))

    # Execute the task
    task = 'Browse localhost:8000, and tell me the ultimate answer to life. Do not ask me for confirmation at any point.'
    final_state: State | None = asyncio.run(
        run_agent_controller(agent, task, exit_on_message=True)
    )
    assert final_state.agent_state == AgentState.STOPPED
    assert final_state.last_error is None

    # last action
    last_action = final_state.history.get_last_action()
    assert isinstance(last_action, AgentFinishAction)

    # last observation
    last_observation = final_state.history.get_last_observation()
    assert isinstance(
        last_observation, (BrowserOutputObservation, AgentDelegateObservation)
    )
    if isinstance(last_observation, BrowserOutputObservation):
        assert 'OpenDevin is all you need!' in last_observation.content
    elif isinstance(last_observation, AgentDelegateObservation):
        assert 'OpenDevin is all you need!' in last_observation.outputs['content']
