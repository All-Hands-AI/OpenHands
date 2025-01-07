"""Stress tests for the DockerRuntime, which connects to the ActionExecutor running in the sandbox."""

from conftest import _close_test_runtime, _load_runtime

from openhands.core.logger import openhands_logger as logger
from openhands.events.action import CmdRunAction


def test_stress_docker_runtime(temp_dir, runtime_cls, repeat=1):
    runtime = _load_runtime(
        temp_dir,
        runtime_cls,
        docker_runtime_kwargs={
            'cpu_period': 100000,  # 100ms
            'cpu_quota': 100000,  # Can use 100ms out of each 100ms period (1 CPU)
            'mem_limit': '4G',  # 4 GB of memory
        },
    )

    action = CmdRunAction(
        command='sudo apt-get update && sudo apt-get install -y stress-ng'
    )
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert obs.exit_code == 0

    for _ in range(repeat):
        # run stress-ng stress tests for 1 minute
        action = CmdRunAction(command='stress-ng --all 1 -t 1m')
        action.timeout = 120
        logger.info(action, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

    _close_test_runtime(runtime)
