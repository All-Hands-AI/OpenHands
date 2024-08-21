"""Test the EventStreamRuntime, which connects to the RuntimeClient running in the sandbox."""

import asyncio
import os
import time

import pytest
from pytest import TempPathFactory

from openhands.core.config import AppConfig, SandboxConfig, load_from_env
from openhands.core.logger import openhands_logger as logger
from openhands.events import EventStream
from openhands.events.action import (
    CmdRunAction,
    FileReadAction,
    FileWriteAction,
    IPythonRunCellAction,
)
from openhands.events.observation import (
    CmdOutputObservation,
    ErrorObservation,
    FileReadObservation,
    FileWriteObservation,
    IPythonRunCellObservation,
)
from openhands.runtime.client.runtime import EventStreamRuntime
from openhands.runtime.plugins import AgentSkillsRequirement, JupyterRequirement
from openhands.runtime.runtime import Runtime
from openhands.storage import get_file_store


@pytest.fixture(autouse=True)
def print_method_name(request):
    print('\n########################################################################')
    print(f'Running test: {request.node.name}')
    print('########################################################################')
    yield


@pytest.fixture
def temp_dir(tmp_path_factory: TempPathFactory) -> str:
    return str(tmp_path_factory.mktemp('test_runtime'))


TEST_RUNTIME = os.getenv('TEST_RUNTIME', 'eventstream')
PY3_FOR_TESTING = '/openhands/miniforge3/bin/mamba run -n base python3'


# Depending on TEST_RUNTIME, feed the appropriate box class(es) to the test.
def get_box_classes():
    runtime = TEST_RUNTIME
    if runtime.lower() == 'eventstream':
        return [EventStreamRuntime]
    else:
        raise ValueError(f'Invalid runtime: {runtime}')


# This assures that all tests run together per runtime, not alternating between them,
# which cause errors (especially outside GitHub actions).
@pytest.fixture(scope='module', params=get_box_classes())
def box_class(request):
    time.sleep(2)
    return request.param


# TODO: We will change this to `run_as_user` when `ServerRuntime` is deprecated.
# since `EventStreamRuntime` supports running as an arbitrary user.
@pytest.fixture(scope='module', params=[True, False])
def run_as_openhands(request):
    time.sleep(1)
    return request.param


@pytest.fixture(scope='module', params=[True, False])
def enable_auto_lint(request):
    time.sleep(1)
    return request.param


@pytest.fixture(scope='module', params=None)
def container_image(request):
    time.sleep(1)
    env_image = os.environ.get('SANDBOX_CONTAINER_IMAGE')
    if env_image:
        request.param = env_image
    else:
        if not hasattr(request, 'param'):  # prevent runtime AttributeError
            request.param = None
        if request.param is None:
            request.param = request.config.getoption('--container-image')
        if request.param is None:
            request.param = pytest.param(
                'nikolaik/python-nodejs:python3.11-nodejs22',
                'python:3.11-bookworm',
                'node:22-bookworm',
                'golang:1.23-bookworm',
            )
    print(f'Container image: {request.param}')
    return request.param


async def _load_runtime(
    temp_dir,
    box_class,
    run_as_openhands: bool = True,
    enable_auto_lint: bool = False,
    container_image: str | None = None,
    browsergym_eval_env: str | None = None,
) -> Runtime:
    sid = 'test'
    cli_session = 'main_test'
    # AgentSkills need to be initialized **before** Jupyter
    # otherwise Jupyter will not access the proper dependencies installed by AgentSkills
    plugins = [AgentSkillsRequirement(), JupyterRequirement()]
    config = AppConfig(
        workspace_base=temp_dir,
        workspace_mount_path=temp_dir,
        sandbox=SandboxConfig(
            use_host_network=True,
            browsergym_eval_env=browsergym_eval_env,
        ),
    )
    load_from_env(config, os.environ)
    config.run_as_openhands = run_as_openhands
    config.sandbox.enable_auto_lint = enable_auto_lint

    file_store = get_file_store(config.file_store, config.file_store_path)
    event_stream = EventStream(cli_session, file_store)

    if container_image is not None:
        config.sandbox.container_image = container_image

    runtime = box_class(
        config=config,
        event_stream=event_stream,
        sid=sid,
        plugins=plugins,
        container_image=container_image,
    )
    await runtime.ainit()
    await asyncio.sleep(1)
    return runtime


# ============================================================================================================================
# ipython-specific tests
# ============================================================================================================================


