"""Replay tests"""

import asyncio
from pathlib import Path

from conftest import _close_test_runtime, _load_runtime

from openhands.controller.state.state import State
from openhands.core.config.config_utils import OH_DEFAULT_AGENT
from openhands.core.config.openhands_config import OpenHandsConfig
from openhands.core.main import run_controller
from openhands.core.schema.agent import AgentState
from openhands.events.action.empty import NullAction
from openhands.events.action.message import MessageAction
from openhands.events.event import EventSource
from openhands.events.observation.commands import CmdOutputObservation


def _get_config(trajectory_name: str, agent: str = OH_DEFAULT_AGENT):
    return OpenHandsConfig(
        default_agent=agent,
        run_as_openhands=False,
        # do not mount workspace
        workspace_base=None,
        workspace_mount_path=None,
        replay_trajectory_path=str(
            (Path(__file__).parent / 'trajs' / f'{trajectory_name}.json').resolve()
        ),
    )


def test_simple_replay(temp_dir, runtime_cls, run_as_openhands):
    """
    A simple replay test that involves simple terminal operations and edits
    (creating a simple 2048 game), using the default agent
    """
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    config.replay_trajectory_path = str(
        (Path(__file__).parent / 'trajs' / 'basic.json').resolve()
    )
    config.security.confirmation_mode = False

    state: State | None = asyncio.run(
        run_controller(
            config=config,
            initial_user_action=NullAction(),
            runtime=runtime,
        )
    )

    assert state.agent_state == AgentState.FINISHED

    _close_test_runtime(runtime)


def test_simple_gui_replay(temp_dir, runtime_cls, run_as_openhands):
    """
    A simple replay test that involves simple terminal operations and edits
    (writing a Vue.js App), using the default agent

    Note:
    1. This trajectory is exported from GUI mode, meaning it has extra
    environmental actions that don't appear in headless mode's trajectories
    2. In GUI mode, agents typically don't finish; rather, they wait for the next
    task from the user, so this exported trajectory ends with awaiting_user_input
    """
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)

    config = _get_config('basic_gui_mode')
    config.security.confirmation_mode = False

    state: State | None = asyncio.run(
        run_controller(
            config=config,
            initial_user_action=NullAction(),
            runtime=runtime,
            # exit on message, otherwise this would be stuck on waiting for user input
            exit_on_message=True,
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
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    config.replay_trajectory_path = str(
        (Path(__file__).parent / 'trajs' / 'wrong_initial_state.json').resolve()
    )
    config.security.confirmation_mode = False

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


def test_replay_basic_interactions(temp_dir, runtime_cls, run_as_openhands):
    """
    Replay a trajectory that involves interactions, i.e. with user messages
    in the middle. This tests two things:
    1) The controller should be able to replay all actions without human
    interference (no asking for user input).
    2) The user messages in the trajectory should appear in the history.
    """
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)

    config = _get_config('basic_interactions')
    config.security.confirmation_mode = False

    state: State | None = asyncio.run(
        run_controller(
            config=config,
            initial_user_action=NullAction(),
            runtime=runtime,
        )
    )

    assert state.agent_state == AgentState.FINISHED

    # all user messages appear in the history, so that after a replay (assuming
    # the trajectory doesn't end with `finish` action), LLM knows about all the
    # context and can continue
    user_messages = [
        "what's 1+1?",
        "No, I mean by Goldbach's conjecture!",
        'Finish please',
    ]
    i = 0
    for event in state.history:
        if isinstance(event, MessageAction) and event._source == EventSource.USER:
            assert event.message == user_messages[i]
            i += 1
    assert i == len(user_messages)

    _close_test_runtime(runtime)
