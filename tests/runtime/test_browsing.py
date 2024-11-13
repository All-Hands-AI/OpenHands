"""Browsing-related tests for the EventStreamRuntime, which connects to the ActionExecutor running in the sandbox."""

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

PY3_FOR_TESTING = '/openhands/micromamba/bin/micromamba run -n openhands python3'


def test_simple_browse(temp_dir, runtime_cls, run_as_openhands):
    runtime = _load_runtime(temp_dir, runtime_cls, run_as_openhands)

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


def test_browsergym_eval_env(runtime_cls, temp_dir):
    runtime = _load_runtime(
        temp_dir,
        runtime_cls=runtime_cls,
        run_as_openhands=False,  # need root permission to access file
        base_container_image='xingyaoww/od-eval-miniwob:v1.0',
        browsergym_eval_env='browsergym/miniwob.choose-list',
        force_rebuild_runtime=True,
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

def test_multi_session_browse(temp_dir, runtime_cls, run_as_openhands):
    # Start two runtimes with different session IDs
    runtime1 = _load_runtime(temp_dir, runtime_cls, run_as_openhands, sid="session1")
    runtime2 = _load_runtime(temp_dir, runtime_cls, run_as_openhands, sid="session2")

    # Start a test server for browsing
    action_cmd = CmdRunAction(
        command=f"{PY3_FOR_TESTING} -m http.server 8000 > server.log 2>&1 &"
    )
    obs = runtime1.run_action(action_cmd)
    assert isinstance(obs, CmdOutputObservation)
    assert obs.exit_code == 0

    # Wait for server to start
    action_cmd = CmdRunAction(command="sleep 3")
    runtime1.run_action(action_cmd)

    # Test that each runtime has its own independent browser session
    # First runtime browses to localhost:8000
    action1 = BrowseURLAction(url="http://localhost:8000")
    obs1 = runtime1.run_action(action1)
    assert isinstance(obs1, BrowserOutputObservation)
    assert "http://localhost:8000" in obs1.url
    assert not obs1.error
    assert obs1.open_pages_urls == ["http://localhost:8000/"]
    assert "Directory listing for /" in obs1.content

    # Second runtime browses to about:blank
    action2 = BrowseURLAction(url="about:blank")
    obs2 = runtime2.run_action(action2)
    assert isinstance(obs2, BrowserOutputObservation)
    assert "about:blank" in obs2.url
    assert not obs2.error
    assert obs2.open_pages_urls == ["about:blank"]

    # Verify sessions remain independent
    action1 = BrowseInteractiveAction(browser_actions="noop()")
    obs1 = runtime1.run_action(action1)
    assert "http://localhost:8000" in obs1.url  # First session still on localhost

    action2 = BrowseInteractiveAction(browser_actions="noop()")
    obs2 = runtime2.run_action(action2)
    assert "about:blank" in obs2.url  # Second session still on about:blank

    # Clean up
    action = CmdRunAction(command="rm -rf server.log")
    runtime1.run_action(action)

    _close_test_runtime(runtime1)
    _close_test_runtime(runtime2)
