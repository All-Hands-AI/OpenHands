"""
Loading animation utilities for OpenHands CLI.
Provides animated loading screens during agent initialization.
"""

import sys
import threading
import time


def display_initialization_animation(text: str, is_loaded: threading.Event) -> None:
    """Display a spinning animation while agent is being initialized.

    Args:
        text: The text to display alongside the animation
        is_loaded: Threading event that signals when loading is complete
    """
    ANIMATION_FRAMES = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']

    i = 0
    while not is_loaded.is_set():
        sys.stdout.write('\n')
        sys.stdout.write(
            f'\033[s\033[J\033[38;2;255;215;0m[{ANIMATION_FRAMES[i % len(ANIMATION_FRAMES)]}] {text}\033[0m\033[u\033[1A'
        )
        sys.stdout.flush()
        time.sleep(0.1)
        i += 1

    sys.stdout.write('\r' + ' ' * (len(text) + 10) + '\r')
    sys.stdout.flush()


class LoadingContext:
    """Context manager for displaying loading animations in a separate thread."""

    def __init__(self, text: str):
        """Initialize the loading context.

        Args:
            text: The text to display during loading
        """
        self.text = text
        self.is_loaded = threading.Event()
        self.loading_thread: threading.Thread | None = None

    def __enter__(self) -> 'LoadingContext':
        """Start the loading animation in a separate thread."""
        self.loading_thread = threading.Thread(
            target=display_initialization_animation,
            args=(self.text, self.is_loaded),
            daemon=True,
        )
        self.loading_thread.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Stop the loading animation and clean up the thread."""
        self.is_loaded.set()
        if self.loading_thread:
            self.loading_thread.join(
                timeout=1.0
            )  # Wait up to 1 second for thread to finish