@pytest.mark.asyncio
async def test_simple_cmd_ipython_and_fileop(temp_dir, box_class, run_as_openhands):
    runtime = await _load_runtime(temp_dir, box_class, run_as_openhands)

    # Test run command
    action_cmd = CmdRunAction(command='ls -l')
    logger.info(action_cmd, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action_cmd)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})

    assert isinstance(obs, CmdOutputObservation)
    assert obs.exit_code == 0
    assert 'total 0' in obs.content

    # Test run ipython
    test_code = "print('Hello, `World`!\\n')"
    action_ipython = IPythonRunCellAction(code=test_code)
    logger.info(action_ipython, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action_ipython)
    assert isinstance(obs, IPythonRunCellObservation)

    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert (
        obs.content.strip()
        == 'Hello, `World`!\n[Jupyter current working directory: /workspace]'
    )

    # Test read file (file should not exist)
    action_read = FileReadAction(path='hello.sh')
    logger.info(action_read, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action_read)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert isinstance(obs, ErrorObservation)
    assert 'File not found' in obs.content

    # Test write file
    action_write = FileWriteAction(content='echo "Hello, World!"', path='hello.sh')
    logger.info(action_write, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action_write)
    assert isinstance(obs, FileWriteObservation)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})

    assert obs.content == ''
    # event stream runtime will always use absolute path
    assert obs.path == '/workspace/hello.sh'

    # Test read file (file should exist)
    action_read = FileReadAction(path='hello.sh')
    logger.info(action_read, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action_read)
    assert isinstance(
        obs, FileReadObservation
    ), 'The observation should be a FileReadObservation.'
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})

    assert obs.content == 'echo "Hello, World!"\n'
    assert obs.path == '/workspace/hello.sh'

    # clean up
    action = CmdRunAction(command='rm -rf hello.sh')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert obs.exit_code == 0

    await runtime.close()
    await asyncio.sleep(1)


@pytest.mark.asyncio
async def test_ipython_multi_user(temp_dir, box_class, run_as_openhands):
    runtime = await _load_runtime(temp_dir, box_class, run_as_openhands)

    # Test run ipython
    # get username
    test_code = "import os; print(os.environ['USER'])"
    action_ipython = IPythonRunCellAction(code=test_code)
    logger.info(action_ipython, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action_ipython)
    assert isinstance(obs, IPythonRunCellObservation)

    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    if run_as_openhands:
        assert 'openhands' in obs.content
    else:
        assert 'root' in obs.content

    # print pwd
    test_code = 'import os; print(os.getcwd())'
    action_ipython = IPythonRunCellAction(code=test_code)
    logger.info(action_ipython, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action_ipython)
    assert isinstance(obs, IPythonRunCellObservation)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert (
        obs.content.strip()
        == '/workspace\n[Jupyter current working directory: /workspace]'
    )

    # write a file
    test_code = "with open('test.txt', 'w') as f: f.write('Hello, world!')"
    action_ipython = IPythonRunCellAction(code=test_code)
    logger.info(action_ipython, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action_ipython)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert isinstance(obs, IPythonRunCellObservation)
    assert (
        obs.content.strip()
        == '[Code executed successfully with no output]\n[Jupyter current working directory: /workspace]'
    )

    # check file owner via bash
    action = CmdRunAction(command='ls -alh test.txt')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert obs.exit_code == 0
    if run_as_openhands:
        # -rw-r--r-- 1 openhands root 13 Jul 28 03:53 test.txt
        assert 'openhands' in obs.content.split('\r\n')[0]
        assert 'root' in obs.content.split('\r\n')[0]
    else:
        # -rw-r--r-- 1 root root 13 Jul 28 03:53 test.txt
        assert 'root' in obs.content.split('\r\n')[0]

    # clean up
    action = CmdRunAction(command='rm -rf test')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert obs.exit_code == 0

    await runtime.close()
    await asyncio.sleep(1)


@pytest.mark.asyncio
async def test_ipython_simple(temp_dir, box_class):
    runtime = await _load_runtime(temp_dir, box_class)

    # Test run ipython
    # get username
    test_code = 'print(1)'
    action_ipython = IPythonRunCellAction(code=test_code)
    logger.info(action_ipython, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action_ipython)
    assert isinstance(obs, IPythonRunCellObservation)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert obs.content.strip() == '1\n[Jupyter current working directory: /workspace]'

    await runtime.close()
    await asyncio.sleep(1)


