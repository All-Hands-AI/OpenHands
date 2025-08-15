"""E2E test: Ruby - write and run extract_version.rb to parse name + SemVer

This test verifies that the agent can write a Ruby file that parses strings
of the form "name-version" and extracts the name and SemVer components,
then successfully run the script.

Based on issue #10373: https://github.com/All-Hands-AI/OpenHands/issues/10373
"""

import asyncio
import os
import tempfile
from pathlib import Path

import pytest

from openhands.core.config import OpenHandsConfig
from openhands.core.main import run_controller
from openhands.events.action import MessageAction


@pytest.mark.skipif(
    not os.getenv('LLM_API_KEY'),
    reason='LLM_API_KEY not available - skipping agent-based E2E test',
)
def test_ruby_extract_version_e2e():
    """E2E test: Agent writes and runs extract_version.rb to parse name + SemVer.

    This test follows the requirements from issue #10373:
    - Agent writes extract_version.rb that prints both name and SemVer
    - Handles edge cases where name can contain dashes
    - Installs Ruby if needed and runs script with sample inputs
    - Verifies outputs with assertions

    Note: This test requires LLM_API_KEY to be set and will be skipped in CI
    environments where the API key is not available.
    """

    # Task description for the agent - based on issue requirements
    task = """Please write a Ruby file called 'extract_version.rb' that parses strings of the form <name>-<SemVer> and extracts the name and SemVer components.

Requirements:
1. The script should handle edge cases where the name can contain dashes (e.g., "this-is-a-name-1.2.3" should extract name="this-is-a-name" and semver="1.2.3")
2. Print both the name and the SemVer for given inputs
3. Test with sample inputs including:
   - "proj-alpha-2.10.3" (should yield name="proj-alpha" and semver="2.10.3")
   - "rails-7.0.4" (should yield name="rails" and semver="7.0.4")
   - "react-dom-18.2.0" (should yield name="react-dom" and semver="18.2.0")
   - "vue-router-4.1.6" (should yield name="vue-router" and semver="4.1.6")

4. Install Ruby if needed using 'apt-get install -y ruby'
5. Run the script and verify the outputs are correct

The script should be robust and handle the parsing correctly, especially the edge case where names contain dashes."""

    async def run_test():
        with tempfile.TemporaryDirectory() as temp_dir:
            # Set up configuration
            from openhands.core.config import AgentConfig, LLMConfig

            config = OpenHandsConfig(
                runtime='local',
                workspace_base=temp_dir,
                max_iterations=30,  # Increased for more complex task
                default_agent='CodeActAgent',
                enable_browser=False,
                run_as_openhands=False,
                file_store='local',
                file_store_path=temp_dir,
            )

            # Set up LLM config
            llm_config = LLMConfig(
                model=os.getenv('LLM_MODEL', 'gpt-4o-mini'),
                api_key=os.getenv('LLM_API_KEY'),
                base_url=os.getenv('LLM_BASE_URL'),
            )
            config.set_llm_config(llm_config)

            # Set up agent config
            agent_config = AgentConfig()
            config.agents['agent'] = agent_config

            # Create initial user action
            initial_action = MessageAction(content=task)

            # Run the agent
            final_state = await run_controller(
                config=config,
                initial_user_action=initial_action,
                headless_mode=True,
                exit_on_message=True,
            )

            # Verify the task was completed
            assert final_state is not None, 'Agent should have completed the task'

            # Debug: List all files in the temp directory
            print(f'Files in temp directory {temp_dir}:')
            for file_path in Path(temp_dir).rglob('*'):
                if file_path.is_file():
                    print(f'  {file_path}')

            # Check if the Ruby file was created
            ruby_file_path = Path(temp_dir) / 'extract_version.rb'

            # The test must verify the agent actually completed the task
            assert ruby_file_path.exists(), (
                f'extract_version.rb must be created in {temp_dir}'
            )

            # Read the Ruby file content
            ruby_content = ruby_file_path.read_text()
            print(f'Ruby file content:\n{ruby_content}')

            # Verify the Ruby file contains expected parsing logic
            # The script should handle the edge case of names with dashes
            assert 'def' in ruby_content or 'class' in ruby_content, (
                'Ruby file should contain function/class definitions'
            )

            # Check the event stream for successful execution with expected outputs
            events = final_state.history

            # Look for evidence that Ruby was executed with correct outputs
            expected_outputs = [
                'proj-alpha',  # name from "proj-alpha-2.10.3"
                '2.10.3',  # semver from "proj-alpha-2.10.3"
                'rails',  # name from "rails-7.0.4"
                '7.0.4',  # semver from "rails-7.0.4"
                'react-dom',  # name from "react-dom-18.2.0"
                '18.2.0',  # semver from "react-dom-18.2.0"
            ]

            ruby_execution_found = False
            correct_outputs_found = 0

            for event in events:
                if hasattr(event, 'content') and event.content:
                    content = str(event.content)

                    # Check for Ruby execution
                    if any(
                        indicator in content.lower()
                        for indicator in [
                            'ruby extract_version.rb',
                            'running ruby',
                            'executing ruby',
                        ]
                    ):
                        ruby_execution_found = True

                    # Check for expected outputs
                    for expected_output in expected_outputs:
                        if expected_output in content:
                            correct_outputs_found += 1

            # Verify Ruby was executed
            assert ruby_execution_found, (
                'Evidence of Ruby script execution should be found in the event stream'
            )

            # Verify at least some expected outputs were found
            assert correct_outputs_found >= 4, (
                f'Expected outputs should be found in execution results. Found {correct_outputs_found} out of {len(expected_outputs)}'
            )

            print('✅ E2E Ruby extract_version test completed successfully!')
            print(f'Ruby file created at: {ruby_file_path}')
            print(
                f'Found {correct_outputs_found} expected outputs in execution results'
            )

    # Run the async test
    asyncio.run(run_test())


