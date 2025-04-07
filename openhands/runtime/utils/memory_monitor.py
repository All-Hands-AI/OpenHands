"""Memory monitoring utilities for the runtime."""

import threading

from memory_profiler import memory_usage

from openhands.core.logger import openhands_logger as logger


class LogStream:
    """Stream-like object that redirects writes to a logger."""

    def write(self, message):
        if message and not message.isspace():
            logger.info(f'[Memory usage] {message.strip()}')

    def flush(self):
        pass


class MemoryMonitor:
    def __init__(self, enable: bool = False):
        """Memory monitor for the runtime."""
        self._monitoring_thread: threading.Thread | None = None
        self._stop_monitoring = threading.Event()
        self.log_stream = LogStream()
        self.enable = enable

    def start_monitoring(self):
        """Start monitoring memory usage."""
        if not self.enable:
            return

        if self._monitoring_thread is not None:
            return

        def monitor_process():
            try:
                # Use memory_usage's built-in monitoring loop
                mem_usage = memory_usage(
                    -1,  # Monitor current process
                    interval=0.1,  # Check every second
                    timeout=3600,  # Run indefinitely
                    max_usage=False,  # Get continuous readings
                    include_children=True,  # Include child processes
                    multiprocess=True,  # Monitor all processes
                    stream=self.log_stream,  # Redirect output to logger
                    backend='psutil_pss',
                )
                logger.info(f'Memory usage across time: {mem_usage}')
            except Exception as e:
                logger.error(f'Memory monitoring failed: {e}')

        self._monitoring_thread = threading.Thread(target=monitor_process, daemon=True)
        self._monitoring_thread.start()
        logger.info('Memory monitoring started')

    def stop_monitoring(self):
        """Stop monitoring memory usage."""
        if not self.enable:
            return

        if self._monitoring_thread is not None:
            self._stop_monitoring.set()
            self._monitoring_thread = None
            logger.info('Memory monitoring stopped')
