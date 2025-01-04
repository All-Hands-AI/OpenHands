"""Stress tests for the EventStreamRuntime, which connects to the ActionExecutor running in the sandbox."""

import pytest
from conftest import TEST_IN_CI, _close_test_runtime, _load_runtime

from openhands.core.logger import openhands_logger as logger
from openhands.events.action import CmdRunAction


@pytest.mark.skipif(
    TEST_IN_CI,
    reason='This test should only be run locally, not in CI.',
)
def test_stress_eventstream_runtime(temp_dir, runtime_cls, repeat=1):
    runtime = _load_runtime(temp_dir, runtime_cls)

    action = CmdRunAction(
        command='sudo apt-get update && sudo apt-get install -y stress-ng'
    )
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert obs.exit_code == 0

    for _ in range(repeat):
        # run stress-ng stress tests for 5 minutes
        # FIXME: this would make Docker daemon die, even though running this
        # command on its own in the same container is fine
        action = CmdRunAction(command='stress-ng --all 1 -t 5m')
        action.timeout = 600
        logger.info(action, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

    _close_test_runtime(runtime)
