"""Browsing-related tests for the EventStreamRuntime, which connects to the RuntimeClient running in the sandbox."""

import json

from conftest import _close_test_runtime, _load_runtime

from openhands.core.logger import openhands_logger as logger
from openhands.events.action import (
    BrowseInteractiveAction,
    BrowseURLAction,
    CmdRunAction,
)
from openhands.events.observation import (
    BrowserOutputObservation,
    CmdOutputObservation,
)

# ============================================================================================================================
# Browsing tests
# ============================================================================================================================

PY3_FOR_TESTING = '/openhands/miniforge3/bin/mamba run -n base python3'


def test_simple_browse(temp_dir, box_class, run_as_openhands):
    runtime = _load_runtime(temp_dir, box_class, run_as_openhands)

    # Test browse
    action_cmd = CmdRunAction(
        command=f'{PY3_FOR_TESTING} -m http.server 8000 > server.log 2>&1 &'
    )
    logger.info(action_cmd, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action_cmd)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})

    assert isinstance(obs, CmdOutputObservation)
    assert obs.exit_code == 0
    assert '[1]' in obs.content

    action_cmd = CmdRunAction(command='sleep 3 && cat server.log')
    logger.info(action_cmd, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action_cmd)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert obs.exit_code == 0

    action_browse = BrowseURLAction(url='http://localhost:8000')
    logger.info(action_browse, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action_browse)
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
    obs = runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert obs.exit_code == 0

    _close_test_runtime(runtime)


def test_browsergym_eval_env(box_class, temp_dir):
    runtime = _load_runtime(
        temp_dir,
        box_class=box_class,
        run_as_openhands=False,  # need root permission to access file
        base_container_image='xingyaoww/od-eval-miniwob:v1.0',
        browsergym_eval_env='browsergym/miniwob.choose-list',
    )
    from openhands.runtime.browser.browser_env import (
        BROWSER_EVAL_GET_GOAL_ACTION,
        BROWSER_EVAL_GET_REWARDS_ACTION,
    )

    # Test browse
    action = BrowseInteractiveAction(browser_actions=BROWSER_EVAL_GET_GOAL_ACTION)
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})

    assert isinstance(obs, BrowserOutputObservation)
    assert not obs.error
    assert 'Select' in obs.content
    assert 'from the list and click Submit' in obs.content

    # Make sure the browser can produce observation in eva[l
    action = BrowseInteractiveAction(browser_actions='noop()')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert (
        obs.url.strip()
        == 'file:///miniwob-plusplus/miniwob/html/miniwob/choose-list.html'
    )

    # Make sure the rewards are working
    action = BrowseInteractiveAction(browser_actions=BROWSER_EVAL_GET_REWARDS_ACTION)
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert json.loads(obs.content) == [0.0]

    _close_test_runtime(runtime)
