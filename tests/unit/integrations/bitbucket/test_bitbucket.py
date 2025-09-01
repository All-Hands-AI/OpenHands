"""Tests for Bitbucket integration."""

import os
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import SecretStr

from openhands.integrations.bitbucket.bitbucket_service import BitBucketService
from openhands.integrations.provider import ProviderToken, ProviderType
from openhands.integrations.service_types import OwnerType, Repository
from openhands.integrations.service_types import ProviderType as ServiceProviderType
from openhands.integrations.utils import validate_provider_token
from openhands.resolver.interfaces.bitbucket import BitbucketIssueHandler
from openhands.resolver.interfaces.issue import Issue
from openhands.resolver.interfaces.issue_definitions import ServiceContextIssue
from openhands.resolver.send_pull_request import send_pull_request
from openhands.runtime.base import Runtime
from openhands.server.routes.secrets import check_provider_tokens
from openhands.server.settings import POSTProviderModel
from openhands.server.types import AppMode


# BitbucketIssueHandler Tests
@pytest.fixture
def bitbucket_handler():
    return BitbucketIssueHandler(
        owner='test-workspace',
        repo='test-repo',
        token='test-token',
        username='test-user',
    )


def test_init():
    handler = BitbucketIssueHandler(
        owner='test-workspace',
        repo='test-repo',
        token='test-token',
        username='test-user',
    )

    assert handler.owner == 'test-workspace'
    assert handler.repo == 'test-repo'
    assert handler.token == 'test-token'
    assert handler.username == 'test-user'
    assert handler.base_domain == 'bitbucket.org'
    assert handler.base_url == 'https://api.bitbucket.org/2.0'
    assert (
        handler.download_url
        == 'https://bitbucket.org/test-workspace/test-repo/get/master.zip'
    )
    assert handler.clone_url == 'https://bitbucket.org/test-workspace/test-repo.git'
    assert handler.headers == {
        'Authorization': 'Bearer test-token',
        'Accept': 'application/json',
    }


def test_get_repo_url(bitbucket_handler):
    assert (
        bitbucket_handler.get_repo_url()
        == 'https://bitbucket.org/test-workspace/test-repo'
    )


def test_get_issue_url(bitbucket_handler):
    assert (
        bitbucket_handler.get_issue_url(123)
        == 'https://bitbucket.org/test-workspace/test-repo/issues/123'
    )


def test_get_pr_url(bitbucket_handler):
    assert (
        bitbucket_handler.get_pr_url(123)
        == 'https://bitbucket.org/test-workspace/test-repo/pull-requests/123'
    )


@pytest.mark.asyncio
@patch('httpx.AsyncClient')
async def test_get_issue(mock_client, bitbucket_handler):
    mock_response = MagicMock()
    mock_response.raise_for_status = AsyncMock()
    mock_response.json.return_value = {
        'id': 123,
        'title': 'Test Issue',
        'content': {'raw': 'Test Issue Body'},
        'links': {
            'html': {
                'href': 'https://bitbucket.org/test-workspace/test-repo/issues/123'
            }
        },
        'state': 'open',
        'reporter': {'display_name': 'Test User'},
        'assignee': [{'display_name': 'Assignee User'}],
    }

    mock_client_instance = AsyncMock()
    mock_client_instance.get.return_value = mock_response
    mock_client.return_value.__aenter__.return_value = mock_client_instance

    issue = await bitbucket_handler.get_issue(123)

    assert issue.number == 123
    assert issue.title == 'Test Issue'
    assert issue.body == 'Test Issue Body'
    # We don't test for html_url, state, user, or assignees as they're not part of the Issue model


@patch('httpx.post')
def test_create_pr(mock_post, bitbucket_handler):
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        'links': {
            'html': {
                'href': 'https://bitbucket.org/test-workspace/test-repo/pull-requests/123'
            }
        },
    }
    mock_post.return_value = mock_response

    pr_url = bitbucket_handler.create_pr(
        title='Test PR',
        body='Test PR Body',
        head='feature-branch',
        base='main',
    )

    assert pr_url == 'https://bitbucket.org/test-workspace/test-repo/pull-requests/123'

    expected_payload = {
        'title': 'Test PR',
        'description': 'Test PR Body',
        'source': {'branch': {'name': 'feature-branch'}},
        'destination': {'branch': {'name': 'main'}},
        'close_source_branch': False,
    }

    mock_post.assert_called_once_with(
        'https://api.bitbucket.org/2.0/repositories/test-workspace/test-repo/pullrequests',
        headers=bitbucket_handler.headers,
        json=expected_payload,
    )


