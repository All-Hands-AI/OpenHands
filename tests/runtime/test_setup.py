"""Tests for the setup script."""

from unittest.mock import patch

from conftest import (
    _load_runtime,
)

from openhands.core.setup import initialize_repository_for_runtime
from openhands.events.action import CmdRunAction, FileReadAction, FileWriteAction
from openhands.events.event import EventSource
from openhands.events.observation import (
    CmdOutputObservation,
    FileReadObservation,
    FileWriteObservation,
)
from openhands.integrations.service_types import ProviderType, Repository


def test_initialize_repository_for_runtime(temp_dir, runtime_cls, run_as_openhands):
    """Test that the initialize_repository_for_runtime function works."""
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    mock_repo = Repository(
        id='1232',
        full_name='All-Hands-AI/OpenHands',
        git_provider=ProviderType.GITHUB,
        is_public=True,
    )

    with patch(
        'openhands.runtime.base.ProviderHandler.verify_repo_provider',
        return_value=mock_repo,
    ):
        repository_dir = initialize_repository_for_runtime(
            runtime, selected_repository='All-Hands-AI/OpenHands'
        )

    assert repository_dir is not None
    assert repository_dir == 'OpenHands'


def test_maybe_run_setup_script(temp_dir, runtime_cls, run_as_openhands):
    """Test that setup script is executed when it exists."""
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)

    # Create an empty README.md file first to ensure we start with a clean state
    write_readme = runtime.write(
        FileWriteAction(
            path='README.md',
            content='',
        )
    )
    assert isinstance(write_readme, FileWriteObservation)

    setup_script = '.openhands/setup.sh'
    write_obs = runtime.write(
        FileWriteAction(
            path=setup_script, content="#!/bin/bash\necho 'Hello World' > README.md\n"
        )
    )
    assert isinstance(write_obs, FileWriteObservation)

    # Run setup script
    runtime.maybe_run_setup_script()

    # Verify script was executed by checking output
    read_obs = runtime.read(FileReadAction(path='README.md'))
    assert isinstance(read_obs, FileReadObservation)
    assert read_obs.content == 'Hello World\n'


def test_maybe_run_setup_script_with_long_timeout(
    temp_dir, runtime_cls, run_as_openhands
):
    """Test that setup script is executed when it exists."""
    runtime, config = _load_runtime(
        temp_dir,
        runtime_cls,
        run_as_openhands,
        runtime_startup_env_vars={'NO_CHANGE_TIMEOUT_SECONDS': '1'},
    )

    # Create an empty README.md file first to ensure we start with a clean state
    write_readme = runtime.write(
        FileWriteAction(
            path='README.md',
            content='',
        )
    )
    assert isinstance(write_readme, FileWriteObservation)

    setup_script = '.openhands/setup.sh'
    write_obs = runtime.write(
        FileWriteAction(
            path=setup_script,
            content="#!/bin/bash\nsleep 3 && echo 'Hello World' > README.md\n",
        )
    )
    assert isinstance(write_obs, FileWriteObservation)

    # Run setup script
    runtime.maybe_run_setup_script()

    # Verify script was executed by checking output
    read_obs = runtime.read(FileReadAction(path='README.md'))
    assert isinstance(read_obs, FileReadObservation)
    assert read_obs.content == 'Hello World\n'