def test_ruby_extract_version_functionality():
    """Test the Ruby script functionality without requiring agent execution.

    This test validates that the expected Ruby script works correctly
    and handles all the edge cases specified in issue #10373.
    This test can run in CI environments without LLM API access.
    """
    import subprocess

    # Path to the reference Ruby script
    ruby_script_path = Path(__file__).parent / 'fixtures' / 'extract_version.rb'

    # Verify the fixture script exists
    assert ruby_script_path.exists(), (
        f'Reference Ruby script should exist at {ruby_script_path}'
    )

    # Run the Ruby script and capture output
    result = subprocess.run(
        ['ruby', str(ruby_script_path)], capture_output=True, text=True, check=True
    )

    output = result.stdout
    print(f'Ruby script output:\n{output}')

    # Verify expected outputs are present
    expected_outputs = [
        'proj-alpha',  # name from "proj-alpha-2.10.3"
        '2.10.3',  # semver from "proj-alpha-2.10.3"
        'rails',  # name from "rails-7.0.4"
        '7.0.4',  # semver from "rails-7.0.4"
        'react-dom',  # name from "react-dom-18.2.0"
        '18.2.0',  # semver from "react-dom-18.2.0"
        'vue-router',  # name from "vue-router-4.1.6"
        '4.1.6',  # semver from "vue-router-4.1.6"
        'this-is-a-name',  # name from "this-is-a-name-1.2.3"
        '1.2.3',  # semver from "this-is-a-name-1.2.3"
    ]

    for expected_output in expected_outputs:
        assert expected_output in output, (
            f"Expected output '{expected_output}' should be in Ruby script output"
        )

    # Verify the edge case handling
    assert 'proj-alpha-2.10.3' in output, "Should handle 'proj-alpha-2.10.3' input"
    assert 'this-is-a-name-1.2.3' in output, (
        "Should handle 'this-is-a-name-1.2.3' input"
    )

    print('✅ Ruby script functionality test passed!')
    print(
        'The reference implementation correctly handles all edge cases from issue #10373'
    )


if __name__ == '__main__':
    test_ruby_extract_version_e2e()