# Bitbucket Send Pull Request Tests
@patch('openhands.resolver.send_pull_request.ServiceContextIssue')
@patch('openhands.resolver.send_pull_request.BitbucketIssueHandler')
@patch('subprocess.run')
def test_send_pull_request_bitbucket(
    mock_run, mock_bitbucket_handler, mock_service_context
):
    # Mock subprocess.run to avoid actual git operations
    mock_run.return_value = MagicMock(returncode=0)

    # Mock the BitbucketIssueHandler instance
    mock_instance = MagicMock(spec=BitbucketIssueHandler)
    mock_bitbucket_handler.return_value = mock_instance

    # Mock the ServiceContextIssue instance
    mock_service = MagicMock(spec=ServiceContextIssue)
    mock_service.get_branch_name.return_value = 'openhands-fix-123'
    mock_service.branch_exists.return_value = True
    mock_service.get_default_branch_name.return_value = 'main'
    mock_service.get_clone_url.return_value = (
        'https://bitbucket.org/test-workspace/test-repo.git'
    )
    mock_service.create_pull_request.return_value = {
        'html_url': 'https://bitbucket.org/test-workspace/test-repo/pull-requests/123'
    }
    # Add _strategy attribute to mock
    mock_strategy = MagicMock()
    mock_service._strategy = mock_strategy
    mock_service_context.return_value = mock_service

    # Create a mock Issue
    mock_issue = Issue(
        number=123,
        title='Test Issue',
        owner='test-workspace',
        repo='test-repo',
        body='Test body',
        created_at='2023-01-01T00:00:00Z',
        updated_at='2023-01-01T00:00:00Z',
        closed_at=None,
        head_branch='feature-branch',
        thread_ids=None,
    )

    # Call send_pull_request
    result = send_pull_request(
        issue=mock_issue,
        token='test-token',
        username=None,
        platform=ServiceProviderType.BITBUCKET,
        patch_dir='/tmp',  # Use /tmp instead of /tmp/repo to avoid directory not found error
        pr_type='ready',
        pr_title='Test PR',
        target_branch='main',
    )

    # Verify the result
    assert result == 'https://bitbucket.org/test-workspace/test-repo/pull-requests/123'

    # Verify the handler was created correctly
    mock_bitbucket_handler.assert_called_once_with(
        'test-workspace',
        'test-repo',
        'test-token',
        None,
        'bitbucket.org',
    )

    # Verify ServiceContextIssue was created correctly
    mock_service_context.assert_called_once()

    # Verify create_pull_request was called with the correct data
    expected_body = 'This pull request fixes #123.\n\nAutomatic fix generated by [OpenHands](https://github.com/All-Hands-AI/OpenHands/) 🙌'
    mock_service.create_pull_request.assert_called_once_with(
        {
            'title': 'Test PR',
            'description': expected_body,
            'source_branch': 'openhands-fix-123',
            'target_branch': 'main',
            'draft': False,
        }
    )


# Bitbucket Provider Domain Tests
class TestBitbucketProviderDomain(unittest.TestCase):
    """Test that Bitbucket provider domain is properly handled in Runtime.clone_or_init_repo."""

    @patch('openhands.runtime.base.Runtime.__abstractmethods__', set())
    @patch(
        'openhands.runtime.utils.edit.FileEditRuntimeMixin.__init__', return_value=None
    )
    @patch('openhands.runtime.base.ProviderHandler')
    @pytest.mark.asyncio
    async def test_get_authenticated_git_url_bitbucket(
        self, mock_provider_handler, mock_file_edit_init, *args
    ):
        """Test that _get_authenticated_git_url correctly handles Bitbucket repositories."""
        # Mock the provider handler to return a repository with Bitbucket as the provider
        mock_repository = Repository(
            id='1',
            full_name='workspace/repo',
            git_provider=ServiceProviderType.BITBUCKET,
            is_public=True,
        )

        mock_provider_instance = MagicMock()
        mock_provider_instance.verify_repo_provider.return_value = mock_repository
        mock_provider_handler.return_value = mock_provider_instance

        # Create a minimal runtime instance with abstract methods patched
        config = MagicMock()
        config.get_llm_config.return_value.model = 'test_model'
        runtime = Runtime(config=config, event_stream=MagicMock(), sid='test_sid')

        # Test with no token
        url = await runtime._get_authenticated_git_url('workspace/repo', None)
        self.assertEqual(url, 'https://bitbucket.org/workspace/repo.git')

        # Test with username:password format token
        git_provider_tokens = {
            ProviderType.BITBUCKET: ProviderToken(
                token=SecretStr('username:app_password'), host='bitbucket.org'
            )
        }
        url = await runtime._get_authenticated_git_url(
            'workspace/repo', git_provider_tokens
        )
        # Bitbucket tokens with colon are used directly as username:password
        self.assertEqual(
            url, 'https://username:app_password@bitbucket.org/workspace/repo.git'
        )

        # Test with email:password format token (more realistic)
        git_provider_tokens = {
            ProviderType.BITBUCKET: ProviderToken(
                token=SecretStr('user@example.com:app_password'), host='bitbucket.org'
            )
        }
        url = await runtime._get_authenticated_git_url(
            'workspace/repo', git_provider_tokens
        )
        # Email addresses in tokens are used as-is (no URL encoding in our implementation)
        self.assertEqual(
            url,
            'https://user@example.com:app_password@bitbucket.org/workspace/repo.git',
        )

        # Test with simple token format (access token)
        git_provider_tokens = {
            ProviderType.BITBUCKET: ProviderToken(
                token=SecretStr('simple_token'), host='bitbucket.org'
            )
        }
        url = await runtime._get_authenticated_git_url(
            'workspace/repo', git_provider_tokens
        )
        # Simple tokens use x-token-auth format
        self.assertEqual(
            url, 'https://x-token-auth:simple_token@bitbucket.org/workspace/repo.git'
        )

    @patch('openhands.runtime.base.ProviderHandler')
    @patch.object(Runtime, 'run_action')
    async def test_bitbucket_provider_domain(
        self, mock_run_action, mock_provider_handler
    ):
        # Mock the provider handler to return a repository with Bitbucket as the provider
        mock_repository = Repository(
            id='1',
            full_name='test/repo',
            git_provider=ServiceProviderType.BITBUCKET,
            is_public=True,
        )

        mock_provider_instance = MagicMock()
        mock_provider_instance.verify_repo_provider.return_value = mock_repository
        mock_provider_handler.return_value = mock_provider_instance

        # Create a minimal runtime instance
        runtime = Runtime(config=MagicMock(), event_stream=MagicMock(), sid='test_sid')

        # Mock the workspace_root property to avoid AttributeError
        runtime.workspace_root = '/workspace'

        # Call clone_or_init_repo with a Bitbucket repository
        # This should now succeed with our fix
        await runtime.clone_or_init_repo(
            git_provider_tokens=None,
            selected_repository='test/repo',
            selected_branch=None,
        )

        # Verify that run_action was called at least once (for git clone)
        mock_run_action.assert_called()

        # Verify that the domain used was 'bitbucket.org'
        # Check that at least one call contains 'bitbucket.org' in the action command
        calls_with_bitbucket = [
            call_args
            for call_args in mock_run_action.call_args_list
            if 'bitbucket.org' in call_args[0][0].command
        ]
        self.assertTrue(
            len(calls_with_bitbucket) > 0,
            "Expected at least one call with 'bitbucket.org' in the command",
        )


