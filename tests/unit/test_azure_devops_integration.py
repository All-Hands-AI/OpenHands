import unittest

from pydantic import SecretStr

from openhands.integrations.azure_devops.azure_devops_service import (
    AzureDevOpsServiceImpl,
)
from openhands.integrations.service_types import ProviderType, SuggestedTask, TaskType
from openhands.resolver.interfaces.azure_devops import (
    AzureDevOpsIssueHandler,
    AzureDevOpsPRHandler,
)


class TestAzureDevOpsIntegration(unittest.TestCase):
    def test_provider_type_enum(self):
        """Test that AZURE_DEVOPS is in the ProviderType enum."""
        self.assertIn(ProviderType.AZURE_DEVOPS, ProviderType)

    def test_suggested_task_provider_terms(self):
        """Test that Azure DevOps terms are included in SuggestedTask.get_provider_terms()."""
        # Create a SuggestedTask with AZURE_DEVOPS provider
        task = SuggestedTask(
            git_provider=ProviderType.AZURE_DEVOPS,
            task_type=TaskType.OPEN_ISSUE,
            repo='test-repo',
            issue_number=1,
            title='Test Issue',
        )
        terms = task.get_provider_terms()
        self.assertIn('work item', terms)
        self.assertIn('pull request', terms)
        self.assertIn('repository', terms)

    def test_azure_devops_service_impl_init(self):
        """Test AzureDevOpsServiceImpl initialization."""
        # Arrange
        user_id = 'test-user'
        token = SecretStr('test-token')

        # Act
        service = AzureDevOpsServiceImpl(user_id=user_id, token=token)

        # Assert
        self.assertEqual(service.user_id, user_id)
        self.assertEqual(service.token, token)
        self.assertEqual(service.provider, ProviderType.AZURE_DEVOPS.value)

    def test_azure_devops_issue_handler_init(self):
        """Test AzureDevOpsIssueHandler initialization."""
        # Arrange
        owner = 'test-org'
        repo = 'test-project/test-repo'
        token = 'test-token'
        username = 'test-user'

        # Act
        handler = AzureDevOpsIssueHandler(owner, repo, token, username)

        # Assert
        self.assertEqual(handler.owner, owner)
        self.assertEqual(handler.repo, repo)
        self.assertEqual(handler.token, token)
        self.assertEqual(handler.username, username)
        self.assertEqual(handler.project_name, 'test-project')
        self.assertEqual(handler.repo_name, 'test-repo')

    def test_azure_devops_pr_handler_init(self):
        """Test AzureDevOpsPRHandler initialization."""
        # Arrange
        owner = 'test-org'
        repo = 'test-project/test-repo'
        token = 'test-token'
        username = 'test-user'

        # Act
        handler = AzureDevOpsPRHandler(owner, repo, token, username)

        # Assert
        self.assertEqual(handler.owner, owner)
        self.assertEqual(handler.repo, repo)
        self.assertEqual(handler.token, token)
        self.assertEqual(handler.username, username)
        self.assertEqual(handler.project_name, 'test-project')
        self.assertEqual(handler.repo_name, 'test-repo')

    def test_azure_devops_issue_handler_get_base_url(self):
        """Test AzureDevOpsIssueHandler.get_base_url()."""
        # Arrange
        owner = 'test-org'
        repo = 'test-project/test-repo'
        token = 'test-token'
        username = 'test-user'
        handler = AzureDevOpsIssueHandler(owner, repo, token, username)

        # Act
        base_url = handler.get_base_url()

        # Assert
        expected_url = 'https://dev.azure.com/test-org/test-project/_apis/git/repositories/test-repo'
        self.assertEqual(base_url, expected_url)

    def test_azure_devops_issue_handler_get_clone_url(self):
        """Test AzureDevOpsIssueHandler.get_clone_url()."""
        # Arrange
        owner = 'test-org'
        repo = 'test-project/test-repo'
        token = 'test-token'
        username = 'test-user'
        handler = AzureDevOpsIssueHandler(owner, repo, token, username)

        # Act
        clone_url = handler.get_clone_url()

        # Assert
        expected_url = 'https://test-user:test-token@dev.azure.com/test-org/test-project/_git/test-repo'
        self.assertEqual(clone_url, expected_url)


if __name__ == '__main__':
    unittest.main()
