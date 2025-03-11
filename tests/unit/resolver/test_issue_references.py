from openhands.resolver.utils import extract_issue_references


def test_extract_issue_references():
    # Test basic issue reference
    assert extract_issue_references('Fixes #123') == [123]

    # Test multiple issue references
    assert extract_issue_references('Fixes #123, #456') == [123, 456]

    # Test issue references in code blocks should be ignored
    assert extract_issue_references("""
    Here's a code block:
    ```python
    # This is a comment with #123
    def func():
        pass  # Another #456
    ```
    But this #789 should be extracted
    """) == [789]

    # Test issue references in inline code should be ignored
    assert extract_issue_references(
        'This `#123` should be ignored but #456 should be extracted'
    ) == [456]
    assert extract_issue_references(
        'This `#123` should be ignored but #456 should be extracted'
    ) == [456]

    # Test issue references in URLs should be ignored
    assert extract_issue_references(
        'Check http://example.com/#123 but #456 should be extracted'
    ) == [456]
    assert extract_issue_references(
        'Check http://example.com/#123 but #456 should be extracted'
    ) == [456]

    # Test issue references in markdown links should be extracted
    assert extract_issue_references('[Link to #123](http://example.com) and #456') == [
        123,
        456,
    ]
    assert extract_issue_references('[Link to #123](http://example.com) and #456') == [
        123,
        456,
    ]

    # Test issue references with text around them
    assert extract_issue_references('Issue #123 is fixed and #456 is pending') == [
        123,
        456,
    ]
    assert extract_issue_references('Issue #123 is fixed and #456 is pending') == [
        123,
        456,
    ]
