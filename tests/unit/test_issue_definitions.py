import pytest
import responses
from openhands.resolver.issue_definitions import PRHandler
from openhands.core.config import LLMConfig

@pytest.fixture
def pr_handler():
    return PRHandler(
        owner="test-owner",
        repo="test-repo",
        token="test-token",
        llm_config=LLMConfig(model="test-model")
    )

@responses.activate
def test_get_converted_issues_fetches_specific_issues(pr_handler):
    # Mock the specific issue endpoint
    responses.add(
        responses.GET,
        "https://api.github.com/repos/test-owner/test-repo/issues/123",
        json={
            "number": 123,
            "title": "Test Issue",
            "body": "Test body",
            "state": "open",
            "head": {"ref": "test-branch"},
            "pull_request": {"url": "https://github.com/test-owner/test-repo/pull/123"}  # This makes it a PR
        },
        status=200
    )

    # Mock the PR metadata endpoint
    responses.add(
        responses.POST,
        "https://api.github.com/graphql",
        json={
            "data": {
                "repository": {
                    "pullRequest": {
                        "closingIssuesReferences": {"edges": []},
                        "url": "https://github.com/test-owner/test-repo/pull/123",
                        "reviews": {"nodes": []},
                        "reviewThreads": {"edges": []}
                    }
                }
            }
        },
        status=200
    )

    # Mock the PR comments endpoint
    responses.add(
        responses.GET,
        "https://api.github.com/repos/test-owner/test-repo/issues/123/comments",
        json=[],
        status=200
    )

    # Test fetching a specific issue
    issues = pr_handler.get_converted_issues(issue_numbers=[123])
    
    assert len(issues) == 1
    assert issues[0].number == 123
    assert issues[0].title == "Test Issue"

    # Print out all the requests that were made
    for i, call in enumerate(responses.calls):
        print(f"Request {i+1}: {call.request.method} {call.request.url}")

    # Verify that only the necessary requests were made
    assert len(responses.calls) == 3  # Issue, PR metadata, and PR comments
    assert "/issues/123" in responses.calls[0].request.url
