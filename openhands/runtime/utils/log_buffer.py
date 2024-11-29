import threading
from typing import Callable


class LogBuffer:
    """Synchronous buffer for Docker container logs.

    This class provides a thread-safe way to collect, store, and retrieve logs
    from a Docker container. It uses a list to store log lines and provides methods
    for appending, retrieving, and clearing logs.
    """

    def __init__(self, container, logFn: Callable):
        self.init_msg = 'Runtime client initialized.'

        self.buffer: list[str] = []
        self.lock = threading.Lock()
        self._stop_event = threading.Event()
        self.log_generator = container.logs(stream=True, follow=True)
        self.log_stream_thread = threading.Thread(target=self.stream_logs)
        self.log_stream_thread.daemon = True
        self.log_stream_thread.start()
        self.log = logFn

    def append(self, log_line: str):
        with self.lock:
            self.buffer.append(log_line)

    def get_and_clear(self) -> list[str]:
        with self.lock:
            logs = list(self.buffer)
            self.buffer.clear()
            return logs

    def stream_logs(self):
        """Stream logs from the Docker container in a separate thread.

        This method runs in its own thread to handle the blocking
        operation of reading log lines from the Docker SDK's synchronous generator.
        """
        try:
            for log_line in self.log_generator:
                if self._stop_event.is_set():
                    break
                if log_line:
                    decoded_line = log_line.decode('utf-8').rstrip()
                    self.append(decoded_line)
        except Exception as e:
            self.log('error', f'Error streaming docker logs: {e}')

    def __del__(self):
        if self.log_stream_thread.is_alive():
            self.log(
                'warn',
                "LogBuffer was not properly closed. Use 'log_buffer.close()' for clean shutdown.",
            )
            self.close(timeout=5)

    def close(self, timeout: float = 5.0):
        self._stop_event.set()
        self.log_stream_thread.join(timeout)
        # Close the log generator to release the file descriptor
        if hasattr(self.log_generator, 'close'):
            self.log_generator.close()
