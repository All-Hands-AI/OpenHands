import pytest
from unittest.mock import MagicMock, patch
from openhands.resolver.issue_definitions import IssueHandler

@patch('openhands.resolver.issue_definitions.LLM')
def test_extract_issue_references(mock_llm):
    # Mock LLM since we don't need it for testing issue reference extraction
    handler = IssueHandler("owner", "repo", "token", MagicMock())
    
    # Test cases that should NOT match
    text_without_refs = """
    This is a regular text with no issue references.
    Here's a URL: https://github.com/org/repo/issues/123
    Here's a code block:
    ```
    Issue #456 should be ignored
    ```
    Here's inline code: `Issue #789`
    Here's a URL with hash: https://example.com/page#1234
    Here's a version number: v1.2.3
    """
    assert handler._extract_issue_references(text_without_refs) == []
    
    # Test cases that SHOULD match
    text_with_refs = """
    This PR fixes #123
    Related to #456 and closes #789
    See issue #101 for details
    This PR addresses #202
    References #303
    Fixes: #404
    Fixed #505
    Closes: #606
    Closed #707
    Resolves: #808
    Resolved #909
    """
    assert sorted(handler._extract_issue_references(text_with_refs)) == [101, 123, 202, 303, 404, 456, 505, 606, 707, 789, 808, 909]
    
    # Test edge cases
    edge_cases = """
    Fixes #1 at start of line
    Text fixes #2 in middle
    fixes#3without-space
    FIXES #4 uppercase
    FiXeD #5 mixed case
    fixes: #6 with colon
    fixes,#7 with comma
    fixes;#8 with semicolon
    fixes (#9) with parens
    fixes [#10] with brackets
    fixes{#11}with braces
    fixes #12, #13 and #14
    """
    assert sorted(handler._extract_issue_references(edge_cases)) == [1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