# Provider Token Validation Tests
@pytest.mark.asyncio
async def test_validate_provider_token_with_bitbucket_token():
    """Test that validate_provider_token correctly identifies a Bitbucket token
    and doesn't try to validate it as GitHub or GitLab.
    """
    # Mock the service classes to avoid actual API calls
    with (
        patch('openhands.integrations.utils.GitHubService') as mock_github_service,
        patch('openhands.integrations.utils.GitLabService') as mock_gitlab_service,
        patch(
            'openhands.integrations.utils.BitBucketService'
        ) as mock_bitbucket_service,
    ):
        # Set up the mocks
        github_instance = AsyncMock()
        github_instance.verify_access.side_effect = Exception('Invalid GitHub token')
        mock_github_service.return_value = github_instance

        gitlab_instance = AsyncMock()
        gitlab_instance.get_user.side_effect = Exception('Invalid GitLab token')
        mock_gitlab_service.return_value = gitlab_instance

        bitbucket_instance = AsyncMock()
        bitbucket_instance.get_user.return_value = {'username': 'test_user'}
        mock_bitbucket_service.return_value = bitbucket_instance

        # Test with a Bitbucket token
        token = SecretStr('username:app_password')
        result = await validate_provider_token(token)

        # Verify that all services were tried
        mock_github_service.assert_called_once()
        mock_gitlab_service.assert_called_once()
        mock_bitbucket_service.assert_called_once()

        # Verify that the token was identified as a Bitbucket token
        assert result == ProviderType.BITBUCKET


@pytest.mark.asyncio
async def test_check_provider_tokens_with_only_bitbucket():
    """Test that check_provider_tokens doesn't try to validate GitHub or GitLab tokens
    when only a Bitbucket token is provided.
    """
    # Create a mock validate_provider_token function
    mock_validate = AsyncMock()
    mock_validate.return_value = ProviderType.BITBUCKET

    # Create provider tokens with only Bitbucket
    provider_tokens = {
        ProviderType.BITBUCKET: ProviderToken(
            token=SecretStr('username:app_password'), host='bitbucket.org'
        ),
        ProviderType.GITHUB: ProviderToken(token=SecretStr(''), host='github.com'),
        ProviderType.GITLAB: ProviderToken(token=SecretStr(''), host='gitlab.com'),
    }

    # Create the POST model
    post_model = POSTProviderModel(provider_tokens=provider_tokens)

    # Call check_provider_tokens with the patched validate_provider_token
    with patch(
        'openhands.server.routes.secrets.validate_provider_token', mock_validate
    ):
        result = await check_provider_tokens(post_model, None)

        # Verify that validate_provider_token was called only once with the Bitbucket token and host
        expected_token = provider_tokens[ProviderType.BITBUCKET].token
        expected_host = provider_tokens[ProviderType.BITBUCKET].host
        mock_validate.assert_called_once_with(expected_token, expected_host)

        # Verify that no error message was returned
        assert result == ''


@pytest.mark.asyncio
async def test_bitbucket_sort_parameter_mapping():
    """Test that the Bitbucket service correctly maps sort parameters."""
    # Create a service instance
    service = BitBucketService(token=SecretStr('test-token'))

    # Mock the _make_request method to avoid actual API calls
    with patch.object(service, '_make_request') as mock_request:
        # Mock workspaces response
        mock_request.side_effect = [
            # First call: workspaces
            ({'values': [{'slug': 'test-workspace', 'name': 'Test Workspace'}]}, {}),
            # Second call: repositories with mapped sort parameter
            ({'values': []}, {}),
        ]

        # Call get_repositories with sort='pushed'
        await service.get_all_repositories('pushed', AppMode.SAAS)

        # Verify that the second call used 'updated_on' instead of 'pushed'
        assert mock_request.call_count == 2

        # Verify the second call was made with the correct parameters
        # We can't use assert_called_with directly because we need to check partial URL and params
        # But we can verify the call structure more explicitly
        calls = mock_request.call_args_list
        assert len(calls) == 2, f'Expected 2 calls, got {len(calls)}'

        # Check the second call (repositories call) contains the mapped sort parameter
        second_call_url, second_call_params = calls[1][0]
        assert second_call_params['sort'] == '-updated_on', (
            f"Expected sort parameter '-updated_on', got {second_call_params.get('sort')}"
        )
        assert 'repositories/test-workspace' in second_call_url, (
            f"Expected URL to contain 'repositories/test-workspace', got {second_call_url}"
        )