def test_setup_script_events_added_to_stream(temp_dir, runtime_cls, run_as_openhands):
    """Test that setup script command and output are added to the event stream for UI visibility."""
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)

    setup_script = '.openhands/setup.sh'
    write_obs = runtime.write(
        FileWriteAction(
            path=setup_script,
            content="#!/bin/bash\necho 'Setup completed successfully'\n",
        )
    )
    assert isinstance(write_obs, FileWriteObservation)

    # Get initial events
    initial_events = list(runtime.event_stream.search_events())
    initial_event_count = len(initial_events)

    # Run setup script
    runtime.maybe_run_setup_script()

    # Get all events after running setup script
    all_events = list(runtime.event_stream.search_events())
    new_events = all_events[initial_event_count:]

    # Should have at least 2 new events: the action and the observation
    assert len(new_events) >= 2

    # Find the setup command action
    setup_action = None
    setup_observation = None

    for event in new_events:
        if (
            isinstance(event, CmdRunAction)
            and 'chmod +x .openhands/setup.sh && source .openhands/setup.sh'
            in event.command
        ):
            setup_action = event
        elif (
            isinstance(event, CmdOutputObservation)
            and hasattr(event, '_cause')
            and setup_action
            and event._cause == setup_action.id
        ):
            setup_observation = event

    # Verify the setup action was added to the event stream
    assert setup_action is not None, (
        'Setup command action should be added to event stream'
    )
    assert (
        setup_action.command
        == 'chmod +x .openhands/setup.sh && source .openhands/setup.sh'
    )
    assert (
        setup_action.thought
        == 'Running setup script to configure the workspace environment.'
    )
    assert setup_action.source == EventSource.ENVIRONMENT

    # Verify the setup observation was added to the event stream
    assert setup_observation is not None, (
        'Setup command observation should be added to event stream'
    )
    assert setup_observation.source == EventSource.ENVIRONMENT
    assert 'Setup completed successfully' in setup_observation.content


def test_setup_script_not_executed_multiple_times(
    temp_dir, runtime_cls, run_as_openhands
):
    """Test that setup script is not executed multiple times when called repeatedly."""
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)

    setup_script = '.openhands/setup.sh'
    write_obs = runtime.write(
        FileWriteAction(
            path=setup_script,
            content="#!/bin/bash\necho 'Setup completed successfully'\n",
        )
    )
    assert isinstance(write_obs, FileWriteObservation)

    # Verify the flag is initially False
    assert not runtime._setup_script_executed

    # Get initial events
    initial_events = list(runtime.event_stream.search_events())
    initial_event_count = len(initial_events)

    # Run setup script first time
    runtime.maybe_run_setup_script()

    # Verify the flag is now True
    assert runtime._setup_script_executed

    # Run setup script second time (should be a no-op)
    runtime.maybe_run_setup_script()

    # Get all events after running setup script
    all_events = list(runtime.event_stream.search_events())
    new_events = all_events[initial_event_count:]

    # Count how many times the setup command appears in the events
    setup_command_count = 0
    for event in new_events:
        if (
            hasattr(event, 'command')
            and 'chmod +x .openhands/setup.sh && source .openhands/setup.sh'
            in event.command
        ):
            setup_command_count += 1

    # The setup script should only be executed once, even if called multiple times
    assert setup_command_count == 1


def test_setup_script_failure_events_added_to_stream(
    temp_dir, runtime_cls, run_as_openhands
):
    """Test that setup script failure is properly shown in the event stream."""
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)

    setup_script = '.openhands/setup.sh'
    write_obs = runtime.write(
        FileWriteAction(
            path=setup_script, content="#!/bin/bash\necho 'Setup failed' && exit 1\n"
        )
    )
    assert isinstance(write_obs, FileWriteObservation)

    # Get initial events
    initial_events = list(runtime.event_stream.search_events())
    initial_event_count = len(initial_events)

    # Run setup script
    runtime.maybe_run_setup_script()

    # Get all events after running setup script
    all_events = list(runtime.event_stream.search_events())
    new_events = all_events[initial_event_count:]

    # Should have at least 2 new events: the action and the observation
    assert len(new_events) >= 2

    # Find the setup command action and observation
    setup_action = None
    setup_observation = None

    for event in new_events:
        if (
            isinstance(event, CmdRunAction)
            and 'chmod +x .openhands/setup.sh && source .openhands/setup.sh'
            in event.command
        ):
            setup_action = event
        elif (
            isinstance(event, CmdOutputObservation)
            and hasattr(event, '_cause')
            and setup_action
            and event._cause == setup_action.id
        ):
            setup_observation = event

    # Verify the setup action was added to the event stream
    assert setup_action is not None, (
        'Setup command action should be added to event stream'
    )
    assert setup_action.source == EventSource.ENVIRONMENT

    # Verify the setup observation was added to the event stream and shows failure
    assert setup_observation is not None, (
        'Setup command observation should be added to event stream'
    )
    assert setup_observation.source == EventSource.ENVIRONMENT
    assert setup_observation.exit_code != 0, 'Setup script should have failed'
    assert 'Setup failed' in setup_observation.content
