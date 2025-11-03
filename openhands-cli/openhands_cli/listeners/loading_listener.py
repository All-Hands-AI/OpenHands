"""
Loading animation utilities for OpenHands CLI.
Provides animated loading screens during agent initialization.
"""

import contextlib
import io
import sys
import time
import threading
import logging

ANIMATION_FRAMES = ['⠋','⠙','⠹','⠸','⠼','⠴','⠦','⠧','⠇','⠏']

def display_initialization_animation(text: str, done: threading.Event, stream) -> None:
    """Display a spinning animation while agent is being initialized.

    Args:
        text: The text to display alongside the animation
        is_loaded: Threading event that signals when loading is complete
        output_stream: Stream to write animation to (defaults to sys.stdout)
    """
    i = 0
    try:
        while not done.is_set():
            stream.write('\r\033[K')  # clear line
            stream.write(f'\033[38;2;255;215;0m[{ANIMATION_FRAMES[i % len(ANIMATION_FRAMES)]}] {text}\033[0m')
            stream.flush()
            time.sleep(0.1)
            i += 1
    finally:
        stream.write('\r\033[K')  # clear on exit
        stream.flush()

class LoadingContext:
    """
    Context manager for displaying loading animations in a separate thread
    Suppresses ALL output (stdout/stderr at FD level, across threads/C code)
    while showing a spinner on the original TTY.
    """
    def __init__(self, text: str, silence_logging: bool = True):
        self.text = text
        self.silence_logging = silence_logging
        self._done = threading.Event()
        self._thread = None

        self._saved_stdout_fd = None
        self._saved_stderr_fd = None
        self._devnull_fd = None
        self._spinner_stream = None
        self._old_logging_disable = None

    def __enter__(self):
        # 1) Save real stdout/stderr FDs
        self._saved_stdout_fd = os.dup(1)
        self._saved_stderr_fd = os.dup(2)

        # 2) Open /dev/null and dup2 over stdout/stderr (FD-level redirection)
        self._devnull_fd = os.open(os.devnull, os.O_WRONLY)
        os.dup2(self._devnull_fd, 1)
        os.dup2(self._devnull_fd, 2)

        # 3) Create a stream to the original TTY using the saved stdout FD
        #    buffering=1 for line-buffered text output
        self._spinner_stream = os.fdopen(self._saved_stdout_fd, 'w', buffering=1, closefd=False)

        # 4) Optionally silence logging (so handlers don't re-route elsewhere)
        if self.silence_logging:
            self._old_logging_disable = logging.root.manager.disable
            logging.disable(logging.CRITICAL)

        # 5) Start spinner thread writing to original TTY
        self._thread = threading.Thread(target=_spinner, args=(self.text, self._done, self._spinner_stream), daemon=True)
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc, tb):
        # Stop spinner
        self._done.set()
        if self._thread:
            self._thread.join(timeout=1.0)

        # Restore logging
        if self.silence_logging and self._old_logging_disable is not None:
            logging.disable(self._old_logging_disable)

        # Restore stdout/stderr to original FDs
        if self._saved_stdout_fd is not None:
            os.dup2(self._saved_stdout_fd, 1)
        if self._saved_stderr_fd is not None:
            os.dup2(self._saved_stderr_fd, 2)

        # Cleanup
        if self._spinner_stream:
            try:
                self._spinner_stream.flush()
            except Exception:
                pass
            # don't close saved fd twice; closing stream is fine here
            self._spinner_stream.close()

        for fd in (self._devnull_fd, self._saved_stdout_fd, self._saved_stderr_fd):
            try:
                if fd is not None:
                    os.close(fd)
            except OSError:
                pass