async def _test_ipython_agentskills_fileop_pwd_impl(
    runtime: EventStreamRuntime, enable_auto_lint: bool
):
    # remove everything in /workspace
    action = CmdRunAction(command='rm -rf /workspace/*')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert obs.exit_code == 0

    action = CmdRunAction(command='mkdir test')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert isinstance(obs, CmdOutputObservation)
    assert obs.exit_code == 0

    action = IPythonRunCellAction(code="create_file('hello.py')")
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert isinstance(obs, IPythonRunCellObservation)
    assert obs.content.replace('\r\n', '\n').strip().split('\n') == (
        '[File: /workspace/hello.py (1 lines total)]\n'
        '(this is the beginning of the file)\n'
        '1|\n'
        '(this is the end of the file)\n'
        '[File hello.py created.]\n'
        '[Jupyter current working directory: /workspace]'
    ).strip().split('\n')

    action = CmdRunAction(command='cd test')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert isinstance(obs, CmdOutputObservation)
    assert obs.exit_code == 0

    # This should create a file in the current working directory
    # i.e., /workspace/test/hello.py instead of /workspace/hello.py
    action = IPythonRunCellAction(code="create_file('hello.py')")
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert isinstance(obs, IPythonRunCellObservation)
    assert obs.content.replace('\r\n', '\n').strip().split('\n') == (
        '[File: /workspace/test/hello.py (1 lines total)]\n'
        '(this is the beginning of the file)\n'
        '1|\n'
        '(this is the end of the file)\n'
        '[File hello.py created.]\n'
        '[Jupyter current working directory: /workspace/test]'
    ).strip().split('\n')

    if enable_auto_lint:
        # edit file, but make a mistake in indentation
        action = IPythonRunCellAction(
            code="insert_content_at_line('hello.py', 1, '  print(\"hello world\")')"
        )
        logger.info(action, extra={'msg_type': 'ACTION'})
        obs = await runtime.run_action(action)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert isinstance(obs, IPythonRunCellObservation)
        assert obs.content.replace('\r\n', '\n').strip().split('\n') == (
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
[Jupyter current working directory: /workspace/test]
"""
        ).strip().split('\n')

    # edit file with correct indentation
    action = IPythonRunCellAction(
        code="insert_content_at_line('hello.py', 1, 'print(\"hello world\")')"
    )
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert isinstance(obs, IPythonRunCellObservation)
    assert obs.content.replace('\r\n', '\n').strip().split('\n') == (
        """
[File: /workspace/test/hello.py (1 lines total after edit)]
(this is the beginning of the file)
1|print("hello world")
(this is the end of the file)
[File updated (edited at line 1). Please review the changes and make sure they are correct (correct indentation, no duplicate lines, etc). Edit the file again if necessary.]
[Jupyter current working directory: /workspace/test]
"""
    ).strip().split('\n')

    action = CmdRunAction(command='rm -rf /workspace/*')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert obs.exit_code == 0

    await runtime.close()
    await asyncio.sleep(1)


@pytest.mark.asyncio
async def test_ipython_agentskills_fileop_pwd(
    temp_dir, box_class, run_as_openhands, enable_auto_lint
):
    """Make sure that cd in bash also update the current working directory in ipython."""

    runtime = await _load_runtime(
        temp_dir, box_class, run_as_openhands, enable_auto_lint=enable_auto_lint
    )
    await _test_ipython_agentskills_fileop_pwd_impl(runtime, enable_auto_lint)

    await runtime.close()
    await asyncio.sleep(1)


@pytest.mark.asyncio
async def test_ipython_agentskills_fileop_pwd_with_userdir(temp_dir, box_class):
    """Make sure that cd in bash also update the current working directory in ipython.

    Handle special case where the pwd is provided as "~", which should be expanded using os.path.expanduser
    on the client side.
    """

    runtime = await _load_runtime(
        temp_dir,
        box_class,
        run_as_openhands=False,
    )

    action = CmdRunAction(command='cd ~')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert obs.exit_code == 0

    action = CmdRunAction(command='mkdir test && ls -la')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert isinstance(obs, CmdOutputObservation)
    assert obs.exit_code == 0

    action = IPythonRunCellAction(code="create_file('hello.py')")
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert isinstance(obs, IPythonRunCellObservation)
    assert obs.content.replace('\r\n', '\n').strip().split('\n') == (
        '[File: /root/hello.py (1 lines total)]\n'
        '(this is the beginning of the file)\n'
        '1|\n'
        '(this is the end of the file)\n'
        '[File hello.py created.]\n'
        '[Jupyter current working directory: /root]'
    ).strip().split('\n')

    action = CmdRunAction(command='cd test')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert isinstance(obs, CmdOutputObservation)
    assert obs.exit_code == 0

    # This should create a file in the current working directory
    # i.e., /workspace/test/hello.py instead of /workspace/hello.py
    action = IPythonRunCellAction(code="create_file('hello.py')")
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert isinstance(obs, IPythonRunCellObservation)
    assert obs.content.replace('\r\n', '\n').strip().split('\n') == (
        '[File: /root/test/hello.py (1 lines total)]\n'
        '(this is the beginning of the file)\n'
        '1|\n'
        '(this is the end of the file)\n'
        '[File hello.py created.]\n'
        '[Jupyter current working directory: /root/test]'
    ).strip().split('\n')

    await runtime.close()
    await asyncio.sleep(1)


@pytest.mark.asyncio
async def test_ipython_package_install(temp_dir, box_class, run_as_openhands):
    """Make sure that cd in bash also update the current working directory in ipython."""
    runtime = await _load_runtime(temp_dir, box_class, run_as_openhands)

    # It should error out since pymsgbox is not installed
    action = IPythonRunCellAction(code='import pymsgbox')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert "ModuleNotFoundError: No module named 'pymsgbox'" in obs.content

    # Install pymsgbox in Jupyter
    action = IPythonRunCellAction(code='%pip install pymsgbox==1.0.9')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert (
        'Successfully installed pymsgbox-1.0.9' in obs.content
        or '[Package installed successfully]' in obs.content
    )

    action = IPythonRunCellAction(code='import pymsgbox')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    # import should not error out
    assert (
        obs.content.strip()
        == '[Code executed successfully with no output]\n[Jupyter current working directory: /workspace]'
    )

    await runtime.close()
    await asyncio.sleep(1)
