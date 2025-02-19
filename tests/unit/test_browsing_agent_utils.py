"""Tests for the browsing agent utils."""

import pytest

from openhands.agenthub.browsing_agent.utils import (
    ParseError,
    compress_string,
    extract_html_tags,
    parse_html_tags,
    parse_html_tags_raise,
    yaml_parser,
)


def test_yaml_parser_valid():
    """Test yaml_parser with valid input."""
    valid_yaml = """
    key1: value1
    key2: value2
    """
    value, valid, retry_message = yaml_parser(valid_yaml)
    assert valid is True
    assert value == {'key1': 'value1', 'key2': 'value2'}
    assert retry_message == ''


def test_yaml_parser_invalid():
    """Test yaml_parser with invalid input."""
    invalid_yaml = """
    key1: value1
    key2: : invalid : syntax :
    """
    value, valid, retry_message = yaml_parser(invalid_yaml)
    assert valid is False
    assert value == {}
    assert 'valid yaml' in retry_message.lower()


def test_compress_string():
    """Test string compression with redundant paragraphs and lines."""
    text = """
First paragraph
with multiple lines
that are unique.

Second paragraph
that repeats.

Third unique
paragraph here.

Second paragraph
that repeats.
"""
    result = compress_string(text)

    # Check that definitions section exists
    assert '<definitions>' in result
    assert '</definitions>' in result

    # Check that repeated content is replaced with identifiers
    definitions = extract_html_tags(result, ['definitions'])['definitions'][0]
    assert '§-0' in result  # Paragraph identifier
    assert 'Second paragraph' in definitions


def test_extract_html_tags_single():
    """Test extracting a single HTML tag."""
    text = '<test>Content</test>'
    result = extract_html_tags(text, ['test'])
    assert result == {'test': ['Content']}


def test_extract_html_tags_multiple():
    """Test extracting multiple HTML tags."""
    text = '<tag1>First</tag1><tag2>Second</tag2><tag1>Third</tag1>'
    result = extract_html_tags(text, ['tag1', 'tag2'])
    assert result == {'tag1': ['First', 'Third'], 'tag2': ['Second']}


def test_extract_html_tags_nested():
    """Test extracting nested HTML tags."""
    text = '<outer>Outside<inner>Inside</inner>End</outer>'
    result = extract_html_tags(text, ['outer', 'inner'])
    assert result == {'outer': ['Outside<inner>Inside</inner>End'], 'inner': ['Inside']}


def test_parse_html_tags_basic():
    """Test basic HTML tag parsing."""
    text = '<required>Content</required><optional>Extra</optional>'
    result, valid, message = parse_html_tags(
        text, keys=('required',), optional_keys=('optional',)
    )
    assert valid is True
    assert result == {'required': 'Content', 'optional': 'Extra'}
    assert message == ''


def test_parse_html_tags_missing_required():
    """Test parsing with missing required tags."""
    text = '<optional>Present</optional>'
    result, valid, message = parse_html_tags(
        text, keys=('required',), optional_keys=('optional',)
    )
    assert valid is False
    assert 'Missing the key <required>' in message


def test_parse_html_tags_multiple_instances():
    """Test parsing with multiple instances of the same tag."""
    text = '<tag>First</tag><tag>Second</tag>'

    # Test without merge_multiple
    result, valid, message = parse_html_tags(text, keys=('tag',))
    assert valid is False
    assert 'multiple instances' in message.lower()

    # Test with merge_multiple
    result, valid, message = parse_html_tags(text, keys=('tag',), merge_multiple=True)
    assert valid is True
    assert 'First' in result['tag']
    assert 'Second' in result['tag']


def test_parse_html_tags_raise():
    """Test parse_html_tags_raise function."""
    valid_text = '<required>Content</required>'
    result = parse_html_tags_raise(valid_text, keys=('required',))
    assert result == {'required': 'Content'}

    invalid_text = '<wrong>Content</wrong>'
    with pytest.raises(ParseError):
        parse_html_tags_raise(invalid_text, keys=('required',))


def test_parse_html_tags_empty():
    """Test parsing with empty content."""
    text = '<tag></tag>'
    result, valid, message = parse_html_tags(text, keys=('tag',))
    assert valid is True
    assert result == {'tag': ''}


def test_parse_html_tags_whitespace():
    """Test parsing with whitespace content."""
    text = '<tag>  \n  </tag>'
    result, valid, message = parse_html_tags(text, keys=('tag',))
    assert valid is True
    assert result == {'tag': ''}


def test_parse_html_tags_case_sensitivity():
    """Test case sensitivity in tag parsing."""
    text = '<TAG>Content</TAG>'
    result = extract_html_tags(text, ['tag'])
    assert result == {}  # Tags should be case-sensitive
