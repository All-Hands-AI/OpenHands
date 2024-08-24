import asyncio
import os
import time

import pytest
from pytest import TempPathFactory

from openhands.core.config import AppConfig, SandboxConfig, load_from_env
from openhands.events import EventStream
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


@pytest.fixture
async def runtime(temp_dir, box_class, run_as_openhands):
    runtime = await _load_runtime(temp_dir, box_class, run_as_openhands)
    yield runtime
    await runtime.close()
    await asyncio.sleep(1)


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


# Export necessary function
__all__ = ['_load_runtime']
