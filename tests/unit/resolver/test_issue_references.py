from openhands.core.config.llm_config import LLMConfig
from openhands.resolver.issue_definitions import IssueHandler


def test_extract_issue_references():
    llm_config = LLMConfig(model='test', api_key='test')
    handler = IssueHandler('test-owner', 'test-repo', 'test-token', llm_config)

    # Test basic issue reference
    assert handler._extract_issue_references('Fixes #123') == [123]

    # Test multiple issue references
    assert handler._extract_issue_references('Fixes #123, #456') == [123, 456]

    # Test issue references in code blocks should be ignored
    assert handler._extract_issue_references("""
    Here's a code block:
    ```python
    # This is a comment with #123
    def func():
        pass  # Another #456
    ```
    But this #789 should be extracted
    """) == [789]

    # Test issue references in inline code should be ignored
    assert handler._extract_issue_references(
        'This `#123` should be ignored but #456 should be extracted'
    ) == [456]

    # Test issue references in URLs should be ignored
    assert handler._extract_issue_references(
        'Check http://example.com/#123 but #456 should be extracted'
    ) == [456]

    # Test issue references in markdown links should be extracted
    assert handler._extract_issue_references(
        '[Link to #123](http://example.com) and #456'
    ) == [123, 456]

    # Test issue references with text around them
    assert handler._extract_issue_references(
        'Issue #123 is fixed and #456 is pending'
    ) == [123, 456]
