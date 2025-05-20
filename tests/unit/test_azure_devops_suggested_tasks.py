import asyncio
import unittest
from unittest.mock import MagicMock, patch

from pydantic import SecretStr

from openhands.integrations.azure_devops.azure_devops_service import (
    AzureDevOpsServiceImpl,
)
from openhands.integrations.service_types import ProviderType, TaskType


class TestAzureDevOpsSuggestedTasks(unittest.TestCase):
    @patch('openhands.integrations.azure_devops.azure_devops_service.Connection')
    def test_get_suggested_tasks_issues(self, mock_connection):
        """Test getting suggested tasks for issues."""
        # Arrange
        user_id = 'test-user'
        token = SecretStr('test-token')

        # Mock the Work Item Tracking client
        mock_wit_client = MagicMock()

        # Mock the query_by_wiql method
        mock_wiql_result = MagicMock()
        mock_wiql_result.work_items = [MagicMock(id=1), MagicMock(id=2)]
        mock_wit_client.query_by_wiql.return_value = mock_wiql_result

        # Mock the get_work_item method
        mock_work_item1 = MagicMock()
        mock_work_item1.id = 1
        mock_work_item1.fields = {
            'System.TeamProject': 'TestProject',
            'System.Title': 'Test Issue 1',
        }

        mock_work_item2 = MagicMock()
        mock_work_item2.id = 2
        mock_work_item2.fields = {
            'System.TeamProject': 'TestProject',
            'System.Title': 'Test Issue 2',
        }

        mock_wit_client.get_work_item.side_effect = [mock_work_item1, mock_work_item2]

        # Mock the Git client
        mock_git_client = MagicMock()

        # Mock the get_repositories method
        mock_git_client.get_repositories.return_value = []

        # Set up the connection mock to return the clients
        mock_connection_instance = MagicMock()
        mock_connection_instance.clients.get_work_item_tracking_client.return_value = (
            mock_wit_client
        )
        mock_connection_instance.clients.get_git_client.return_value = mock_git_client
        mock_connection.return_value = mock_connection_instance

        # Act
        service = AzureDevOpsServiceImpl(user_id=user_id, token=token)
        tasks = asyncio.run(service.get_suggested_tasks())

        # Assert
        self.assertEqual(len(tasks), 2)

        self.assertEqual(tasks[0].git_provider, ProviderType.AZURE_DEVOPS)
        self.assertEqual(tasks[0].task_type, TaskType.OPEN_ISSUE)
        self.assertEqual(tasks[0].repo, 'TestProject')
        self.assertEqual(tasks[0].issue_number, 1)
        self.assertEqual(tasks[0].title, 'Test Issue 1')

        self.assertEqual(tasks[1].git_provider, ProviderType.AZURE_DEVOPS)
        self.assertEqual(tasks[1].task_type, TaskType.OPEN_ISSUE)
        self.assertEqual(tasks[1].repo, 'TestProject')
        self.assertEqual(tasks[1].issue_number, 2)
        self.assertEqual(tasks[1].title, 'Test Issue 2')

    @patch('openhands.integrations.azure_devops.azure_devops_service.Connection')
    def test_get_suggested_tasks_pull_requests(self, mock_connection):
        """Test getting suggested tasks for pull requests."""
        # Arrange
        user_id = 'test-user'
        token = SecretStr('test-token')

        # Mock the Work Item Tracking client
        mock_wit_client = MagicMock()

        # Mock the query_by_wiql method
        mock_wiql_result = MagicMock()
        mock_wiql_result.work_items = []
        mock_wit_client.query_by_wiql.return_value = mock_wiql_result

        # Mock the Git client
        mock_git_client = MagicMock()

        # Mock the get_repositories method
        mock_project = MagicMock()
        mock_project.name = 'TestProject'

        mock_repo = MagicMock()
        mock_repo.id = 'repo-id'
        mock_repo.name = 'test-repo'
        mock_repo.project = mock_project

        mock_git_client.get_repositories.return_value = [mock_repo]

        # Mock the get_pull_requests method
        mock_pr1 = MagicMock()
        mock_pr1.pull_request_id = 101
        mock_pr1.title = 'PR with merge conflicts'
        mock_pr1.merge_status = 'conflicts'

        mock_pr2 = MagicMock()
        mock_pr2.pull_request_id = 102
        mock_pr2.title = 'PR with failing checks'
        mock_pr2.merge_status = 'succeeded'

        mock_pr3 = MagicMock()
        mock_pr3.pull_request_id = 103
        mock_pr3.title = 'PR with unresolved comments'
        mock_pr3.merge_status = 'succeeded'

        mock_git_client.get_pull_requests.return_value = [mock_pr1, mock_pr2, mock_pr3]

        # Mock the get_pull_request_policy_evaluations method
        mock_policy_eval = MagicMock()
        mock_policy_eval.status = 'rejected'

        mock_git_client.get_pull_request_policy_evaluations.side_effect = [
            [],  # For PR1 (already has merge conflicts)
            [mock_policy_eval],  # For PR2 (failing checks)
            [],  # For PR3 (will check for unresolved comments)
        ]

        # Mock the get_threads method
        mock_thread = MagicMock()
        mock_thread.status = 'active'
        mock_thread.is_deleted = False

        mock_git_client.get_threads.side_effect = [
            [],  # For PR1 (already has merge conflicts)
            [],  # For PR2 (already has failing checks)
            [mock_thread],  # For PR3 (unresolved comments)
        ]

        # Set up the connection mock to return the clients
        mock_connection_instance = MagicMock()
        mock_connection_instance.clients.get_work_item_tracking_client.return_value = (
            mock_wit_client
        )
        mock_connection_instance.clients.get_git_client.return_value = mock_git_client
        mock_connection.return_value = mock_connection_instance

        # Act
        service = AzureDevOpsServiceImpl(user_id=user_id, token=token)
        tasks = asyncio.run(service.get_suggested_tasks())

        # Assert
        # We expect at least 1 task
        self.assertGreaterEqual(len(tasks), 1)

        # Verify that all tasks have the correct provider type
        for task in tasks:
            self.assertEqual(task.git_provider, ProviderType.AZURE_DEVOPS)
            self.assertEqual(task.repo, 'TestProject/test-repo')

            # Verify that the issue number is one of the expected values
            self.assertIn(task.issue_number, [101, 102, 103])

            # Verify that the task type is one of the expected types
            self.assertIn(
                task.task_type,
                [
                    TaskType.MERGE_CONFLICTS,
                    TaskType.FAILING_CHECKS,
                    TaskType.UNRESOLVED_COMMENTS,
                ],
            )


if __name__ == '__main__':
    unittest.main()