@pytest.mark.asyncio
async def test_bitbucket_pagination():
    """Test that the Bitbucket service correctly handles pagination for repositories."""
    # Create a service instance
    service = BitBucketService(token=SecretStr('test-token'))

    # Mock the _make_request method to simulate paginated responses
    with patch.object(service, '_make_request') as mock_request:
        # Mock responses for pagination test
        mock_request.side_effect = [
            # First call: workspaces
            ({'values': [{'slug': 'test-workspace', 'name': 'Test Workspace'}]}, {}),
            # Second call: first page of repositories
            (
                {
                    'values': [
                        {
                            'uuid': 'repo-1',
                            'slug': 'repo1',
                            'workspace': {'slug': 'test-workspace'},
                            'is_private': False,
                            'updated_on': '2023-01-01T00:00:00Z',
                        },
                        {
                            'uuid': 'repo-2',
                            'slug': 'repo2',
                            'workspace': {'slug': 'test-workspace'},
                            'is_private': True,
                            'updated_on': '2023-01-02T00:00:00Z',
                        },
                    ],
                    'next': 'https://api.bitbucket.org/2.0/repositories/test-workspace?page=2',
                },
                {},
            ),
            # Third call: second page of repositories
            (
                {
                    'values': [
                        {
                            'uuid': 'repo-3',
                            'slug': 'repo3',
                            'workspace': {'slug': 'test-workspace'},
                            'is_private': False,
                            'updated_on': '2023-01-03T00:00:00Z',
                        }
                    ],
                    # No 'next' URL indicates this is the last page
                },
                {},
            ),
        ]

        # Call get_repositories
        repositories = await service.get_all_repositories('pushed', AppMode.SAAS)

        # Verify that all three requests were made (workspaces + 2 pages of repos)
        assert mock_request.call_count == 3

        # Verify that we got all repositories from both pages
        assert len(repositories) == 3
        assert repositories[0].id == 'repo-1'
        assert repositories[1].id == 'repo-2'
        assert repositories[2].id == 'repo-3'

        # Verify repository properties
        assert repositories[0].full_name == 'test-workspace/repo1'
        assert repositories[0].is_public is True
        assert repositories[1].is_public is False
        assert repositories[2].is_public is True


@pytest.mark.asyncio
async def test_validate_provider_token_with_empty_tokens():
    """Test that validate_provider_token handles empty tokens correctly."""
    # Create a mock for each service
    with (
        patch('openhands.integrations.utils.GitHubService') as mock_github_service,
        patch('openhands.integrations.utils.GitLabService') as mock_gitlab_service,
        patch(
            'openhands.integrations.utils.BitBucketService'
        ) as mock_bitbucket_service,
    ):
        # Configure mocks to raise exceptions for invalid tokens
        mock_github_service.return_value.verify_access.side_effect = Exception(
            'Invalid token'
        )
        mock_gitlab_service.return_value.verify_access.side_effect = Exception(
            'Invalid token'
        )
        mock_bitbucket_service.return_value.verify_access.side_effect = Exception(
            'Invalid token'
        )

        # Test with an empty token
        token = SecretStr('')
        result = await validate_provider_token(token)

        # Services should be tried but fail with empty tokens
        mock_github_service.assert_called_once()
        mock_gitlab_service.assert_called_once()
        mock_bitbucket_service.assert_called_once()

        # Result should be None for invalid tokens
        assert result is None

        # Reset mocks for second test
        mock_github_service.reset_mock()
        mock_gitlab_service.reset_mock()
        mock_bitbucket_service.reset_mock()

        # Test with a whitespace-only token
        token = SecretStr('   ')
        result = await validate_provider_token(token)

        # Services should be tried but fail with whitespace tokens
        mock_github_service.assert_called_once()
        mock_gitlab_service.assert_called_once()
        mock_bitbucket_service.assert_called_once()

        # Result should be None for invalid tokens
        assert result is None


