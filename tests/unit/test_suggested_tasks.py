import pytest
from unittest.mock import AsyncMock, patch

from openhands.integrations.github.github_service import GitHubService
from openhands.integrations.github.github_types import GitHubUser, GitHubRepository, TaskType

@pytest.mark.asyncio
async def test_get_suggested_tasks():
    # Mock responses
    mock_user = GitHubUser(
        id=1,
        login="test-user",
        avatar_url="https://example.com/avatar.jpg",
        name="Test User"
    )

    mock_repos = [
        GitHubRepository(
            id=1,
            full_name="test-org/repo-1",
            stargazers_count=10
        ),
        GitHubRepository(
            id=2,
            full_name="test-user/repo-2",
            stargazers_count=5
        )
    ]

    # Mock GraphQL response for each repository
    mock_graphql_responses = [
        {
            "data": {
                "repository": {
                    "pullRequests": {
                        "nodes": [
                            {
                                "number": 1,
                                "title": "PR with conflicts",
                                "mergeable": "CONFLICTING",
                                "commits": {
                                    "nodes": [{"commit": {"statusCheckRollup": None}}]
                                },
                                "reviews": {"nodes": []}
                            },
                            {
                                "number": 2,
                                "title": "PR with failing checks",
                                "mergeable": "MERGEABLE",
                                "commits": {
                                    "nodes": [{"commit": {"statusCheckRollup": {"state": "FAILURE"}}}]
                                },
                                "reviews": {"nodes": []}
                            }
                        ]
                    },
                    "issues": {
                        "nodes": [
                            {
                                "number": 3,
                                "title": "Assigned issue 1"
                            }
                        ]
                    }
                }
            }
        },
        {
            "data": {
                "repository": {
                    "pullRequests": {
                        "nodes": [
                            {
                                "number": 4,
                                "title": "PR with comments",
                                "mergeable": "MERGEABLE",
                                "commits": {
                                    "nodes": [{"commit": {"statusCheckRollup": {"state": "SUCCESS"}}}]
                                },
                                "reviews": {
                                    "nodes": [{"state": "CHANGES_REQUESTED"}]
                                }
                            }
                        ]
                    },
                    "issues": {
                        "nodes": [
                            {
                                "number": 5,
                                "title": "Assigned issue 2"
                            }
                        ]
                    }
                }
            }
        }
    ]

    # Create service instance with mocked methods
    service = GitHubService()
    service.get_user = AsyncMock(return_value=mock_user)
    service.get_repositories = AsyncMock(return_value=mock_repos)
    service.execute_graphql_query = AsyncMock()
    service.execute_graphql_query.side_effect = mock_graphql_responses

    # Call the function
    tasks = await service.get_suggested_tasks()

    # Verify the results
    assert len(tasks) == 5  # Should have 5 tasks total

    # Verify each task type is present
    task_types = [task.task_type for task in tasks]
    assert TaskType.MERGE_CONFLICTS in task_types
    assert TaskType.FAILING_CHECKS in task_types
    assert TaskType.UNRESOLVED_COMMENTS in task_types
    assert TaskType.OPEN_ISSUE in task_types
    assert len([t for t in task_types if t == TaskType.OPEN_ISSUE]) == 2  # Should have 2 open issues

    # Verify repositories are correct
    repos = {task.repo for task in tasks}
    assert "test-org/repo-1" in repos
    assert "test-user/repo-2" in repos

    # Verify specific tasks
    conflict_pr = next(t for t in tasks if t.task_type == TaskType.MERGE_CONFLICTS)
    assert conflict_pr.issue_number == 1
    assert conflict_pr.title == "PR with conflicts"

    failing_pr = next(t for t in tasks if t.task_type == TaskType.FAILING_CHECKS)
    assert failing_pr.issue_number == 2
    assert failing_pr.title == "PR with failing checks"

    commented_pr = next(t for t in tasks if t.task_type == TaskType.UNRESOLVED_COMMENTS)
    assert commented_pr.issue_number == 4
    assert commented_pr.title == "PR with comments"