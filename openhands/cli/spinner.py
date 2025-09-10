"""Unified spinner utility for CLI operations."""

import asyncio
import sys
import threading
import time


class Spinner:
    """A unified spinner utility that works with both threading and asyncio events."""

    FRAMES = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']

    def __init__(self, text: str = 'Loading...', use_ansi_colors: bool = False):
        """Initialize spinner with text and optional ANSI color formatting.

        Args:
            text: Text to display alongside the spinner
            use_ansi_colors: Whether to use ANSI color codes for formatting
        """
        self.text = text
        self.use_ansi_colors = use_ansi_colors
        self._frame_index = 0

    def _get_formatted_text(self) -> str:
        """Get the formatted spinner text."""
        frame = self.FRAMES[self._frame_index % len(self.FRAMES)]
        if self.use_ansi_colors:
            return f'\033[s\033[J\033[38;2;255;215;0m[{frame}] {self.text}\033[0m\033[u\033[1A'
        else:
            return f'\r{frame} {self.text}'

    def _clear_line(self) -> None:
        """Clear the spinner line."""
        if self.use_ansi_colors:
            sys.stdout.write('\r' + ' ' * (len(self.text) + 10) + '\r')
        else:
            print('\r' + ' ' * (len(self.text) + 10) + '\r', end='', flush=True)

    def show_with_threading_event(self, stop_event: threading.Event) -> None:
        """Show spinner using a threading.Event for control.

        Args:
            stop_event: Threading event to signal when to stop the spinner
        """
        self._frame_index = 0
        while not stop_event.is_set():
            if self.use_ansi_colors:
                sys.stdout.write('\n')
                sys.stdout.write(self._get_formatted_text())
                sys.stdout.flush()
            else:
                print(self._get_formatted_text(), end='', flush=True)

            time.sleep(0.1)
            self._frame_index += 1

        self._clear_line()
        sys.stdout.flush()

    def show_with_asyncio_event(self, is_loaded: asyncio.Event) -> None:
        """Show spinner using an asyncio.Event for control.

        Args:
            is_loaded: Asyncio event to signal when to stop the spinner
        """
        self._frame_index = 0
        while not is_loaded.is_set():
            if self.use_ansi_colors:
                sys.stdout.write('\n')
                sys.stdout.write(self._get_formatted_text())
                sys.stdout.flush()
            else:
                print(self._get_formatted_text(), end='', flush=True)

            time.sleep(0.1)
            self._frame_index += 1

        self._clear_line()
        sys.stdout.flush()


def show_loading_spinner(
    stop_event: threading.Event, text: str = 'Loading conversations...'
) -> None:
    """Show a loading spinner animation using threading.Event.

    Args:
        stop_event: Threading event to signal when to stop the spinner
        text: Text to display alongside the spinner
    """
    spinner = Spinner(text, use_ansi_colors=False)
    spinner.show_with_threading_event(stop_event)


def display_initialization_animation(text: str, is_loaded: asyncio.Event) -> None:
    """Display initialization animation using asyncio.Event.

    Args:
        text: Text to display alongside the spinner
        is_loaded: Asyncio event to signal when to stop the spinner
    """
    spinner = Spinner(text, use_ansi_colors=True)
    spinner.show_with_asyncio_event(is_loaded)