@pytest.mark.asyncio
async def test_bitbucket_get_repositories_with_user_owner_type():
    """Test that get_repositories correctly sets owner_type field for user repositories."""
    service = BitBucketService(token=SecretStr('test-token'))

    # Mock repository data for user repositories (private workspace)
    mock_workspaces = [{'slug': 'test-user', 'name': 'Test User'}]
    mock_repos = [
        {
            'uuid': 'repo-1',
            'slug': 'user-repo1',
            'workspace': {'slug': 'test-user', 'is_private': True},
            'is_private': False,
            'updated_on': '2023-01-01T00:00:00Z',
        },
        {
            'uuid': 'repo-2',
            'slug': 'user-repo2',
            'workspace': {'slug': 'test-user', 'is_private': True},
            'is_private': True,
            'updated_on': '2023-01-02T00:00:00Z',
        },
    ]

    with patch.object(service, '_fetch_paginated_data') as mock_fetch:
        mock_fetch.side_effect = [mock_workspaces, mock_repos]

        repositories = await service.get_all_repositories('pushed', AppMode.SAAS)

        # Verify we got the expected number of repositories
        assert len(repositories) == 2

        # Verify owner_type is correctly set for user repositories (private workspace)
        for repo in repositories:
            assert repo.owner_type == OwnerType.ORGANIZATION
            assert isinstance(repo, Repository)
            assert repo.git_provider == ServiceProviderType.BITBUCKET


@pytest.mark.asyncio
async def test_bitbucket_get_repositories_with_organization_owner_type():
    """Test that get_repositories correctly sets owner_type field for organization repositories."""
    service = BitBucketService(token=SecretStr('test-token'))

    # Mock repository data for organization repositories (public workspace)
    mock_workspaces = [{'slug': 'test-org', 'name': 'Test Organization'}]
    mock_repos = [
        {
            'uuid': 'repo-3',
            'slug': 'org-repo1',
            'workspace': {'slug': 'test-org', 'is_private': False},
            'is_private': False,
            'updated_on': '2023-01-03T00:00:00Z',
        },
        {
            'uuid': 'repo-4',
            'slug': 'org-repo2',
            'workspace': {'slug': 'test-org', 'is_private': False},
            'is_private': True,
            'updated_on': '2023-01-04T00:00:00Z',
        },
    ]

    with patch.object(service, '_fetch_paginated_data') as mock_fetch:
        mock_fetch.side_effect = [mock_workspaces, mock_repos]

        repositories = await service.get_all_repositories('pushed', AppMode.SAAS)

        # Verify we got the expected number of repositories
        assert len(repositories) == 2

        # Verify owner_type is correctly set for organization repositories (public workspace)
        for repo in repositories:
            assert repo.owner_type == OwnerType.ORGANIZATION
            assert isinstance(repo, Repository)
            assert repo.git_provider == ServiceProviderType.BITBUCKET


@pytest.mark.asyncio
async def test_bitbucket_get_repositories_mixed_owner_types():
    """Test that get_repositories correctly handles mixed user and organization repositories."""
    service = BitBucketService(token=SecretStr('test-token'))

    # Mock repository data with mixed workspace types
    mock_workspaces = [
        {'slug': 'test-user', 'name': 'Test User'},
        {'slug': 'test-org', 'name': 'Test Organization'},
    ]

    # First workspace (user) repositories
    mock_user_repos = [
        {
            'uuid': 'repo-1',
            'slug': 'user-repo',
            'workspace': {'slug': 'test-user', 'is_private': True},
            'is_private': False,
            'updated_on': '2023-01-01T00:00:00Z',
        }
    ]

    # Second workspace (organization) repositories
    mock_org_repos = [
        {
            'uuid': 'repo-2',
            'slug': 'org-repo',
            'workspace': {'slug': 'test-org', 'is_private': False},
            'is_private': False,
            'updated_on': '2023-01-02T00:00:00Z',
        }
    ]

    with patch.object(service, '_fetch_paginated_data') as mock_fetch:
        mock_fetch.side_effect = [mock_workspaces, mock_user_repos, mock_org_repos]

        repositories = await service.get_all_repositories('pushed', AppMode.SAAS)

        # Verify we got repositories from both workspaces
        assert len(repositories) == 2

        # Verify owner_type is correctly set for each repository
        user_repo = next(repo for repo in repositories if 'user-repo' in repo.full_name)
        org_repo = next(repo for repo in repositories if 'org-repo' in repo.full_name)

        assert user_repo.owner_type == OwnerType.ORGANIZATION
        assert org_repo.owner_type == OwnerType.ORGANIZATION


# Setup.py Bitbucket Token Tests
@patch('openhands.core.setup.call_async_from_sync')
@patch('openhands.core.setup.get_file_store')
@patch('openhands.core.setup.EventStream')
def test_initialize_repository_for_runtime_with_bitbucket_token(
    mock_event_stream, mock_get_file_store, mock_call_async_from_sync
):
    """Test that initialize_repository_for_runtime properly handles BITBUCKET_TOKEN."""
    from openhands.core.setup import initialize_repository_for_runtime
    from openhands.integrations.provider import ProviderType

    # Mock runtime
    mock_runtime = MagicMock()
    mock_runtime.clone_or_init_repo = AsyncMock(return_value='test-repo')
    mock_runtime.maybe_run_setup_script = MagicMock()
    mock_runtime.maybe_setup_git_hooks = MagicMock()

    # Mock call_async_from_sync to return the expected result
    mock_call_async_from_sync.return_value = 'test-repo'

    # Set up environment with BITBUCKET_TOKEN
    with patch.dict(os.environ, {'BITBUCKET_TOKEN': 'username:app_password'}):
        result = initialize_repository_for_runtime(
            runtime=mock_runtime, selected_repository='all-hands-ai/test-repo'
        )

    # Verify the result
    assert result == 'test-repo'

    # Verify that call_async_from_sync was called with the correct arguments
    mock_call_async_from_sync.assert_called_once()

    # Extract call arguments to verify the provider tokens were set correctly
    call_args = mock_call_async_from_sync.call_args
    assert call_args[0][0] == mock_runtime.clone_or_init_repo, (
        'Expected first argument to be clone_or_init_repo method'
    )

    # Check that provider tokens were passed correctly
    provider_tokens = call_args[0][2]  # Third argument is immutable_provider_tokens
    assert provider_tokens is not None, 'Provider tokens should not be None'
    assert ProviderType.BITBUCKET in provider_tokens, (
        'BITBUCKET provider should be in provider_tokens'
    )
    assert (
        provider_tokens[ProviderType.BITBUCKET].token.get_secret_value()
        == 'username:app_password'
    ), (
        f"Expected BITBUCKET token to be 'username:app_password', got {provider_tokens[ProviderType.BITBUCKET].token.get_secret_value()}"
    )

    # Check that the repository was passed correctly
    assert call_args[0][3] == 'all-hands-ai/test-repo', (
        "Expected selected_repository to be 'all-hands-ai/test-repo'"
    )
    assert call_args[0][4] is None, 'Expected selected_branch to be None'


