"""Tests for the setup script."""

from unittest.mock import patch

from conftest import (
    _load_runtime,
)

from openhands.core.setup import initialize_repository_for_runtime
from openhands.events.action import FileReadAction, FileWriteAction
from openhands.events.observation import FileReadObservation, FileWriteObservation
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

    setup_script = '.openhands/setup.sh'
    write_obs = runtime.write(
        FileWriteAction(
            path=setup_script, content="#!/bin/bash\necho 'Hello World' >> README.md\n"
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

    setup_script = '.openhands/setup.sh'
    write_obs = runtime.write(
        FileWriteAction(
            path=setup_script,
            content="#!/bin/bash\nsleep 3 && echo 'Hello World' >> README.md\n",
        )
    )
    assert isinstance(write_obs, FileWriteObservation)

    # Run setup script
    runtime.maybe_run_setup_script()

    # Verify script was executed by checking output
    read_obs = runtime.read(FileReadAction(path='README.md'))
    assert isinstance(read_obs, FileReadObservation)
    assert read_obs.content == 'Hello World\n'


def test_maybe_run_setup_script_with_env_vars(temp_dir, runtime_cls, run_as_openhands):
    """Test that setup script can set environment variables that persist."""
    runtime, config = _load_runtime(
        temp_dir,
        runtime_cls,
        run_as_openhands,
    )

    # Create a setup script that sets environment variables
    setup_script = '.openhands/setup.sh'
    write_obs = runtime.write(
        FileWriteAction(
            path=setup_script,
            content="""#!/bin/bash
# Set environment variables
export TEST_ENV_VAR="test_value"
export PATH="$PATH:/custom/bin"
echo "Environment variables set"
""",
        )
    )
    assert isinstance(write_obs, FileWriteObservation)

    # Run setup script
    runtime.maybe_run_setup_script()

    # Verify environment variables were set by checking them in a command
    from openhands.events.action import CmdRunAction
    from openhands.events.observation import CmdOutputObservation

    # Check if TEST_ENV_VAR was set
    check_env_action = CmdRunAction('echo $TEST_ENV_VAR', blocking=True)
    check_env_obs = runtime.run_action(check_env_action)
    assert isinstance(check_env_obs, CmdOutputObservation)
    assert check_env_obs.exit_code == 0
    assert 'test_value' in check_env_obs.content

    # Check if PATH was updated
    check_path_action = CmdRunAction('echo $PATH | grep "/custom/bin"', blocking=True)
    check_path_obs = runtime.run_action(check_path_action)
    assert isinstance(check_path_obs, CmdOutputObservation)
    assert check_path_obs.exit_code == 0
    assert '/custom/bin' in check_path_obs.content


def test_maybe_run_setup_script_with_complex_script(
    temp_dir, runtime_cls, run_as_openhands
):
    """Test that complex setup scripts are handled properly."""
    runtime, config = _load_runtime(
        temp_dir,
        runtime_cls,
        run_as_openhands,
    )

    # Create a complex setup script similar to the one in the issue
    setup_script = '.openhands/setup.sh'
    write_obs = runtime.write(
        FileWriteAction(
            path=setup_script,
            content="""#!/bin/bash
set -e

echo "Setting up complex environment..."

# Set environment variables
export COMPLEX_TEST_VAR="complex_value"

# Create a file that indicates the script ran successfully
echo "Setup completed successfully" > setup_completed.txt

# Simulate a long-running process
for i in {1..5}; do
    echo "Processing step $i..."
    sleep 1
done

echo "Setup complete!"
""",
        )
    )
    assert isinstance(write_obs, FileWriteObservation)

    # Run setup script
    runtime.maybe_run_setup_script()

    # Verify script completed by checking for the output file
    from openhands.events.action import CmdRunAction, FileReadAction
    from openhands.events.observation import CmdOutputObservation, FileReadObservation

    read_obs = runtime.read(FileReadAction(path='setup_completed.txt'))
    assert isinstance(read_obs, FileReadObservation)
    assert 'Setup completed successfully' in read_obs.content

    # Check if environment variable was set
    check_env_action = CmdRunAction('echo $COMPLEX_TEST_VAR', blocking=True)
    check_env_obs = runtime.run_action(check_env_action)
    assert isinstance(check_env_obs, CmdOutputObservation)
    assert check_env_obs.exit_code == 0
    assert 'complex_value' in check_env_obs.content

    # Verify we can run additional commands after the setup script
    test_cmd_action = CmdRunAction('echo "Terminal is still responsive"', blocking=True)
    test_cmd_obs = runtime.run_action(test_cmd_action)
    assert isinstance(test_cmd_obs, CmdOutputObservation)
    assert test_cmd_obs.exit_code == 0
    assert 'Terminal is still responsive' in test_cmd_obs.content
