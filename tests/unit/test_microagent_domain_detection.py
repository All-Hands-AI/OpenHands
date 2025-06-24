"""Test microagent domain detection for different Git providers."""

from types import MappingProxyType

from pydantic import SecretStr

from openhands.integrations.provider import ProviderToken
from openhands.integrations.service_types import ProviderType


class MockRuntime:
    """Mock runtime class to test microagent domain detection logic."""

    def __init__(self, git_provider_tokens=None):
        self.git_provider_tokens = git_provider_tokens

    def get_microagents_from_org_or_user(self, selected_repository: str):
        """Simplified version of the microagent domain detection logic."""
        repo_parts = selected_repository.split('/')
        if len(repo_parts) < 2:
            return {}

        # Determine the provider and domain
        provider_domains = {
            ProviderType.GITHUB: 'github.com',
            ProviderType.GITLAB: 'gitlab.com',
            ProviderType.AZURE_DEVOPS: 'dev.azure.com',
        }

        # First, try to extract domain from repository name if it includes one
        if len(repo_parts) > 2:
            domain = repo_parts[0]
            provider = None
        else:
            # Repository name doesn't include domain (e.g., "org/repo")
            # Try to determine provider from available tokens
            domain = 'github.com'  # Default fallback
            provider = None

            if self.git_provider_tokens:
                # If we only have one provider token, use that
                if len(self.git_provider_tokens) == 1:
                    provider = next(iter(self.git_provider_tokens))
                    domain = provider_domains.get(provider, 'github.com')
                else:
                    # Multiple providers - would need additional logic to determine which one
                    # For now, default to GitHub
                    pass

        org_name = repo_parts[-2]

        # Construct the org-level .openhands repo path
        org_openhands_repo = f'{domain}/{org_name}/.openhands'

        return {
            'domain': domain,
            'provider': provider,
            'org_name': org_name,
            'org_openhands_repo': org_openhands_repo,
        }


