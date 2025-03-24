import os

from openhands.utils.prompt import PromptManager


def test_system_prompt_contains_github_pr_instructions():
    """Test that the system prompt contains the GitHub pull request instructions."""
    # Create a PromptManager instance with the correct prompt directory
    prompt_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        'openhands/agenthub/codeact_agent/prompts',
    )
    prompt_manager = PromptManager(prompt_dir=prompt_dir)

    # Get the system prompt
    system_prompt = prompt_manager.get_system_message()

    # Check that the GitHub pull request instructions are in the system prompt
    assert '<GITHUB_PULL_REQUESTS>' in system_prompt
    assert 'Create only ONE pull request per session/issue' in system_prompt
    assert 'DO NOT create a new pull request for additional changes' in system_prompt
    assert 'commit those changes to the same branch' in system_prompt
    assert 'Preserve the original pull request title and purpose' in system_prompt


def test_github_microagent_contains_pr_instructions():
    """Test that the GitHub microagent contains the pull request instructions."""
    # Read the GitHub microagent file
    with open('/workspace/OpenHands/microagents/knowledge/github.md', 'r') as f:
        github_microagent_content = f.read()

    # Check that the GitHub pull request instructions are in the microagent
    assert 'Create only ONE pull request per session/issue' in github_microagent_content
    assert (
        'DO NOT create a new pull request for additional changes'
        in github_microagent_content
    )
    assert 'commit those changes to the same branch' in github_microagent_content
    assert (
        'Preserve the original pull request title and purpose'
        in github_microagent_content
    )
