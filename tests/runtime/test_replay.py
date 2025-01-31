"""Replay tests"""

import asyncio

from conftest import _close_test_runtime, _load_runtime

from openhands.controller.state.state import State
from openhands.core.config.app_config import AppConfig
from openhands.core.config.config_utils import OH_DEFAULT_AGENT
from openhands.core.main import run_controller
from openhands.core.schema.agent import AgentState
from openhands.events.action.empty import NullAction
from openhands.events.observation.commands import CmdOutputObservation


def _get_config(trajectory_name: str, agent: str = OH_DEFAULT_AGENT):
    return AppConfig(
        default_agent=agent,
        run_as_openhands=False,
        # do not mount workspace
        workspace_base=None,
        workspace_mount_path=None,
        replay_trajectory_path=f'./tests/runtime/trajs/{trajectory_name}.json',
    )


def test_simple_replay(temp_dir, runtime_cls, run_as_openhands):
    """
    A simple replay test that involves simple terminal operations and edits
    (creating a simple 2048 game), using the default agent
    """
    runtime = _load_runtime(temp_dir, runtime_cls, run_as_openhands)

    config = _get_config('basic')

    state: State | None = asyncio.run(
        run_controller(
            config=config,
            initial_user_action=NullAction(),
            runtime=runtime,
        )
    )

    assert state.agent_state == AgentState.FINISHED

    _close_test_runtime(runtime)


def test_replay_wrong_initial_state(temp_dir, runtime_cls, run_as_openhands):
    """
    Replay requires a consistent initial state to start with, otherwise it might
    be producing garbage. The trajectory used in this test assumes existence of
    a file named 'game_2048.py', which doesn't exist when we replay the trajectory
    (so called inconsistent initial states). This test demonstrates how this would
    look like: the following events would still be replayed even though they are
    meaningless.
    """
    runtime = _load_runtime(temp_dir, runtime_cls, run_as_openhands)

    config = _get_config('wrong_initial_state')

    state: State | None = asyncio.run(
        run_controller(
            config=config,
            initial_user_action=NullAction(),
            runtime=runtime,
        )
    )

    assert state.agent_state == AgentState.FINISHED

    has_error_in_action = False
    for event in state.history:
        if isinstance(event, CmdOutputObservation) and event.exit_code != 0:
            has_error_in_action = True
            break

    assert has_error_in_action

    _close_test_runtime(runtime)