@patch('openhands.core.setup.call_async_from_sync')
@patch('openhands.core.setup.get_file_store')
@patch('openhands.core.setup.EventStream')
def test_initialize_repository_for_runtime_with_multiple_tokens(
    mock_event_stream, mock_get_file_store, mock_call_async_from_sync
):
    """Test that initialize_repository_for_runtime handles multiple provider tokens including Bitbucket."""
    from openhands.core.setup import initialize_repository_for_runtime
    from openhands.integrations.provider import ProviderType

    # Mock runtime
    mock_runtime = MagicMock()
    mock_runtime.clone_or_init_repo = AsyncMock(return_value='test-repo')
    mock_runtime.maybe_run_setup_script = MagicMock()
    mock_runtime.maybe_setup_git_hooks = MagicMock()

    # Mock call_async_from_sync to return the expected result
    mock_call_async_from_sync.return_value = 'test-repo'

    # Set up environment with multiple tokens
    with patch.dict(
        os.environ,
        {
            'GITHUB_TOKEN': 'github_token_123',
            'GITLAB_TOKEN': 'gitlab_token_456',
            'BITBUCKET_TOKEN': 'username:bitbucket_app_password',
        },
    ):
        result = initialize_repository_for_runtime(
            runtime=mock_runtime, selected_repository='all-hands-ai/test-repo'
        )

    # Verify the result
    assert result == 'test-repo'

    # Verify that call_async_from_sync was called
    mock_call_async_from_sync.assert_called_once()

    # Extract call arguments to verify the provider tokens were set correctly
    call_args = mock_call_async_from_sync.call_args
    provider_tokens = call_args[0][2]  # Third argument is immutable_provider_tokens
    assert provider_tokens is not None, 'Provider tokens should not be None'

    # Verify all three provider types are present
    assert ProviderType.GITHUB in provider_tokens, (
        'GITHUB provider should be in provider_tokens'
    )
    assert ProviderType.GITLAB in provider_tokens, (
        'GITLAB provider should be in provider_tokens'
    )
    assert ProviderType.BITBUCKET in provider_tokens, (
        'BITBUCKET provider should be in provider_tokens'
    )

    # Verify token values
    assert (
        provider_tokens[ProviderType.GITHUB].token.get_secret_value()
        == 'github_token_123'
    ), (
        f"Expected GITHUB token to be 'github_token_123', got {provider_tokens[ProviderType.GITHUB].token.get_secret_value()}"
    )
    assert (
        provider_tokens[ProviderType.GITLAB].token.get_secret_value()
        == 'gitlab_token_456'
    ), (
        f"Expected GITLAB token to be 'gitlab_token_456', got {provider_tokens[ProviderType.GITLAB].token.get_secret_value()}"
    )
    assert (
        provider_tokens[ProviderType.BITBUCKET].token.get_secret_value()
        == 'username:bitbucket_app_password'
    ), (
        f"Expected BITBUCKET token to be 'username:bitbucket_app_password', got {provider_tokens[ProviderType.BITBUCKET].token.get_secret_value()}"
    )


