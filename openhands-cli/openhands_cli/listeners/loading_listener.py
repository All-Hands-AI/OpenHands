"""
Loading animation utilities for OpenHands CLI.
Provides animated loading screens during agent initialization.
"""

import contextlib
import io
import sys
import threading
import time


def display_initialization_animation(text: str, is_loaded: threading.Event, output_stream=None) -> None:
    """Display a spinning animation while agent is being initialized.

    Args:
        text: The text to display alongside the animation
        is_loaded: Threading event that signals when loading is complete
        output_stream: Stream to write animation to (defaults to sys.stdout)
    """
    ANIMATION_FRAMES = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    
    # Use provided stream or default to stdout
    stream = output_stream or sys.stdout

    i = 0
    while not is_loaded.is_set():
        stream.write('\n')
        stream.write(
            f'\033[s\033[J\033[38;2;255;215;0m[{ANIMATION_FRAMES[i % len(ANIMATION_FRAMES)]}] {text}\033[0m\033[u\033[1A'
        )
        stream.flush()
        time.sleep(0.1)
        i += 1

    stream.write('\r' + ' ' * (len(text) + 10) + '\r')
    stream.flush()


class LoadingContext:
    """Context manager for displaying loading animations in a separate thread while suppressing other output."""

    def __init__(self, text: str, suppress_output: bool = True):
        """Initialize the loading context.

        Args:
            text: The text to display during loading
            suppress_output: Whether to suppress stdout/stderr during loading
        """
        self.text = text
        self.suppress_output = suppress_output
        self.is_loaded = threading.Event()
        self.loading_thread: threading.Thread | None = None
        self._original_stdout = None
        self._original_stderr = None
        self._captured_output = None

    def __enter__(self) -> 'LoadingContext':
        """Start the loading animation in a separate thread and optionally suppress output."""
        # Capture original streams before starting animation
        if self.suppress_output:
            self._original_stdout = sys.stdout
            self._original_stderr = sys.stderr
            self._captured_output = io.StringIO()
        
        # Start the loading animation with the original stdout
        self.loading_thread = threading.Thread(
            target=display_initialization_animation,
            args=(self.text, self.is_loaded, self._original_stdout if self.suppress_output else None),
            daemon=True,
        )
        self.loading_thread.start()
        
        # Now suppress stdout/stderr if requested
        if self.suppress_output:
            sys.stdout = self._captured_output
            sys.stderr = self._captured_output
        
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Stop the loading animation, restore output streams, and clean up the thread."""
        # Restore stdout/stderr first
        if self.suppress_output and self._original_stdout and self._original_stderr:
            sys.stdout = self._original_stdout
            sys.stderr = self._original_stderr
        
        # Stop the loading animation
        self.is_loaded.set()
        if self.loading_thread:
            self.loading_thread.join(
                timeout=1.0
            )  # Wait up to 1 second for thread to finish