class TestMicroagentDomainDetection:
    """Test cases for microagent domain detection across different Git providers."""

    def test_github_with_full_domain(self):
        """Test GitHub repository with full domain in name."""
        runtime = MockRuntime()
        result = runtime.get_microagents_from_org_or_user(
            'github.com/octocat/Hello-World'
        )

        assert result['domain'] == 'github.com'
        assert result['org_name'] == 'octocat'
        assert result['org_openhands_repo'] == 'github.com/octocat/.openhands'

    def test_gitlab_with_full_domain(self):
        """Test GitLab repository with full domain in name."""
        runtime = MockRuntime()
        result = runtime.get_microagents_from_org_or_user(
            'gitlab.com/gitlab-org/gitlab'
        )

        assert result['domain'] == 'gitlab.com'
        assert result['org_name'] == 'gitlab-org'
        assert result['org_openhands_repo'] == 'gitlab.com/gitlab-org/.openhands'

    def test_azure_devops_with_full_domain(self):
        """Test Azure DevOps repository with full domain in name."""
        runtime = MockRuntime()
        result = runtime.get_microagents_from_org_or_user(
            'dev.azure.com/myorg/myproject'
        )

        assert result['domain'] == 'dev.azure.com'
        assert result['org_name'] == 'myorg'
        assert result['org_openhands_repo'] == 'dev.azure.com/myorg/.openhands'

    def test_github_single_token_short_name(self):
        """Test GitHub repository with short name and single GitHub token."""
        github_token = ProviderToken(
            token=SecretStr('github_token_123'), user_id=None, host='github.com'
        )

        git_provider_tokens = MappingProxyType({ProviderType.GITHUB: github_token})

        runtime = MockRuntime(git_provider_tokens)
        result = runtime.get_microagents_from_org_or_user('octocat/Hello-World')

        assert result['domain'] == 'github.com'
        assert result['provider'] == ProviderType.GITHUB
        assert result['org_name'] == 'octocat'
        assert result['org_openhands_repo'] == 'github.com/octocat/.openhands'

    def test_gitlab_single_token_short_name(self):
        """Test GitLab repository with short name and single GitLab token."""
        gitlab_token = ProviderToken(
            token=SecretStr('gitlab_token_123'), user_id=None, host='gitlab.com'
        )

        git_provider_tokens = MappingProxyType({ProviderType.GITLAB: gitlab_token})

        runtime = MockRuntime(git_provider_tokens)
        result = runtime.get_microagents_from_org_or_user('gitlab-org/gitlab')

        assert result['domain'] == 'gitlab.com'
        assert result['provider'] == ProviderType.GITLAB
        assert result['org_name'] == 'gitlab-org'
        assert result['org_openhands_repo'] == 'gitlab.com/gitlab-org/.openhands'

    def test_azure_devops_single_token_short_name(self):
        """Test Azure DevOps repository with short name and single Azure DevOps token."""
        azure_token = ProviderToken(
            token=SecretStr('azure_token_123'),
            user_id=None,
            host='https://dev.azure.com/myorg',
        )

        git_provider_tokens = MappingProxyType({ProviderType.AZURE_DEVOPS: azure_token})

        runtime = MockRuntime(git_provider_tokens)
        result = runtime.get_microagents_from_org_or_user('myorg/myproject')

        assert result['domain'] == 'dev.azure.com'
        assert result['provider'] == ProviderType.AZURE_DEVOPS
        assert result['org_name'] == 'myorg'
        assert result['org_openhands_repo'] == 'dev.azure.com/myorg/.openhands'

    def test_multiple_tokens_defaults_to_github(self):
        """Test that with multiple tokens, it defaults to GitHub for short names."""
        github_token = ProviderToken(
            token=SecretStr('github_token_123'), user_id=None, host='github.com'
        )

        azure_token = ProviderToken(
            token=SecretStr('azure_token_123'),
            user_id=None,
            host='https://dev.azure.com/myorg',
        )

        git_provider_tokens = MappingProxyType(
            {ProviderType.GITHUB: github_token, ProviderType.AZURE_DEVOPS: azure_token}
        )

        runtime = MockRuntime(git_provider_tokens)
        result = runtime.get_microagents_from_org_or_user('someorg/somerepo')

        # With multiple tokens, should default to GitHub
        assert result['domain'] == 'github.com'
        assert result['provider'] is None  # No specific provider determined
        assert result['org_name'] == 'someorg'
        assert result['org_openhands_repo'] == 'github.com/someorg/.openhands'

    def test_no_tokens_defaults_to_github(self):
        """Test that without tokens, it defaults to GitHub for short names."""
        runtime = MockRuntime()
        result = runtime.get_microagents_from_org_or_user('someorg/somerepo')

        assert result['domain'] == 'github.com'
        assert result['provider'] is None
        assert result['org_name'] == 'someorg'
        assert result['org_openhands_repo'] == 'github.com/someorg/.openhands'

    def test_custom_gitlab_domain(self):
        """Test custom GitLab domain with full path."""
        runtime = MockRuntime()
        result = runtime.get_microagents_from_org_or_user(
            'gitlab.example.com/myorg/myproject'
        )

        assert result['domain'] == 'gitlab.example.com'
        assert result['org_name'] == 'myorg'
        assert result['org_openhands_repo'] == 'gitlab.example.com/myorg/.openhands'

    def test_custom_github_enterprise_domain(self):
        """Test custom GitHub Enterprise domain with full path."""
        runtime = MockRuntime()
        result = runtime.get_microagents_from_org_or_user(
            'github.enterprise.com/myorg/myproject'
        )

        assert result['domain'] == 'github.enterprise.com'
        assert result['org_name'] == 'myorg'
        assert result['org_openhands_repo'] == 'github.enterprise.com/myorg/.openhands'

    def test_invalid_repository_name(self):
        """Test invalid repository name with only one part."""
        runtime = MockRuntime()
        result = runtime.get_microagents_from_org_or_user('invalid')

        assert result == {}

    def test_deeply_nested_repository_path(self):
        """Test repository path with more than 3 parts."""
        runtime = MockRuntime()
        result = runtime.get_microagents_from_org_or_user(
            'github.com/org/subgroup/project'
        )

        assert result['domain'] == 'github.com'
        assert result['org_name'] == 'subgroup'  # Second to last part
        assert result['org_openhands_repo'] == 'github.com/subgroup/.openhands'

    def test_azure_devops_real_world_scenario(self):
        """Test real-world Azure DevOps scenario with actual token structure."""
        azure_token = ProviderToken(
            token=SecretStr('pat_token_value'),
            user_id=None,
            host='https://dev.azure.com/all-hands-ai',
        )

        git_provider_tokens = MappingProxyType({ProviderType.AZURE_DEVOPS: azure_token})

        runtime = MockRuntime(git_provider_tokens)
        result = runtime.get_microagents_from_org_or_user('test-project/test-project')

        assert result['domain'] == 'dev.azure.com'
        assert result['provider'] == ProviderType.AZURE_DEVOPS
        assert result['org_name'] == 'test-project'
        assert result['org_openhands_repo'] == 'dev.azure.com/test-project/.openhands'


if __name__ == '__main__':
    # Run tests if executed directly
    import sys

    test_class = TestMicroagentDomainDetection()
    test_methods = [method for method in dir(test_class) if method.startswith('test_')]

    passed = 0
    failed = 0

    for test_method in test_methods:
        try:
            print(f'Running {test_method}...')
            getattr(test_class, test_method)()
            print(f'✅ {test_method} passed')
            passed += 1
        except Exception as e:
            print(f'❌ {test_method} failed: {e}')
            failed += 1

    print(f'\nResults: {passed} passed, {failed} failed')

    if failed > 0:
        sys.exit(1)
    else:
        print('🎉 All tests passed!')
        sys.exit(0)
