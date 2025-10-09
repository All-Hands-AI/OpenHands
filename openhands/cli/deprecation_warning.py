"""Deprecation warning utilities for the old OpenHands CLI."""

import sys

from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import HTML


def display_deprecation_warning() -> None:
    """Display a prominent deprecation warning for the old CLI interface."""
    warning_lines = [
        '',
        '⚠️  DEPRECATION WARNING ⚠️',
        '',
        'This CLI interface is deprecated and will be removed in a future version.',
        'Please migrate to the new OpenHands CLI:',
        '',
        'For more information, visit: https://docs.all-hands.dev/usage/how-to/cli-mode',
        '',
        '=' * 70,
        '',
    ]

    # Print warning with prominent styling
    for line in warning_lines:
        if 'DEPRECATION WARNING' in line:
            print_formatted_text(HTML(f'<ansired><b>{line}</b></ansired>'))
        elif line.startswith('  •'):
            print_formatted_text(HTML(f'<ansigreen>{line}</ansigreen>'))
        elif 'https://' in line:
            print_formatted_text(HTML(f'<ansiblue>{line}</ansiblue>'))
        elif line.startswith('='):
            print_formatted_text(HTML(f'<ansiyellow>{line}</ansiyellow>'))
        else:
            print_formatted_text(HTML(f'<ansiyellow>{line}</ansiyellow>'))

    # Flush to ensure immediate display
    sys.stdout.flush()
