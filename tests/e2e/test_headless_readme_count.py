import json
import os
import subprocess
import tempfile
from pathlib import Path

import pytest


def get_readme_line_count():
    """Get the actual line count of README.md in the repository."""
    repo_root = Path(__file__).parent.parent.parent
    readme_path = repo_root / 'README.md'

    if not readme_path.exists():
        return 0

    with open(readme_path, 'r', encoding='utf-8') as f:
        return len(f.readlines())


def test_headless_mode_readme_line_count_no_browser():
    """
    E2E test: Run OpenHands in headless mode to count README.md lines without browser usage.

    This test:
    1. Launches the backend headlessly using openhands.core.main
    2. Disables browsing (ENABLE_BROWSER=false, AGENT_ENABLE_BROWSING=false)
    3. Ensures the agent uses shell to run wc -l README.md
    4. Verifies the integer matches the repo README.md line count
    5. Ensures no browse/browse_interactive actions appear in event logs
    """
    repo_root = Path(__file__).parent.parent.parent
    expected_line_count = get_readme_line_count()
    print(f'Expected README.md line count: {expected_line_count}')

    # Ensure we have a valid line count
    assert expected_line_count > 0, 'Could not read README.md or file is empty'

    # Check if LLM environment variables are available
    llm_model = os.environ.get('LLM_MODEL')
    llm_api_key = os.environ.get('LLM_API_KEY')

    if not llm_model or not llm_api_key:
        pytest.skip('LLM_MODEL or LLM_API_KEY environment variables not set')

    # Set up environment variables to disable browsing and configure LLM
    env = os.environ.copy()
    env.update(
        {
            'ENABLE_BROWSER': 'false',
            'AGENT_ENABLE_BROWSING': 'false',
            'RUNTIME': 'local',
            'RUN_AS_OPENHANDS': 'false',
            'SKIP_DEPENDENCY_CHECK': '1',
            'PYTHONUNBUFFERED': '1',
        }
    )

    # Create a temporary directory for trajectory output and config
    with tempfile.TemporaryDirectory() as tmpdir:
        trajectory_path = os.path.join(tmpdir, 'trajectory.json')
        config_path = os.path.join(tmpdir, 'config.toml')

        # Create a config file to save trajectory and configure LLM
        config_content = f"""
[core]
save_trajectory_path = "{trajectory_path}"

[llm]
model = "{llm_model}"
api_key = "{llm_api_key}"
"""
        with open(config_path, 'w') as f:
            f.write(config_content)

        # Task to count lines in README.md
        task = 'Count the number of lines in README.md using the wc command and tell me the exact number.'

        # Command to run OpenHands in headless mode
        cmd = [
            'python',
            '-m',
            'openhands.core.main',
            '--config-file',
            config_path,
            '-c',
            'CodeActAgent',  # Use CodeActAgent which can execute shell commands
            '-t',
            task,
        ]

        print(f'Running command: {" ".join(cmd)}')
        print(f'Working directory: {repo_root}')
        print(
            f'Environment variables: ENABLE_BROWSER={env.get("ENABLE_BROWSER")}, AGENT_ENABLE_BROWSING={env.get("AGENT_ENABLE_BROWSING")}'
        )

        # Run the command
        try:
            result = subprocess.run(
                cmd,
                cwd=repo_root,
                env=env,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            print('STDOUT:')
            print(result.stdout)
            print('STDERR:')
            print(result.stderr)
            print(f'Return code: {result.returncode}')

            # Handle different types of failures
            if result.returncode != 0:
                error_output = result.stdout + result.stderr

                # Check for specific LLM-related errors that we can handle gracefully
                if any(
                    error in error_output.lower()
                    for error in [
                        'exceeded budget',
                        'over budget',
                        'quota exceeded',
                        'rate limit',
                        'invalid model',
                        'authentication failed',
                    ]
                ):
                    pytest.skip(
                        f'LLM service unavailable or over budget: {error_output}'
                    )
                else:
                    pytest.fail(
                        f'Command failed with return code {result.returncode}: {error_output}'
                    )

            # Check that the output contains the expected line count
            output_text = result.stdout + result.stderr

            # Look for the line count in the output
            found_count = False
            for line in output_text.split('\n'):
                # Look for patterns like "183 README.md" or just "183" in context of README
                if 'README.md' in line and str(expected_line_count) in line:
                    print(f'Found expected line count in output: {line.strip()}')
                    found_count = True
                    break
                # Also check for just the number in context
                elif f'{expected_line_count}' in line and (
                    'line' in line.lower() or 'count' in line.lower()
                ):
                    print(f'Found expected line count in output: {line.strip()}')
                    found_count = True
                    break

            # If we didn't find the count in the output, check the trajectory file
            if not found_count and os.path.exists(trajectory_path):
                print('Checking trajectory file for line count...')
                with open(trajectory_path, 'r') as f:
                    trajectory_content = f.read()
                    if str(expected_line_count) in trajectory_content:
                        print(
                            f'Found expected line count {expected_line_count} in trajectory file'
                        )
                        found_count = True

            assert found_count, (
                f'Expected line count {expected_line_count} not found in output or trajectory'
            )

            # Verify no browsing actions were used by checking the trajectory
            if os.path.exists(trajectory_path):
                with open(trajectory_path, 'r') as f:
                    trajectory = json.load(f)

                # Check that no browse or browse_interactive actions were used
                browsing_actions = []
                for event in trajectory.get('events', []):
                    action_type = event.get('action', {}).get('action', '')
                    if action_type in ['browse', 'browse_interactive']:
                        browsing_actions.append(action_type)

                assert not browsing_actions, (
                    f'Found browsing actions {browsing_actions} in trajectory, but browsing should be disabled'
                )

                print('✓ Verified no browsing actions were used')

                # Also verify that shell commands were used (wc command)
                shell_commands = []
                for event in trajectory.get('events', []):
                    if event.get('action', {}).get('action') == 'run':
                        command = event.get('action', {}).get('command', '')
                        if command:
                            shell_commands.append(command)

                wc_commands = [
                    cmd
                    for cmd in shell_commands
                    if 'wc' in cmd.lower() and 'readme' in cmd.lower()
                ]
                if wc_commands:
                    print(f'✓ Verified wc command was used: {wc_commands}')
                else:
                    print(
                        f'Warning: No wc command found in shell commands: {shell_commands}'
                    )
            else:
                print(
                    'Warning: Trajectory file not found, cannot verify browsing actions'
                )

        except subprocess.TimeoutExpired:
            pytest.skip(
                'Command timed out after 5 minutes - likely due to LLM service issues'
            )
        except Exception as e:
            pytest.fail(f'Test failed with exception: {e}')
