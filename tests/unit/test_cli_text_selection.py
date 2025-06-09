"""Tests for CLI text selection functionality in OpenHands."""

import os
from pathlib import Path


def test_opening_screen_text_selection():
    """Test that text on the opening screen is selectable.

    This test verifies that the opening screen (banner, welcome message, etc.)
    uses TextArea with focusable=True for all text display, allowing users to
    select and copy text from the opening screen.
    """

    # Instead of mocking, let's directly check the implementation
    # Get the path to the tui.py file using a relative path from this test file
    current_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    repo_root = current_dir.parent.parent
    tui_path = repo_root / 'openhands' / 'cli' / 'tui.py'

    with open(tui_path, 'r') as f:
        tui_content = f.read()

    # Check if the opening screen functions use TextArea with focusable=True
    banner_function = tui_content[
        tui_content.find('def display_banner') : tui_content.find(
            'def display_welcome_message'
        )
    ]
    welcome_function = tui_content[
        tui_content.find('def display_welcome_message') : tui_content.find(
            'def display_initial_user_prompt'
        )
    ]
    prompt_function = tui_content[
        tui_content.find('def display_initial_user_prompt') : tui_content.find(
            '# Prompt output display functions'
        )
    ]

    # Count occurrences of TextArea with focusable=True in each function
    banner_count = banner_function.count('focusable=True')
    welcome_count = welcome_function.count('focusable=True')
    prompt_count = prompt_function.count('focusable=True')

    # We expect at least 1 TextArea with focusable=True in each function
    assert banner_count >= 1, 'Banner function should use TextArea with focusable=True'
    assert welcome_count >= 1, (
        'Welcome function should use TextArea with focusable=True'
    )
    assert prompt_count >= 1, 'Prompt function should use TextArea with focusable=True'

    # We expect at least 3 TextArea instances in total
    total_count = banner_count + welcome_count + prompt_count
    assert total_count >= 3, (
        'Opening screen should use TextArea with focusable=True for all text display'
    )