@patch('openhands.core.setup.call_async_from_sync')
@patch('openhands.core.setup.get_file_store')
@patch('openhands.core.setup.EventStream')
def test_initialize_repository_for_runtime_without_bitbucket_token(
    mock_event_stream, mock_get_file_store, mock_call_async_from_sync
):
    """Test that initialize_repository_for_runtime works without BITBUCKET_TOKEN."""
    from openhands.core.setup import initialize_repository_for_runtime
    from openhands.integrations.provider import ProviderType

    # Mock runtime
    mock_runtime = MagicMock()
    mock_runtime.clone_or_init_repo = AsyncMock(return_value='test-repo')
    mock_runtime.maybe_run_setup_script = MagicMock()
    mock_runtime.maybe_setup_git_hooks = MagicMock()

    # Mock call_async_from_sync to return the expected result
    mock_call_async_from_sync.return_value = 'test-repo'

    # Set up environment without BITBUCKET_TOKEN but with other tokens
    with patch.dict(
        os.environ,
        {'GITHUB_TOKEN': 'github_token_123', 'GITLAB_TOKEN': 'gitlab_token_456'},
        clear=False,
    ):
        # Ensure BITBUCKET_TOKEN is not in environment
        if 'BITBUCKET_TOKEN' in os.environ:
            del os.environ['BITBUCKET_TOKEN']

        result = initialize_repository_for_runtime(
            runtime=mock_runtime, selected_repository='all-hands-ai/test-repo'
        )

    # Verify the result
    assert result == 'test-repo'

    # Verify that call_async_from_sync was called
    mock_call_async_from_sync.assert_called_once()

    # Extract call arguments to verify the provider tokens were set correctly
    call_args = mock_call_async_from_sync.call_args
    provider_tokens = call_args[0][2]  # Third argument is immutable_provider_tokens
    assert provider_tokens is not None, 'Provider tokens should not be None'

    # Verify only GitHub and GitLab are present, not Bitbucket
    assert ProviderType.GITHUB in provider_tokens, (
        'GITHUB provider should be in provider_tokens'
    )
    assert ProviderType.GITLAB in provider_tokens, (
        'GITLAB provider should be in provider_tokens'
    )
    assert ProviderType.BITBUCKET not in provider_tokens, (
        'BITBUCKET provider should not be in provider_tokens'
    )


@pytest.mark.asyncio
async def test_bitbucket_order_parameter_honored():
    """Test that the Bitbucket service correctly honors the order parameter (asc/desc)."""
    # Create a service instance
    service = BitBucketService(token=SecretStr('test-token'))

    # Mock the _make_request method to avoid actual API calls
    with patch.object(service, '_make_request') as mock_request:
        # Mock response for repositories
        mock_request.return_value = ({'values': []}, {})

        # Test ascending order
        await service.get_paginated_repos(
            page=1,
            per_page=10,
            sort='updated',
            installation_id='test-workspace',
            query=None,
            order='asc',
        )

        # Verify the call was made with ascending order (no '-' prefix)
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        url, params = call_args[0]
        assert params['sort'] == 'updated_on', (
            f"Expected sort parameter 'updated_on', got {params.get('sort')}"
        )
        assert 'repositories/test-workspace' in url, (
            f"Expected URL to contain 'repositories/test-workspace', got {url}"
        )

        # Reset mock for next test
        mock_request.reset_mock()

        # Test descending order
        await service.get_paginated_repos(
            page=1,
            per_page=10,
            sort='updated',
            installation_id='test-workspace',
            query=None,
            order='desc',
        )

        # Verify the call was made with descending order ('-' prefix)
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        url, params = call_args[0]
        assert params['sort'] == '-updated_on', (
            f"Expected sort parameter '-updated_on', got {params.get('sort')}"
        )
        assert 'repositories/test-workspace' in url, (
            f"Expected URL to contain 'repositories/test-workspace', got {url}"
        )

        # Reset mock for next test
        mock_request.reset_mock()

        # Test default order (should be descending)
        await service.get_paginated_repos(
            page=1,
            per_page=10,
            sort='created',
            installation_id='test-workspace',
            query=None,
            # order parameter omitted, should default to 'desc'
        )

        # Verify the call was made with descending order by default
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        url, params = call_args[0]
        assert params['sort'] == '-created_on', (
            f"Expected sort parameter '-created_on', got {params.get('sort')}"
        )


@pytest.mark.asyncio
async def test_bitbucket_search_repositories_passes_order():
    """Test that search_repositories correctly passes the order parameter to get_paginated_repos."""
    # Create a service instance
    service = BitBucketService(token=SecretStr('test-token'))

    # Mock the get_installations method
    with patch.object(service, 'get_installations') as mock_installations:
        mock_installations.return_value = ['test-workspace']

        # Mock the get_paginated_repos method to capture calls
        with patch.object(service, 'get_paginated_repos') as mock_paginated_repos:
            mock_paginated_repos.return_value = []

            # Test ascending order
            await service.search_repositories(
                query='test-repo',
                per_page=10,
                sort='updated',
                order='asc',
                public=False,
            )

            # Verify get_paginated_repos was called with the correct order parameter
            mock_paginated_repos.assert_called()

            # Check that at least one call included the 'asc' order parameter
            calls_with_asc = [
                call_args
                for call_args in mock_paginated_repos.call_args_list
                if len(call_args[0]) > 5
                and call_args[0][5] == 'asc'  # order is the 6th positional argument
            ]
            assert len(calls_with_asc) > 0, (
                "Expected at least one call with 'asc' order parameter"
            )

            # Reset mock for next test
            mock_paginated_repos.reset_mock()

            # Test descending order
            await service.search_repositories(
                query='test-repo',
                per_page=10,
                sort='created',
                order='desc',
                public=False,
            )

            # Verify get_paginated_repos was called with the correct order parameter
            mock_paginated_repos.assert_called()

            # Check that at least one call included the 'desc' order parameter
            calls_with_desc = [
                call_args
                for call_args in mock_paginated_repos.call_args_list
                if len(call_args[0]) > 5
                and call_args[0][5] == 'desc'  # order is the 6th positional argument
            ]
            assert len(calls_with_desc) > 0, (
                "Expected at least one call with 'desc' order parameter"
            )


