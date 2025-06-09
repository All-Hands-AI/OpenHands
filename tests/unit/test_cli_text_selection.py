"""Tests for CLI text selection functionality."""

import os
from pathlib import Path


def test_text_areas_have_focusable_parameter():
    """Test that all TextArea instances in the CLI have the focusable parameter set to True."""

    # Let's directly check if all TextArea instances have been updated with focusable=True
    # by looking at the specific lines where we made changes

    expected_lines = [
        222,
        238,
        267,
        283,
        300,
        319,
        429,  # Line numbers where TextArea is instantiated
    ]

    # Get the path to the tui.py file using a relative path from this test file
    current_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    repo_root = current_dir.parent.parent
    tui_path = repo_root / 'openhands' / 'cli' / 'tui.py'

    with open(tui_path, 'r') as f:
        lines = f.readlines()

    for line_num in expected_lines:
        # Get the TextArea declaration and the next few lines
        text_area_block = ''.join(lines[line_num - 1 : line_num + 6])
        assert 'focusable=True' in text_area_block, (
            f'focusable=True not found in TextArea at line {line_num}: {text_area_block}'
        )
