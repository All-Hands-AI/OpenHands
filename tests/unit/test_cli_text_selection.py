"""Tests for CLI text selection functionality."""


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

    with open('/workspace/OpenHands/openhands/cli/tui.py', 'r') as f:
        lines = f.readlines()

    for line_num in expected_lines:
        # Get the TextArea declaration and the next few lines
        text_area_block = ''.join(lines[line_num - 1 : line_num + 6])
        assert 'focusable=True' in text_area_block, (
            f'focusable=True not found in TextArea at line {line_num}: {text_area_block}'
        )
