import threading
from typing import Callable

import docker


class LogStreamer:
    """Streams Docker container logs to stdout.

    This class provides a way to stream logs from a Docker container directly to stdout
    through the provided logging function.
    """

    def __init__(
        self,
        container: docker.models.containers.Container,
        logFn: Callable,
    ):
        self.log = logFn
        self.log_generator = container.logs(stream=True, follow=True)
        self._stop_event = threading.Event()

        # Start the stdout streaming thread
        self.stdout_thread = threading.Thread(target=self._stream_logs)
        self.stdout_thread.daemon = True
        self.stdout_thread.start()

    def _stream_logs(self):
        """Stream logs from the Docker container to stdout."""
        try:
            for log_line in self.log_generator:
                if self._stop_event.is_set():
                    break
                if log_line:
                    decoded_line = log_line.decode('utf-8').rstrip()
                    self.log('debug', f'[inside container] {decoded_line}')
        except Exception as e:
            self.log('error', f'Error streaming docker logs to stdout: {e}')

    def __del__(self):
        if self.stdout_thread and self.stdout_thread.is_alive():
            self.close(timeout=5)

    def close(self, timeout: float = 5.0):
        """Clean shutdown of the log streaming."""
        self._stop_event.set()
        if self.stdout_thread and self.stdout_thread.is_alive():
            self.stdout_thread.join(timeout)
        # Close the log generator to release the file descriptor
        if hasattr(self.log_generator, 'close'):
            self.log_generator.close()
