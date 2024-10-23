"""Env vars related tests for the EventStreamRuntime, which connects to the ActionExecutor running in the sandbox."""

import os
from unittest.mock import patch

from conftest import _close_test_runtime, _load_runtime

from openhands.events.action import CmdRunAction
from openhands.events.observation import CmdOutputObservation

# ============================================================================================================================
# Environment variables tests
# ============================================================================================================================


def test_env_vars_os_environ(temp_dir, box_class, run_as_openhands):
    with patch.dict(os.environ, {'SANDBOX_ENV_FOOBAR': 'BAZ'}):
        runtime = _load_runtime(temp_dir, box_class, run_as_openhands)

        obs: CmdOutputObservation = runtime.run_action(CmdRunAction(command='env'))
        print(obs)

        obs: CmdOutputObservation = runtime.run_action(
            CmdRunAction(command='echo $FOOBAR')
        )
        print(obs)
        assert obs.exit_code == 0, 'The exit code should be 0.'
        assert (
            obs.content.strip().split('\n\r')[0].strip() == 'BAZ'
        ), f'Output: [{obs.content}] for {box_class}'

        _close_test_runtime(runtime)


def test_env_vars_runtime_operations(temp_dir, box_class):
    runtime = _load_runtime(temp_dir, box_class)

    # Test adding single env var
    runtime.add_env_vars({'QUUX': 'abc"def'})
    obs = runtime.run_action(CmdRunAction(command='echo $QUUX'))
    assert (
        obs.exit_code == 0 and obs.content.strip().split('\r\n')[0].strip() == 'abc"def'
    )

    # Test adding multiple env vars
    runtime.add_env_vars({'FOOBAR': 'xyz'})
    obs = runtime.run_action(CmdRunAction(command='echo $QUUX $FOOBAR'))
    assert (
        obs.exit_code == 0
        and obs.content.strip().split('\r\n')[0].strip() == 'abc"def xyz'
    )

    # Test adding empty dict
    prev_env = runtime.run_action(CmdRunAction(command='env')).content
    runtime.add_env_vars({})
    current_env = runtime.run_action(CmdRunAction(command='env')).content
    assert prev_env == current_env

    # Test overwriting env vars
    runtime.add_env_vars({'QUUX': 'new_value'})
    obs = runtime.run_action(CmdRunAction(command='echo $QUUX'))
    assert (
        obs.exit_code == 0
        and obs.content.strip().split('\r\n')[0].strip() == 'new_value'
    )

    _close_test_runtime(runtime)


def test_env_vars_added_by_config(temp_dir, box_class):
    runtime = _load_runtime(
        temp_dir,
        box_class,
        runtime_startup_env_vars={'ADDED_ENV_VAR': 'added_value'},
    )

    # Test adding single env var
    obs = runtime.run_action(CmdRunAction(command='echo $ADDED_ENV_VAR'))
    assert (
        obs.exit_code == 0
        and obs.content.strip().split('\r\n')[0].strip() == 'added_value'
    )
    _close_test_runtime(runtime)
