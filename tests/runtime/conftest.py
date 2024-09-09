import os
import random
import time

import pytest
from pytest import TempPathFactory

from openhands.core.config import AppConfig, SandboxConfig, load_from_env
from openhands.events import EventStream
from openhands.runtime.client.runtime import EventStreamRuntime
from openhands.runtime.plugins import AgentSkillsRequirement, JupyterRequirement
from openhands.runtime.remote.runtime import RemoteRuntime
from openhands.runtime.runtime import Runtime
from openhands.storage import get_file_store


@pytest.fixture(autouse=True)
def print_method_name(request):
    print(
        '\n\n########################################################################'
    )
    print(f'Running test: {request.node.name}')
    print(
        '########################################################################\n\n'
    )
    yield


@pytest.fixture
def temp_dir(tmp_path_factory: TempPathFactory, request) -> str:
    random_number = random.randint(10000, 99999)
    temp_dir = tmp_path_factory.mktemp(f'test_runtime_{random_number}')

    def cleanup():
        if os.path.exists(temp_dir):
            try:
                os.rmdir(temp_dir)
            except OSError:
                import shutil

                shutil.rmtree(temp_dir)

    request.addfinalizer(cleanup)

    return str(temp_dir)


TEST_RUNTIME = os.getenv('TEST_RUNTIME', 'eventstream').lower()
RUN_AS_OPENHANDS = (
    os.getenv('RUN_AS_OPENHANDS', 'True').lower() in ['true', '1', 'yes'] == 'true'
)


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
    return [RUN_AS_OPENHANDS]


# This assures that all tests run together per runtime, not alternating between them,
# which cause errors (especially outside GitHub actions).
@pytest.fixture(scope='module', params=get_box_classes())
def box_class(request):
    time.sleep(2)
    return request.param


# TODO: We will change this to `run_as_user` when `ServerRuntime` is deprecated.
# since `EventStreamRuntime` supports running as an arbitrary user.
@pytest.fixture(scope='module', params=get_run_as_openhands())
def run_as_openhands(request):
    return request.param


@pytest.fixture(scope='module', params=[True, False])
def enable_auto_lint(request):
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


@pytest.fixture
def runtime(temp_dir, box_class, run_as_openhands):
    runtime = _load_runtime(temp_dir, box_class, run_as_openhands)
    yield runtime
    runtime.close()
    time.sleep(1)


def _load_runtime(
    temp_dir,
    box_class,
    run_as_openhands: bool = True,
    enable_auto_lint: bool = False,
    base_container_image: str | None = None,
    browsergym_eval_env: str | None = None,
) -> Runtime:
    sid = 'test'
    cli_session = 'main_test'

    # AgentSkills need to be initialized **before** Jupyter
    # otherwise Jupyter will not access the proper dependencies installed by AgentSkills
    plugins = [AgentSkillsRequirement(), JupyterRequirement()]

    # Create a workspace folder in the temp directory
    temp_folder = os.path.join(temp_dir, 'workspace/')
    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)

    config = AppConfig(
        workspace_base=temp_folder,
        workspace_mount_path_in_sandbox=temp_folder,
        sandbox=SandboxConfig(
            use_host_network=True,
            browsergym_eval_env=browsergym_eval_env,
        ),
    )
    load_from_env(config, os.environ)
    config.run_as_openhands = run_as_openhands
    config.sandbox.enable_auto_lint = enable_auto_lint
    if base_container_image is not None:
        config.sandbox.base_container_image = base_container_image

    file_store = get_file_store(config.file_store, config.file_store_path)
    event_stream = EventStream(cli_session, file_store)

    runtime = box_class(
        config=config,
        event_stream=event_stream,
        sid=sid,
        plugins=plugins,
    )
    time.sleep(1)
    return runtime


# Export necessary function
__all__ = ['_load_runtime']
