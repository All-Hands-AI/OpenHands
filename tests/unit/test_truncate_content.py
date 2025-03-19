from openhands.events.serialization.event import truncate_content


def test_truncate_content_no_truncation():
    """Test that truncate_content returns the original content when it's shorter than max_chars."""
    content = 'This is a short message'
    max_chars = 100
    result = truncate_content(content, max_chars)
    assert result == content


def test_truncate_content_none_max_chars():
    """Test that truncate_content returns the original content when max_chars is None."""
    content = 'This is a message of any length'
    result = truncate_content(content, None)
    assert result == content


def test_truncate_content_negative_max_chars():
    """Test that truncate_content returns the original content when max_chars is negative."""
    content = 'This is a message of any length'
    result = truncate_content(content, -1)
    assert result == content


def test_truncate_content_truncation():
    """Test that truncate_content truncates the middle of the content when it's longer than max_chars."""
    content = 'This is a very long message that should be truncated in the middle'
    max_chars = 20
    result = truncate_content(content, max_chars)

    # The result should be the first 10 chars + truncation message + last 10 chars
    expected_prefix = content[:10]
    expected_suffix = content[-10:]
    truncation_message = '\n[... Observation truncated due to length ...]\n'

    assert result.startswith(expected_prefix)
    assert result.endswith(expected_suffix)
    assert truncation_message in result
    assert len(result) == 10 + len(truncation_message) + 10


def test_truncate_content_exact_length():
    """Test that truncate_content doesn't truncate when content length equals max_chars."""
    content = 'Exact length'
    max_chars = len(content)
    result = truncate_content(content, max_chars)
    assert result == content


def test_truncate_content_with_agent_condensation_action():
    """Test that truncate_content works correctly with a long summary from AgentCondensationAction."""
    # Simulate a long summary that would come from an AgentCondensationAction
    long_summary = 'A' * 15000  # 15,000 characters
    max_chars = 10000  # The limit we want to enforce

    result = truncate_content(long_summary, max_chars)

    # Verify the result is truncated correctly
    assert len(result) < 15000
    assert '\n[... Observation truncated due to length ...]\n' in result

    # The result should be approximately max_chars in length
    # (half from beginning, half from end, plus the truncation message)
    truncation_message = '\n[... Observation truncated due to length ...]\n'
    expected_length = (max_chars // 2) * 2 + len(truncation_message)
    assert abs(len(result) - expected_length) <= 1  # Allow for rounding
