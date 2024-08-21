"""Bash-related tests for the EventStreamRuntime, which connects to the RuntimeClient running in the sandbox."""

import asyncio
import os
import tempfile
import time

import pytest
from pytest import TempPathFactory

from openhands.core.config import AppConfig, SandboxConfig, load_from_env
from openhands.core.logger import openhands_logger as logger
from openhands.events import EventStream
from openhands.events.action import CmdRunAction
from openhands.events.observation import CmdOutputObservation
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
# Bash-specific tests
# ============================================================================================================================


@pytest.mark.asyncio
async def test_bash_command_pexcept(temp_dir, box_class, run_as_openhands):
    runtime = await _load_runtime(temp_dir, box_class, run_as_openhands)

    # We set env var PS1="\u@\h:\w $"
    # and construct the PEXCEPT prompt base on it.
    # When run `env`, bad implementation of CmdRunAction will be pexcepted by this
    # and failed to pexcept the right content, causing it fail to get error code.
    obs = await runtime.run_action(CmdRunAction(command='env'))

    # For example:
    # 02:16:13 - openhands:DEBUG: client.py:78 - Executing command: env
    # 02:16:13 - openhands:DEBUG: client.py:82 - Command output: PYTHONUNBUFFERED=1
    # CONDA_EXE=/openhands/miniforge3/bin/conda
    # [...]
    # LC_CTYPE=C.UTF-8
    # PS1=\u@\h:\w $
    # 02:16:13 - openhands:DEBUG: client.py:89 - Executing command for exit code: env
    # 02:16:13 - openhands:DEBUG: client.py:92 - Exit code Output:
    # CONDA_DEFAULT_ENV=base

    # As long as the exit code is 0, the test will pass.
    assert isinstance(
        obs, CmdOutputObservation
    ), 'The observation should be a CmdOutputObservation.'
    assert obs.exit_code == 0, 'The exit code should be 0.'

    await runtime.close()
    await asyncio.sleep(1)


@pytest.mark.asyncio
async def test_single_multiline_command(temp_dir, box_class):
    runtime = await _load_runtime(temp_dir, box_class)

    action = CmdRunAction(command='echo \\\n -e "foo"')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert obs.exit_code == 0, 'The exit code should be 0.'
    assert 'foo' in obs.content

    await runtime.close()
    await asyncio.sleep(1)


@pytest.mark.asyncio
async def test_multiline_echo(temp_dir, box_class):
    runtime = await _load_runtime(temp_dir, box_class)

    action = CmdRunAction(command='echo -e "hello\nworld"')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert obs.exit_code == 0, 'The exit code should be 0.'
    assert 'hello\r\nworld' in obs.content

    await runtime.close()
    await asyncio.sleep(1)


@pytest.mark.asyncio
async def test_runtime_whitespace(temp_dir, box_class):
    runtime = await _load_runtime(temp_dir, box_class)

    action = CmdRunAction(command='echo -e "\\n\\n\\n"')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})

    assert obs.exit_code == 0, 'The exit code should be 0.'
    assert '\r\n\r\n\r\n' in obs.content

    await runtime.close()
    await asyncio.sleep(1)


