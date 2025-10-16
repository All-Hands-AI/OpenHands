"""Test that agent instructions properly address pre-commit hooks.

This test ensures that the agent's instructions (microagents and system prompts)
explicitly mention NOT using --no-verify flag to ensure pre-commit hooks are executed.
"""

from pathlib import Path

import pytest


class TestPreCommitInstructions:
    """Test that agent instructions properly guide the agent to respect pre-commit hooks."""

    @pytest.fixture
    def microagents_dir(self) -> Path:
        """Get the microagents directory."""
        return Path(__file__).parent.parent.parent / 'microagents'

    @pytest.fixture
    def system_prompt_file(self) -> Path:
        """Get the system prompt file for CodeActAgent."""
        return (
            Path(__file__).parent.parent.parent
            / 'openhands'
            / 'agenthub'
            / 'codeact_agent'
            / 'prompts'
            / 'system_prompt.j2'
        )

    def test_github_microagent_mentions_no_verify(self, microagents_dir: Path):
        """Test that github.md microagent mentions not using --no-verify."""
        github_md = microagents_dir / 'github.md'
        assert github_md.exists(), 'github.md microagent file should exist'

        content = github_md.read_text()

        # Check that it mentions not using --no-verify
        assert '--no-verify' in content.lower(), (
            'github.md should mention --no-verify flag'
        )
        assert 'never' in content.lower() and '--no-verify' in content.lower(), (
            'github.md should instruct to NEVER use --no-verify'
        )
        assert 'pre-commit' in content.lower(), (
            'github.md should mention pre-commit hooks'
        )

    def test_gitlab_microagent_mentions_no_verify(self, microagents_dir: Path):
        """Test that gitlab.md microagent mentions not using --no-verify."""
        gitlab_md = microagents_dir / 'gitlab.md'
        assert gitlab_md.exists(), 'gitlab.md microagent file should exist'

        content = gitlab_md.read_text()

        # Check that it mentions not using --no-verify
        assert '--no-verify' in content.lower(), (
            'gitlab.md should mention --no-verify flag'
        )
        assert 'never' in content.lower() and '--no-verify' in content.lower(), (
            'gitlab.md should instruct to NEVER use --no-verify'
        )
        assert 'pre-commit' in content.lower(), (
            'gitlab.md should mention pre-commit hooks'
        )

    def test_bitbucket_microagent_mentions_no_verify(self, microagents_dir: Path):
        """Test that bitbucket.md microagent mentions not using --no-verify."""
        bitbucket_md = microagents_dir / 'bitbucket.md'
        assert bitbucket_md.exists(), 'bitbucket.md microagent file should exist'

        content = bitbucket_md.read_text()

        # Check that it mentions not using --no-verify
        assert '--no-verify' in content.lower(), (
            'bitbucket.md should mention --no-verify flag'
        )
        assert 'never' in content.lower() and '--no-verify' in content.lower(), (
            'bitbucket.md should instruct to NEVER use --no-verify'
        )
        assert 'pre-commit' in content.lower(), (
            'bitbucket.md should mention pre-commit hooks'
        )

    def test_system_prompt_mentions_no_verify(self, system_prompt_file: Path):
        """Test that system_prompt.j2 mentions not using --no-verify."""
        assert system_prompt_file.exists(), (
            'system_prompt.j2 file should exist for CodeActAgent'
        )

        content = system_prompt_file.read_text()

        # Check that it mentions not using --no-verify in VERSION_CONTROL section
        assert '--no-verify' in content.lower(), (
            'system_prompt.j2 should mention --no-verify flag'
        )
        assert 'never' in content.lower() and '--no-verify' in content.lower(), (
            'system_prompt.j2 should instruct to NEVER use --no-verify'
        )
        assert 'pre-commit' in content.lower(), (
            'system_prompt.j2 should mention pre-commit hooks'
        )

    def test_git_microagents_show_correct_commit_examples(self, microagents_dir: Path):
        """Test that git-related microagents show commit examples without --no-verify."""
        for microagent_file in ['github.md', 'gitlab.md', 'bitbucket.md']:
            file_path = microagents_dir / microagent_file
            content = file_path.read_text()

            # Find all code examples with git commit
            lines = content.split('\n')
            in_code_block = False
            for line in lines:
                if line.strip().startswith('```'):
                    in_code_block = not in_code_block
                elif in_code_block and 'git commit' in line:
                    # Ensure the example doesn't use --no-verify
                    assert '--no-verify' not in line.lower(), (
                        f'{microagent_file} should not show examples using '
                        f'--no-verify flag: {line}'
                    )
