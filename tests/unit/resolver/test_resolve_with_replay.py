import re
from unittest.mock import mock_open, patch

import pytest

from openhands.resolver.resolve_issue import (
    REPLAY_COMMENT_PATTERN,
    strip_replay_comments,
)


def test_strip_replay_comments_basic():
    git_patch = """
+++ b/test.cpp
+ int x = 5; // replay comment
+ int y = 10; {/* replay comment */}
"""

    with patch('builtins.open', mock_open()):
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = True
            strip_replay_comments('/base', git_patch)


def test_strip_replay_comments_no_matches():
    git_patch = """
+++ b/test.cpp
+ int x = 5;
+ int y = 10;
"""

    with patch('builtins.open', mock_open()):
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = True
            strip_replay_comments('/base', git_patch)


def test_strip_replay_comments_multiple_files():
    git_patch = """
+++ b/test1.cpp
+ int x = 5; // replay
+++ b/test2.cpp
+ int y = 10; {/* replay */}
"""

    with patch('builtins.open', mock_open()):
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = True
            strip_replay_comments('/base', git_patch)


@pytest.mark.parametrize(
    'line,expected',
    [
        ('+ int x = 5; // replay', True),
        ('+ int x = 5; {/* replay */}', True),
        ('+ int x = 5;', False),
        ('- int x = 5; // replay', False),
    ],
)
def test_replay_comment_pattern(line, expected):
    matches = bool(re.match(REPLAY_COMMENT_PATTERN, line.lstrip()))
    assert (
        matches == expected
    ), f'\nPattern: {REPLAY_COMMENT_PATTERN}\nLine: {line}\nExpected: {expected}\nGot: {matches}\nMatch object: {re.match(REPLAY_COMMENT_PATTERN, line.lstrip())}'