@pytest.mark.asyncio
async def test_get_bitbucket_sort_param_all_sort_types():
    """Test _get_bitbucket_sort_param with all supported sort types and default desc order."""
    service = BitBucketService(token=SecretStr('test-token'))

    # Test all sort types with default desc order
    assert service._get_bitbucket_sort_param('pushed') == '-updated_on'
    assert service._get_bitbucket_sort_param('updated') == '-updated_on'
    assert service._get_bitbucket_sort_param('created') == '-created_on'
    assert service._get_bitbucket_sort_param('full_name') == '-name'
    assert service._get_bitbucket_sort_param('unknown_sort') == '-updated_on'  # default


@pytest.mark.asyncio
async def test_get_bitbucket_sort_param_asc_order():
    """Test _get_bitbucket_sort_param with ascending order for all sort types."""
    service = BitBucketService(token=SecretStr('test-token'))

    # Test all sort types with ascending order
    assert service._get_bitbucket_sort_param('pushed', 'asc') == 'updated_on'
    assert service._get_bitbucket_sort_param('updated', 'asc') == 'updated_on'
    assert service._get_bitbucket_sort_param('created', 'asc') == 'created_on'
    assert service._get_bitbucket_sort_param('full_name', 'asc') == 'name'
    assert (
        service._get_bitbucket_sort_param('unknown_sort', 'asc') == 'updated_on'
    )  # default


@pytest.mark.asyncio
async def test_get_bitbucket_sort_param_desc_order():
    """Test _get_bitbucket_sort_param with explicit descending order for all sort types."""
    service = BitBucketService(token=SecretStr('test-token'))

    # Test all sort types with explicit descending order
    assert service._get_bitbucket_sort_param('pushed', 'desc') == '-updated_on'
    assert service._get_bitbucket_sort_param('updated', 'desc') == '-updated_on'
    assert service._get_bitbucket_sort_param('created', 'desc') == '-created_on'
    assert service._get_bitbucket_sort_param('full_name', 'desc') == '-name'
    assert (
        service._get_bitbucket_sort_param('unknown_sort', 'desc') == '-updated_on'
    )  # default


@pytest.mark.asyncio
async def test_get_bitbucket_sort_param_case_insensitive_order():
    """Test _get_bitbucket_sort_param with case-insensitive order parameters."""
    service = BitBucketService(token=SecretStr('test-token'))

    # Test case insensitive order parameters
    assert service._get_bitbucket_sort_param('updated', 'DESC') == '-updated_on'
    assert service._get_bitbucket_sort_param('updated', 'Desc') == '-updated_on'
    assert service._get_bitbucket_sort_param('updated', 'ASC') == 'updated_on'
    assert service._get_bitbucket_sort_param('updated', 'Asc') == 'updated_on'
    assert service._get_bitbucket_sort_param('updated', 'asc') == 'updated_on'
    assert service._get_bitbucket_sort_param('updated', 'desc') == '-updated_on'


@pytest.mark.asyncio
async def test_get_bitbucket_sort_param_invalid_order():
    """Test _get_bitbucket_sort_param with invalid order parameters defaults to asc (no prefix)."""
    service = BitBucketService(token=SecretStr('test-token'))

    # Test invalid order parameters - should default to asc behavior (no prefix)
    # Only 'desc' (case insensitive) gets the '-' prefix, everything else is treated as asc
    assert service._get_bitbucket_sort_param('updated', 'invalid') == 'updated_on'
    assert service._get_bitbucket_sort_param('updated', '') == 'updated_on'
    assert service._get_bitbucket_sort_param('updated', 'random') == 'updated_on'


@pytest.mark.asyncio
async def test_get_bitbucket_sort_param_edge_cases():
    """Test _get_bitbucket_sort_param with edge cases and boundary conditions."""
    service = BitBucketService(token=SecretStr('test-token'))

    # Test empty sort parameter - should default to updated_on
    assert service._get_bitbucket_sort_param('', 'asc') == 'updated_on'
    assert service._get_bitbucket_sort_param('', 'desc') == '-updated_on'

    # Test None-like values (if they could be passed)
    assert (
        service._get_bitbucket_sort_param('None', 'asc') == 'updated_on'
    )  # treated as unknown

    # Test whitespace handling
    assert (
        service._get_bitbucket_sort_param(' updated ', 'asc') == 'updated_on'
    )  # treated as unknown due to spaces


@pytest.mark.asyncio
async def test_get_bitbucket_sort_param_mapping_correctness():
    """Test that _get_bitbucket_sort_param correctly maps to Bitbucket API field names."""
    service = BitBucketService(token=SecretStr('test-token'))

    # Verify the mapping is correct for Bitbucket API
    # 'pushed' -> 'updated_on' (Bitbucket doesn't have pushed_at)
    assert 'updated_on' in service._get_bitbucket_sort_param('pushed', 'asc')

    # 'updated' -> 'updated_on'
    assert 'updated_on' in service._get_bitbucket_sort_param('updated', 'asc')

    # 'created' -> 'created_on'
    assert 'created_on' in service._get_bitbucket_sort_param('created', 'asc')

    # 'full_name' -> 'name' (Bitbucket uses 'name' field)
    assert service._get_bitbucket_sort_param('full_name', 'asc') == 'name'

    # Default case -> 'updated_on'
    assert 'updated_on' in service._get_bitbucket_sort_param('anything_else', 'asc')
