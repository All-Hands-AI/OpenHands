"""Test for duplicate setup script execution."""

from conftest import _load_runtime

from openhands.events.action import FileWriteAction
from openhands.events.observation import FileWriteObservation


def test_setup_script_not_executed_multiple_times(
    temp_dir, runtime_cls, run_as_openhands
):
    """Test that setup script is not executed multiple times when called from different places."""
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)

    # Create a setup script that writes to a file with a counter
    setup_script = '.openhands/setup.sh'
    setup_content = """#!/bin/bash
# Create counter file if it doesn't exist
if [ ! -f /tmp/setup_counter ]; then
    echo "0" > /tmp/setup_counter
fi

# Read current counter, increment, and write back
counter=$(cat /tmp/setup_counter)
counter=$((counter + 1))
echo "$counter" > /tmp/setup_counter

# Output the execution count
echo "Setup script executed $counter time(s)"
"""

    write_obs = runtime.write(FileWriteAction(path=setup_script, content=setup_content))
    assert isinstance(write_obs, FileWriteObservation)

    # Get initial events count
    initial_events = list(runtime.event_stream.search_events())
    initial_event_count = len(initial_events)

    # Call maybe_run_setup_script multiple times (simulating different code paths)
    runtime.maybe_run_setup_script()
    runtime.maybe_run_setup_script()  # Second call should be a no-op

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
    assert setup_command_count == 1, (
        f'Setup script should only be executed once, but was executed {setup_command_count} times'
    )


def test_setup_script_flag_prevents_duplicate_execution(
    temp_dir, runtime_cls, run_as_openhands
):
    """Test that the _setup_script_executed flag prevents duplicate execution."""
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)

    # Create a simple setup script
    setup_script = '.openhands/setup.sh'
    setup_content = """#!/bin/bash
echo "Setup script executed"
"""

    write_obs = runtime.write(FileWriteAction(path=setup_script, content=setup_content))
    assert isinstance(write_obs, FileWriteObservation)

    # Verify the flag is initially False
    assert not runtime._setup_script_executed, (
        'Setup script flag should initially be False'
    )

    # Get initial events count
    initial_events = list(runtime.event_stream.search_events())
    initial_event_count = len(initial_events)

    # Call maybe_run_setup_script first time
    runtime.maybe_run_setup_script()

    # Verify the flag is now True
    assert runtime._setup_script_executed, (
        'Setup script flag should be True after execution'
    )

    # Call maybe_run_setup_script second time (should be a no-op)
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
    assert setup_command_count == 1, (
        f'Setup script should only be executed once, but was executed {setup_command_count} times'
    )
