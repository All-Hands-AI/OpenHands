from unittest.mock import mock_open, patch

import pytest

from openhands.linter.base import LintResult


@pytest.fixture
def mock_file_content():
    return '\n'.join([f'Line {i}' for i in range(1, 21)])


def test_visualize_standard_case(mock_file_content):
    lint_result = LintResult(
        file='test_file.py', line=10, column=5, message='Test error message'
    )

    with patch('builtins.open', mock_open(read_data=mock_file_content)):
        result = lint_result.visualize(half_window=3)

    expected_output = (
        " 7|Line 7\n"
        " 8|Line 8\n"
        " 9|Line 9\n"
        "\033[91m10|Line 10\033[0m\n"
        f"  {' ' * lint_result.column}^ ERROR HERE: Test error message\n"
        "11|Line 11\n"
        "12|Line 12\n"
        "13|Line 13"
    )

    assert result == expected_output


def test_visualize_small_window(mock_file_content):
    lint_result = LintResult(
        file='test_file.py', line=10, column=5, message='Test error message'
    )

    with patch('builtins.open', mock_open(read_data=mock_file_content)):
        result = lint_result.visualize(half_window=1)

    expected_output = (
        " 9|Line 9\n"
        "\033[91m10|Line 10\033[0m\n"
        f"  {' ' * lint_result.column}^ ERROR HERE: Test error message\n"
        "11|Line 11"
    )

    assert result == expected_output


def test_visualize_error_at_start(mock_file_content):
    lint_result = LintResult(
        file='test_file.py', line=1, column=3, message='Start error'
    )

    with patch('builtins.open', mock_open(read_data=mock_file_content)):
        result = lint_result.visualize(half_window=2)

    expected_output = (
        "\033[91m 1|Line 1\033[0m\n"
        f"  {' ' * lint_result.column}^ ERROR HERE: Start error\n"
        " 2|Line 2\n"
        " 3|Line 3"
    )

    assert result == expected_output


def test_visualize_error_at_end(mock_file_content):
    lint_result = LintResult(
        file='test_file.py', line=20, column=1, message='End error'
    )

    with patch('builtins.open', mock_open(read_data=mock_file_content)):
        result = lint_result.visualize(half_window=2)

    expected_output = (
        "18|Line 18\n"
        "19|Line 19\n"
        "\033[91m20|Line 20\033[0m\n"
        f"  {' ' * lint_result.column}^ ERROR HERE: End error"
    )

    assert result == expected_output
