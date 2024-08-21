"""Browsing-related tests for the EventStreamRuntime, which connects to the RuntimeClient running in the sandbox."""

import asyncio
import json
import os
import time

import pytest
from pytest import TempPathFactory

from openhands.core.config import AppConfig, SandboxConfig, load_from_env
from openhands.core.logger import openhands_logger as logger
from openhands.events import EventStream
from openhands.events.action import (
    BrowseInteractiveAction,
    BrowseURLAction,
    CmdRunAction,
)
from openhands.events.observation import (
    BrowserOutputObservation,
    CmdOutputObservation,
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
# Browsing tests
# ============================================================================================================================


@pytest.mark.asyncio
async def test_simple_browse(temp_dir, box_class, run_as_openhands):
    runtime = await _load_runtime(temp_dir, box_class, run_as_openhands)

    # Test browse
    action_cmd = CmdRunAction(
        command=f'{PY3_FOR_TESTING} -m http.server 8000 > server.log 2>&1 &'
    )
    logger.info(action_cmd, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action_cmd)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})

    assert isinstance(obs, CmdOutputObservation)
    assert obs.exit_code == 0
    assert '[1]' in obs.content

    action_cmd = CmdRunAction(command='sleep 5 && cat server.log')
    logger.info(action_cmd, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action_cmd)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert obs.exit_code == 0

    action_browse = BrowseURLAction(url='http://localhost:8000')
    logger.info(action_browse, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action_browse)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})

    assert isinstance(obs, BrowserOutputObservation)
    assert 'http://localhost:8000' in obs.url
    assert not obs.error
    assert obs.open_pages_urls == ['http://localhost:8000/']
    assert obs.active_page_index == 0
    assert obs.last_browser_action == 'goto("http://localhost:8000")'
    assert obs.last_browser_action_error == ''
    assert 'Directory listing for /' in obs.content
    assert 'server.log' in obs.content

    # clean up
    action = CmdRunAction(command='rm -rf server.log')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert obs.exit_code == 0

    await runtime.close()
    await asyncio.sleep(1)


@pytest.mark.asyncio
async def test_browsergym_eval_env(temp_dir):
    runtime = await _load_runtime(
        temp_dir,
        # only supported in event stream runtime
        box_class=EventStreamRuntime,
        run_as_openhands=False,  # need root permission to access file
        container_image='xingyaoww/od-eval-miniwob:v1.0',
        browsergym_eval_env='browsergym/miniwob.choose-list',
    )
    from openhands.runtime.browser.browser_env import (
        BROWSER_EVAL_GET_GOAL_ACTION,
        BROWSER_EVAL_GET_REWARDS_ACTION,
    )

    # Test browse
    action = BrowseInteractiveAction(browser_actions=BROWSER_EVAL_GET_GOAL_ACTION)
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})

    assert isinstance(obs, BrowserOutputObservation)
    assert not obs.error
    assert 'Select' in obs.content
    assert 'from the list and click Submit' in obs.content

    # Make sure the browser can produce observation in eva[l
    action = BrowseInteractiveAction(browser_actions='noop()')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert (
        obs.url.strip()
        == 'file:///miniwob-plusplus/miniwob/html/miniwob/choose-list.html'
    )

    # Make sure the rewards are working
    action = BrowseInteractiveAction(browser_actions=BROWSER_EVAL_GET_REWARDS_ACTION)
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert json.loads(obs.content) == [0.0]

    await runtime.close()
    await asyncio.sleep(1)
