"""Env vars related tests for the EventStreamRuntime, which connects to the RuntimeClient running in the sandbox."""

import os
import time
from unittest.mock import patch

from conftest import _load_runtime

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

        runtime.close()
        time.sleep(1)


def test_env_vars_runtime_add_env_vars(temp_dir, box_class):
    runtime = _load_runtime(temp_dir, box_class)
    runtime.add_env_vars({'QUUX': 'abc"def'})

    obs: CmdOutputObservation = runtime.run_action(CmdRunAction(command='echo $QUUX'))
    print(obs)
    assert obs.exit_code == 0, 'The exit code should be 0.'
    assert (
        obs.content.strip().split('\r\n')[0].strip() == 'abc"def'
    ), f'Output: [{obs.content}] for {box_class}'

    runtime.close()
    time.sleep(1)


def test_env_vars_runtime_add_empty_dict(temp_dir, box_class):
    runtime = _load_runtime(temp_dir, box_class)

    prev_obs = runtime.run_action(CmdRunAction(command='env'))
    assert prev_obs.exit_code == 0, 'The exit code should be 0.'
    print(prev_obs)

    runtime.add_env_vars({})

    obs = runtime.run_action(CmdRunAction(command='env'))
    assert obs.exit_code == 0, 'The exit code should be 0.'
    print(obs)
    assert (
        obs.content == prev_obs.content
    ), 'The env var content should be the same after adding an empty dict.'

    runtime.close()
    time.sleep(1)


def test_env_vars_runtime_add_multiple_env_vars(temp_dir, box_class):
    runtime = _load_runtime(temp_dir, box_class)
    runtime.add_env_vars({'QUUX': 'abc"def', 'FOOBAR': 'xyz'})

    obs: CmdOutputObservation = runtime.run_action(
        CmdRunAction(command='echo $QUUX $FOOBAR')
    )
    print(obs)
    assert obs.exit_code == 0, 'The exit code should be 0.'
    assert (
        obs.content.strip().split('\r\n')[0].strip() == 'abc"def xyz'
    ), f'Output: [{obs.content}] for {box_class}'

    runtime.close()
    time.sleep(1)


def test_env_vars_runtime_add_env_vars_overwrite(temp_dir, box_class):
    with patch.dict(os.environ, {'SANDBOX_ENV_FOOBAR': 'BAZ'}):
        runtime = _load_runtime(temp_dir, box_class)
        runtime.add_env_vars({'FOOBAR': 'xyz'})

        obs: CmdOutputObservation = runtime.run_action(
            CmdRunAction(command='echo $FOOBAR')
        )
        print(obs)
        assert obs.exit_code == 0, 'The exit code should be 0.'
        assert (
            obs.content.strip().split('\r\n')[0].strip() == 'xyz'
        ), f'Output: [{obs.content}] for {box_class}'

        runtime.close()
        time.sleep(1)
