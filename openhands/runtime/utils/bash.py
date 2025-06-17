"""Bash session implementations for OpenHands.

This module provides backward compatibility by re-exporting the bash session classes.
"""

# Re-export the tmux implementation (the original default)
# Re-export the subprocess implementation
from openhands.runtime.utils.subprocess_bash import SubprocessBashSession
from openhands.runtime.utils.tmux_bash import (
    TmuxBashSession,
    escape_bash_special_chars,
    split_bash_commands,
)

# For backward compatibility, export TmuxBashSession as BashSession
# This maintains compatibility with existing code that imports BashSession
BashSession = TmuxBashSession

__all__ = [
    'BashSession',
    'TmuxBashSession',
    'SubprocessBashSession',
    'escape_bash_special_chars',
    'split_bash_commands',
]
