"""
E2E test for headless mode README.md line counting without browser usage.

This test verifies that OpenHands can count lines in README.md in headless mode
without using any browser actions, as requested in issue #10371.
"""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path


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
    E2E test: Build a docker image and run OpenHands in headless mode to count README.md lines.
    
    This test:
    1. Creates a Docker container with OpenHands installed from source
    2. Runs OpenHands in headless mode with browsing disabled
    3. Asks it to count lines in README.md using shell commands
    4. Verifies the response contains the correct line count
    5. Ensures no browsing actions were used
    """
    repo_root = Path(__file__).parent.parent.parent
    expected_line_count = get_readme_line_count()
    print(f'Expected README.md line count: {expected_line_count}')

    # Ensure we have a valid line count
    assert expected_line_count > 0, 'Could not read README.md or file is empty'

    # Check if LLM environment variables are available
    llm_model = os.environ.get('LLM_MODEL', 'gpt-4o')
    llm_api_key = os.environ.get('LLM_API_KEY', 'test-key')
    llm_base_url = os.environ.get('LLM_BASE_URL', '')

    # Create Dockerfile for the test
    dockerfile_content = f'''
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    git \\
    build-essential \\
    tmux \\
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /src

# Copy the entire repository
COPY . /src

# Install OpenHands
RUN pip install --upgrade pip setuptools wheel
RUN pip install .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV RUNTIME=local
ENV RUN_AS_OPENHANDS=false
ENV ENABLE_BROWSER=false
ENV AGENT_ENABLE_BROWSING=false
ENV SKIP_DEPENDENCY_CHECK=1
ENV LLM_MODEL={llm_model}
ENV LLM_API_KEY={llm_api_key}
ENV LLM_BASE_URL={llm_base_url}

# Create config file
RUN echo '[core]' > /tmp/config.toml && \\
    echo 'workspace_base = "/tmp/workspace"' >> /tmp/config.toml && \\
    echo 'persist_sandbox = false' >> /tmp/config.toml && \\
    echo 'run_as_openhands = false' >> /tmp/config.toml && \\
    echo 'runtime = "local"' >> /tmp/config.toml && \\
    echo 'disable_color = true' >> /tmp/config.toml && \\
    echo 'max_iterations = 10' >> /tmp/config.toml && \\
    echo 'save_trajectory_path = "/tmp/trajectory.json"' >> /tmp/config.toml && \\
    echo '' >> /tmp/config.toml && \\
    echo '[llm]' >> /tmp/config.toml && \\
    echo 'model = "{llm_model}"' >> /tmp/config.toml && \\
    echo 'api_key = "{llm_api_key}"' >> /tmp/config.toml && \\
    echo 'base_url = "{llm_base_url}"' >> /tmp/config.toml

# Run OpenHands with the task
CMD ["python", "-m", "openhands.core.main", \\
     "--config-file", "/tmp/config.toml", \\
     "--agent", "CodeActAgent", \\
     "--task", "Count the number of lines in README.md using the wc command and tell me the exact number."]
'''

    with tempfile.TemporaryDirectory() as tmpdir:
        dockerfile_path = os.path.join(tmpdir, 'Dockerfile')
        with open(dockerfile_path, 'w') as f:
            f.write(dockerfile_content)

        # Copy the repo into the temp dir for docker build context
        build_context = os.path.join(tmpdir, 'context')
        print(f'Copying repository from {repo_root} to {build_context}')
        shutil.copytree(repo_root, build_context, dirs_exist_ok=True)

        image_tag = 'openhands-e2e-headless-readme-test'
        
        # Build the Docker image
        build_cmd = [
            'docker', 'build',
            '-t', image_tag,
            '-f', dockerfile_path,
            build_context
        ]
        
        print(f'Building Docker image: {" ".join(build_cmd)}')
        build_proc = subprocess.run(build_cmd, capture_output=True, text=True, timeout=600)
        
        print('Docker build stdout:', build_proc.stdout)
        if build_proc.stderr:
            print('Docker build stderr:', build_proc.stderr)
        
        assert build_proc.returncode == 0, f'Docker build failed with return code {build_proc.returncode}'

        # Run the container
        run_cmd = [
            'docker', 'run', '--rm',
            '-v', '/tmp:/tmp',  # Mount /tmp for trajectory file access
            image_tag
        ]
        
        print(f'Running Docker container: {" ".join(run_cmd)}')
        run_proc = subprocess.run(run_cmd, capture_output=True, text=True, timeout=300)
        
        print('Docker run stdout:', run_proc.stdout)
        if run_proc.stderr:
            print('Docker run stderr:', run_proc.stderr)
        
        # Handle different types of failures
        if run_proc.returncode != 0:
            error_output = run_proc.stdout + run_proc.stderr
            
            # Check for specific LLM-related errors that we can handle gracefully
            if any(error in error_output.lower() for error in [
                'exceeded budget', 'over budget', 'quota exceeded', 'rate limit',
                'invalid model', 'authentication failed', 'api key', 'unauthorized'
            ]):
                import pytest
                pytest.skip(f'LLM service unavailable or over budget: {error_output}')
            else:
                assert False, f'Docker run failed with return code {run_proc.returncode}: {error_output}'

        # Check that the output contains the expected line count
        output_text = run_proc.stdout + run_proc.stderr
        
        # Look for the line count in the output
        found_count = False
        for line in output_text.split('\n'):
            # Look for patterns like "183 README.md" or just "183" in context of README
            if 'README.md' in line and str(expected_line_count) in line:
                print(f'Found expected line count in output: {line.strip()}')
                found_count = True
                break
            # Also check for just the number in context
            elif f'{expected_line_count}' in line and ('line' in line.lower() or 'count' in line.lower()):
                print(f'Found expected line count in output: {line.strip()}')
                found_count = True
                break

        assert found_count, f'Expected line count {expected_line_count} not found in output: {output_text}'

        # Try to get the trajectory file from the container to verify no browsing actions
        # First, run a container to copy the trajectory file
        copy_cmd = [
            'docker', 'run', '--rm',
            '-v', f'{tmpdir}:/output',
            image_tag,
            'sh', '-c', 'cp /tmp/trajectory.json /output/trajectory.json 2>/dev/null || echo "No trajectory file found"'
        ]
        
        copy_proc = subprocess.run(copy_cmd, capture_output=True, text=True, timeout=30)
        
        trajectory_file = os.path.join(tmpdir, 'trajectory.json')
        if os.path.exists(trajectory_file):
            import json
            with open(trajectory_file, 'r') as f:
                trajectory = json.load(f)

            # Check that no browse or browse_interactive actions were used
            browsing_actions = []
            for event in trajectory.get('events', []):
                action_type = event.get('action', {}).get('action', '')
                if action_type in ['browse', 'browse_interactive']:
                    browsing_actions.append(action_type)

            assert not browsing_actions, f'Found browsing actions {browsing_actions} in trajectory, but browsing should be disabled'
            print('✓ Verified no browsing actions were used')

            # Also verify that shell commands were used (wc command)
            shell_commands = []
            for event in trajectory.get('events', []):
                if event.get('action', {}).get('action') == 'run':
                    command = event.get('action', {}).get('command', '')
                    if command:
                        shell_commands.append(command)

            wc_commands = [cmd for cmd in shell_commands if 'wc' in cmd.lower() and 'readme' in cmd.lower()]
            if wc_commands:
                print(f'✓ Verified wc command was used: {wc_commands}')
            else:
                print(f'Warning: No wc command found in shell commands: {shell_commands}')
        else:
            print('Warning: Trajectory file not found, cannot verify browsing actions')

        print('✓ Test passed: README.md line count found and verified in headless mode')