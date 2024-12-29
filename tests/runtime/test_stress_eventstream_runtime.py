"""Stress tests for the EventStreamRuntime, which connects to the ActionExecutor running in the sandbox."""

import pytest
from conftest import TEST_IN_CI, _close_test_runtime, _load_runtime

from openhands.core.logger import openhands_logger as logger
from openhands.events.action import CmdRunAction


@pytest.mark.skipif(
    TEST_IN_CI,
    reason='This test should only be run locally, not in CI.',
)
def test_stress_eventstream_runtime(temp_dir, runtime_cls, repeat=10):
    runtime = _load_runtime(temp_dir, runtime_cls)

    action = CmdRunAction(
        command='sudo apt-get update && sudo apt-get install -y stress-ng'
    )
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert obs.exit_code == 0

    for _ in range(repeat):
        action = CmdRunAction(
            command='stress-ng --vm 4 --vm-bytes 1G --timeout 300s --metrics --verbose'
        )
        action.timeout = 600
        logger.info(action, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        # assert obs.exit_code == 0

    _close_test_runtime(runtime)
