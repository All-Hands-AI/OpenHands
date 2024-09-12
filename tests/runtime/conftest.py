import os
import random
import shutil
import stat
import time
from pathlib import Path

import pytest
from pytest import TempPathFactory

from openhands.core.config import load_app_config
from openhands.events import EventStream
from openhands.runtime.client.runtime import EventStreamRuntime
from openhands.runtime.plugins import AgentSkillsRequirement, JupyterRequirement
from openhands.runtime.remote.runtime import RemoteRuntime
from openhands.runtime.runtime import Runtime
from openhands.storage import get_file_store

TEST_IN_CI = os.getenv('TEST_IN_CI', 'False').lower() in ['true', '1', 'yes']
TEST_RUNTIME = os.getenv('TEST_RUNTIME', 'eventstream').lower()
RUN_AS_OPENHANDS = os.getenv('RUN_AS_OPENHANDS', 'True').lower() in ['true', '1', 'yes']
test_mount_path = ''
project_dir = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sandbox_test_folder = '/openhands/workspace'
tests_started = False


def _get_runtime_sid(runtime: Runtime):
    return '_'.join(runtime.sid.split('_')[:2])


def _get_host_folder(runtime: Runtime):
    return runtime.config.workspace_mount_path


def _get_sandbox_folder(runtime: Runtime):
    sid = _get_runtime_sid(runtime)
    if sid:
        return Path(os.path.join(sandbox_test_folder, sid))
    return None


def _close_test_runtime(runtime: Runtime):
    # TODO this is for EventStreamRuntime, not RemoteRuntime!
    runtime.close(rm_all_containers=False)
    time.sleep(1)


def _remove_test_folder():
    global test_mount_path, project_dir
    if test_mount_path:
        try:
            if test_mount_path and os.path.exists(test_mount_path):
                shutil.rmtree(test_mount_path)
                print(f'Removed sandbox test folder: {test_mount_path}')
        except FileNotFoundError:
            print('Failed to remove test folder!')
        test_mount_path = ''
        # Try to change back to project directory
        try:
            os.chdir(project_dir)
            print(f'Changed back to project directory: {project_dir}')
        except Exception as e:
            print(f'Failed to change back to project directory: {e}')


# *****************************************************************************
# *****************************************************************************


@pytest.fixture(autouse=True)
def print_method_name(request):
    print(
        '\n\n########################################################################'
    )
    print(f'Running test: {request.node.name}')
    print(
        '########################################################################\n\n'
    )


@pytest.fixture
def temp_dir(tmp_path_factory: TempPathFactory, request) -> str:
    """Creates a unique temporary directory.
    Upon finalization, the temporary directory and its content is removed.

    Parameters:
    - tmp_path_factory (TempPathFactory): A TempPathFactory class

    Returns:
    - str: The temporary directory path that was created
    """
    temp_dir = tmp_path_factory.mktemp('test', numbered=True)

    # Set permissions to ensure the directory is writable and deletable
    os.chmod(temp_dir, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)  # 0777 permissions

    def cleanup():
        global project_dir
        os.chdir(project_dir)
        if os.path.exists(temp_dir):
            try:
                os.rmdir(temp_dir)
            except OSError:
                try:
                    shutil.rmtree(temp_dir)
                except OSError:
                    pass

    request.addfinalizer(cleanup)

    return str(temp_dir)


# Depending on TEST_RUNTIME, feed the appropriate box class(es) to the test.
def get_box_classes():
    runtime = TEST_RUNTIME
    if runtime.lower() == 'eventstream':
        return [EventStreamRuntime]
    elif runtime.lower() == 'remote':
        return [RemoteRuntime]
    else:
        raise ValueError(f'Invalid runtime: {runtime}')


def get_run_as_openhands():
    print(
        '\n\n########################################################################'
    )
    print('USER: ' + 'openhands' if RUN_AS_OPENHANDS else 'root')
    print(
        '########################################################################\n\n'
    )
    return [RUN_AS_OPENHANDS]


@pytest.fixture(scope='session')
def runtime_setup():
    yield
    _remove_test_folder()


# This assures that all tests run together per runtime, not alternating between them,
# which cause errors (especially outside GitHub actions).
@pytest.fixture(scope='module', params=get_box_classes())
def box_class(request):
    time.sleep(1)
    return request.param


# TODO: We will change this to `run_as_user` when `ServerRuntime` is deprecated.
# since `EventStreamRuntime` supports running as an arbitrary user.
@pytest.fixture(scope='module', params=get_run_as_openhands())
def run_as_openhands(request):
    time.sleep(1)
    return request.param


@pytest.fixture(scope='module', params=None)
def base_container_image(request):
    time.sleep(1)
    env_image = os.environ.get('SANDBOX_BASE_CONTAINER_IMAGE')
    if env_image:
        request.param = env_image
    else:
        if not hasattr(request, 'param'):  # prevent runtime AttributeError
            request.param = None
        if request.param is None and hasattr(request.config, 'sandbox'):
            try:
                request.param = request.config.sandbox.getoption(
                    '--base_container_image'
                )
            except ValueError:
                request.param = None
        if request.param is None:
            request.param = pytest.param(
                'nikolaik/python-nodejs:python3.11-nodejs22',
                'golang:1.23-bookworm',
            )
    print(f'Container image: {request.param}')
    return request.param


def _load_runtime(
    temp_dir,
    box_class,
    run_as_openhands: bool = True,
    enable_auto_lint: bool = False,
    base_container_image: str | None = None,
    browsergym_eval_env: str | None = None,
) -> Runtime:
    sid = os.path.basename(temp_dir) + '_' + str(random.randint(10000, 99999))
    global test_mount_path

    print(f'*** Test temp directory: {temp_dir}')
    # AgentSkills need to be initialized **before** Jupyter
    # otherwise Jupyter will not access the proper dependencies installed by AgentSkills
    plugins = [AgentSkillsRequirement(), JupyterRequirement()]

    config = load_app_config()
    config.run_as_openhands = run_as_openhands

    # Folder where all tests create their own folder
    test_mount_path = temp_dir

    # Folder specific for this test identified by the generated instance_id
    config.workspace_mount_path = os.path.join(test_mount_path, sid)

    # Mounting folder specific for this test inside the sandbox
    config.workspace_mount_path_in_sandbox = f'{sandbox_test_folder}/{sid}'
    print('\nPaths used:')
    print(f'use_host_network: {config.sandbox.use_host_network}')
    print(f'workspace_base: {config.workspace_base}')
    print(f'workspace_mount_path: {config.workspace_mount_path}')
    print(
        f'workspace_mount_path_in_sandbox: {config.workspace_mount_path_in_sandbox}\n'
    )

    config.sandbox.browsergym_eval_env = browsergym_eval_env
    config.sandbox.enable_auto_lint = enable_auto_lint

    if base_container_image is not None:
        config.sandbox.base_container_image = base_container_image

    file_store = get_file_store(config.file_store, config.file_store_path)
    event_stream = EventStream(sid, file_store)

    runtime = box_class(
        config=config,
        event_stream=event_stream,
        sid=sid,
        plugins=plugins,
    )
    time.sleep(2)
    return runtime


# Export necessary function
__all__ = [
    '_load_runtime',
    '_get_host_folder',
    '_get_sandbox_folder',
]