@pytest.mark.asyncio
async def test_multiple_multiline_commands(temp_dir, box_class, run_as_openhands):
    cmds = [
        'ls -l',
        'echo -e "hello\nworld"',
        """
echo -e "hello it\\'s me"
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
    ]
    joined_cmds = '\n'.join(cmds)

    runtime = await _load_runtime(temp_dir, box_class, run_as_openhands)

    action = CmdRunAction(command=joined_cmds)
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})

    assert isinstance(obs, CmdOutputObservation)
    assert obs.exit_code == 0, 'The exit code should be 0.'

    assert 'total 0' in obs.content
    assert 'hello\r\nworld' in obs.content
    assert "hello it\\'s me" in obs.content
    assert 'hello -v' in obs.content
    assert 'hello\r\nworld\r\nare\r\nyou\r\nthere?' in obs.content
    assert 'hello\r\nworld\r\nare\r\nyou\r\n\r\nthere?' in obs.content
    assert 'hello\r\nworld "\r\n' in obs.content

    await runtime.close()
    await asyncio.sleep(1)


@pytest.mark.asyncio
async def test_no_ps2_in_output(temp_dir, box_class, run_as_openhands):
    """Test that the PS2 sign is not added to the output of a multiline command."""
    runtime = await _load_runtime(temp_dir, box_class, run_as_openhands)

    action = CmdRunAction(command='echo -e "hello\nworld"')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})

    assert 'hello\r\nworld' in obs.content
    assert '>' not in obs.content

    await runtime.close()
    await asyncio.sleep(1)


@pytest.mark.asyncio
async def test_multiline_command_loop(temp_dir, box_class):
    # https://github.com/All-Hands-AI/OpenHands/issues/3143

    runtime = await _load_runtime(temp_dir, box_class)

    init_cmd = """
mkdir -p _modules && \
for month in {01..04}; do
    for day in {01..05}; do
        touch "_modules/2024-${month}-${day}-sample.md"
    done
done
echo "created files"
"""
    action = CmdRunAction(command=init_cmd)
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})

    assert isinstance(obs, CmdOutputObservation)
    assert obs.exit_code == 0, 'The exit code should be 0.'
    assert 'created files' in obs.content

    follow_up_cmd = """
for file in _modules/*.md; do
    new_date=$(echo $file | sed -E 's/2024-(01|02|03|04)-/2024-/;s/2024-01/2024-08/;s/2024-02/2024-09/;s/2024-03/2024-10/;s/2024-04/2024-11/')
    mv "$file" "$new_date"
done
echo "success"
"""
    action = CmdRunAction(command=follow_up_cmd)
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})

    assert isinstance(obs, CmdOutputObservation)
    assert obs.exit_code == 0, 'The exit code should be 0.'
    assert 'success' in obs.content

    await runtime.close()
    await asyncio.sleep(1)


@pytest.mark.asyncio
async def test_cmd_run(temp_dir, box_class, run_as_openhands):
    runtime = await _load_runtime(temp_dir, box_class, run_as_openhands)

    action = CmdRunAction(command='ls -l')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert isinstance(obs, CmdOutputObservation)
    assert obs.exit_code == 0
    assert 'total 0' in obs.content

    action = CmdRunAction(command='mkdir test')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert isinstance(obs, CmdOutputObservation)
    assert obs.exit_code == 0

    action = CmdRunAction(command='ls -l')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert isinstance(obs, CmdOutputObservation)
    assert obs.exit_code == 0
    if run_as_openhands:
        assert 'openhands' in obs.content
    else:
        assert 'root' in obs.content
    assert 'test' in obs.content

    action = CmdRunAction(command='touch test/foo.txt')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert isinstance(obs, CmdOutputObservation)
    assert obs.exit_code == 0

    action = CmdRunAction(command='ls -l test')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert isinstance(obs, CmdOutputObservation)
    assert obs.exit_code == 0
    assert 'foo.txt' in obs.content

    # clean up: this is needed, since CI will not be
    # run as root, and this test may leave a file
    # owned by root
    action = CmdRunAction(command='rm -rf test')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert isinstance(obs, CmdOutputObservation)
    assert obs.exit_code == 0

    await runtime.close()
    await asyncio.sleep(1)


@pytest.mark.asyncio
async def test_run_as_user_correct_home_dir(temp_dir, box_class, run_as_openhands):
    runtime = await _load_runtime(temp_dir, box_class, run_as_openhands)

    action = CmdRunAction(command='cd ~ && pwd')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert isinstance(obs, CmdOutputObservation)
    assert obs.exit_code == 0
    if run_as_openhands:
        assert '/home/openhands' in obs.content
    else:
        assert '/root' in obs.content

    await runtime.close()
    await asyncio.sleep(1)


@pytest.mark.asyncio
async def test_multi_cmd_run_in_single_line(temp_dir, box_class):
    runtime = await _load_runtime(temp_dir, box_class)

    action = CmdRunAction(command='pwd && ls -l')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert isinstance(obs, CmdOutputObservation)
    assert obs.exit_code == 0
    assert '/workspace' in obs.content
    assert 'total 0' in obs.content

    await runtime.close()
    await asyncio.sleep(1)


@pytest.mark.asyncio
async def test_stateful_cmd(temp_dir, box_class):
    runtime = await _load_runtime(temp_dir, box_class)

    action = CmdRunAction(command='mkdir test')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert isinstance(obs, CmdOutputObservation)
    assert obs.exit_code == 0, 'The exit code should be 0.'

    action = CmdRunAction(command='cd test')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert isinstance(obs, CmdOutputObservation)
    assert obs.exit_code == 0, 'The exit code should be 0.'

    action = CmdRunAction(command='pwd')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert isinstance(obs, CmdOutputObservation)
    assert obs.exit_code == 0, 'The exit code should be 0.'
    assert '/workspace/test' in obs.content

    await runtime.close()
    await asyncio.sleep(1)


@pytest.mark.asyncio
async def test_failed_cmd(temp_dir, box_class):
    runtime = await _load_runtime(temp_dir, box_class)

    action = CmdRunAction(command='non_existing_command')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert isinstance(obs, CmdOutputObservation)
    assert obs.exit_code != 0, 'The exit code should not be 0 for a failed command.'

    await runtime.close()
    await asyncio.sleep(1)


def _create_test_file(host_temp_dir):
    # Single file
    with open(os.path.join(host_temp_dir, 'test_file.txt'), 'w') as f:
        f.write('Hello, World!')


@pytest.mark.asyncio
async def test_copy_single_file(temp_dir, box_class):
    runtime = await _load_runtime(temp_dir, box_class)

    with tempfile.TemporaryDirectory() as host_temp_dir:
        _create_test_file(host_temp_dir)
        await runtime.copy_to(
            os.path.join(host_temp_dir, 'test_file.txt'), '/workspace'
        )

    action = CmdRunAction(command='ls -alh /workspace')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert isinstance(obs, CmdOutputObservation)
    assert obs.exit_code == 0
    assert 'test_file.txt' in obs.content

    action = CmdRunAction(command='cat /workspace/test_file.txt')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert isinstance(obs, CmdOutputObservation)
    assert obs.exit_code == 0
    assert 'Hello, World!' in obs.content

    await runtime.close()
    await asyncio.sleep(1)


def _create_test_dir_with_files(host_temp_dir):
    os.mkdir(os.path.join(host_temp_dir, 'test_dir'))
    with open(os.path.join(host_temp_dir, 'test_dir', 'file1.txt'), 'w') as f:
        f.write('File 1 content')
    with open(os.path.join(host_temp_dir, 'test_dir', 'file2.txt'), 'w') as f:
        f.write('File 2 content')


@pytest.mark.asyncio
async def test_copy_directory_recursively(temp_dir, box_class):
    runtime = await _load_runtime(temp_dir, box_class)

    with tempfile.TemporaryDirectory() as host_temp_dir:
        # We need a separate directory, since temp_dir is mounted to /workspace
        _create_test_dir_with_files(host_temp_dir)
        await runtime.copy_to(
            os.path.join(host_temp_dir, 'test_dir'), '/workspace', recursive=True
        )

    action = CmdRunAction(command='ls -alh /workspace')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert isinstance(obs, CmdOutputObservation)
    assert obs.exit_code == 0
    assert 'test_dir' in obs.content
    assert 'file1.txt' not in obs.content
    assert 'file2.txt' not in obs.content

    action = CmdRunAction(command='ls -alh /workspace/test_dir')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert isinstance(obs, CmdOutputObservation)
    assert obs.exit_code == 0
    assert 'file1.txt' in obs.content
    assert 'file2.txt' in obs.content

    action = CmdRunAction(command='cat /workspace/test_dir/file1.txt')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert isinstance(obs, CmdOutputObservation)
    assert obs.exit_code == 0
    assert 'File 1 content' in obs.content

    await runtime.close()
    await asyncio.sleep(1)


@pytest.mark.asyncio
async def test_copy_to_non_existent_directory(temp_dir, box_class):
    runtime = await _load_runtime(temp_dir, box_class)

    with tempfile.TemporaryDirectory() as host_temp_dir:
        _create_test_file(host_temp_dir)
        await runtime.copy_to(
            os.path.join(host_temp_dir, 'test_file.txt'), '/workspace/new_dir'
        )

    action = CmdRunAction(command='cat /workspace/new_dir/test_file.txt')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert isinstance(obs, CmdOutputObservation)
    assert obs.exit_code == 0
    assert 'Hello, World!' in obs.content

    await runtime.close()
    await asyncio.sleep(1)


@pytest.mark.asyncio
async def test_overwrite_existing_file(temp_dir, box_class):
    runtime = await _load_runtime(temp_dir, box_class)

    # touch a file in /workspace
    action = CmdRunAction(command='touch /workspace/test_file.txt')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert isinstance(obs, CmdOutputObservation)
    assert obs.exit_code == 0

    action = CmdRunAction(command='cat /workspace/test_file.txt')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert isinstance(obs, CmdOutputObservation)
    assert obs.exit_code == 0
    assert 'Hello, World!' not in obs.content

    with tempfile.TemporaryDirectory() as host_temp_dir:
        _create_test_file(host_temp_dir)
        await runtime.copy_to(
            os.path.join(host_temp_dir, 'test_file.txt'), '/workspace'
        )

    action = CmdRunAction(command='cat /workspace/test_file.txt')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert isinstance(obs, CmdOutputObservation)
    assert obs.exit_code == 0
    assert 'Hello, World!' in obs.content

    await runtime.close()
    await asyncio.sleep(1)


@pytest.mark.asyncio
async def test_copy_non_existent_file(temp_dir, box_class):
    runtime = await _load_runtime(temp_dir, box_class)

    with pytest.raises(FileNotFoundError):
        await runtime.copy_to(
            os.path.join(temp_dir, 'non_existent_file.txt'),
            '/workspace/should_not_exist.txt',
        )

    action = CmdRunAction(command='ls /workspace/should_not_exist.txt')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert isinstance(obs, CmdOutputObservation)
    assert obs.exit_code != 0  # File should not exist

    await runtime.close()
    await asyncio.sleep(1)


@pytest.mark.asyncio
async def test_keep_prompt(temp_dir):
    # only EventStreamRuntime supports keep_prompt
    runtime = await _load_runtime(
        temp_dir, box_class=EventStreamRuntime, run_as_openhands=False
    )

    action = CmdRunAction(command='touch /workspace/test_file.txt')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert isinstance(obs, CmdOutputObservation)
    assert obs.exit_code == 0
    assert 'root@' in obs.content

    action = CmdRunAction(command='cat /workspace/test_file.txt', keep_prompt=False)
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert isinstance(obs, CmdOutputObservation)
    assert obs.exit_code == 0
    assert 'root@' not in obs.content

    await runtime.close()
    await asyncio.sleep(1)


@pytest.mark.asyncio
async def test_git_operation(box_class):
    # do not mount workspace, since workspace mount by tests will be owned by root
    # while the user_id we get via os.getuid() is different from root
    # which causes permission issues
    runtime = await _load_runtime(
        temp_dir=None,
        box_class=box_class,
        # Need to use non-root user to expose issues
        run_as_openhands=True,
    )

    # this will happen if permission of runtime is not properly configured
    # fatal: detected dubious ownership in repository at '/workspace'

    # check the ownership of the current directory
    action = CmdRunAction(command='ls -alh .')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert isinstance(obs, CmdOutputObservation)
    assert obs.exit_code == 0
    # drwx--S--- 2 openhands root   64 Aug  7 23:32 .
    # drwxr-xr-x 1 root      root 4.0K Aug  7 23:33 ..
    for line in obs.content.split('\r\n'):
        if ' ..' in line:
            # parent directory should be owned by root
            assert 'root' in line
            assert 'openhands' not in line
        elif ' .' in line:
            # current directory should be owned by openhands
            # and its group should be root
            assert 'openhands' in line
            assert 'root' in line

    # make sure all git operations are allowed
    action = CmdRunAction(command='git init')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert isinstance(obs, CmdOutputObservation)
    assert obs.exit_code == 0

    # create a file
    action = CmdRunAction(command='echo "hello" > test_file.txt')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert isinstance(obs, CmdOutputObservation)
    assert obs.exit_code == 0

    # git add
    action = CmdRunAction(command='git add test_file.txt')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert isinstance(obs, CmdOutputObservation)
    assert obs.exit_code == 0

    # git diff
    action = CmdRunAction(command='git diff')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert isinstance(obs, CmdOutputObservation)
    assert obs.exit_code == 0

    # git commit
    action = CmdRunAction(command='git commit -m "test commit"')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert isinstance(obs, CmdOutputObservation)
    assert obs.exit_code == 0

    await runtime.close()

    await runtime.close()
    await asyncio.sleep(1)
