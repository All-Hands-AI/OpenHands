"""Memory monitoring utilities for the runtime."""

import os
import resource
import signal
from typing import Optional

import psutil

from openhands.core.logger import openhands_logger as logger


class MemoryMonitor:
    def __init__(
        self,
        soft_limit_gb: float = 3.5,
        hard_limit_gb: float = 3.8,
        check_interval: float = 1.0,
    ):
        """Initialize memory monitor with configurable limits.

        Args:
            soft_limit_gb: Soft memory limit in GB. When exceeded, a warning is logged.
            hard_limit_gb: Hard memory limit in GB. When exceeded, process is killed.
            check_interval: How often to check memory usage, in seconds.
        """
        self.soft_limit_bytes = int(soft_limit_gb * 1024 * 1024 * 1024)
        self.hard_limit_bytes = int(hard_limit_gb * 1024 * 1024 * 1024)
        self.check_interval = check_interval
        self._timer: Optional[int] = None

    def start_monitoring(self):
        """Start monitoring memory usage."""
        # Set resource limits
        resource.setrlimit(
            resource.RLIMIT_AS, (self.hard_limit_bytes, self.hard_limit_bytes)
        )

        # Set up signal handler for timer
        signal.signal(signal.SIGALRM, self._check_memory)
        signal.setitimer(signal.ITIMER_REAL, self.check_interval, self.check_interval)

    def stop_monitoring(self):
        """Stop monitoring memory usage."""
        if self._timer is not None:
            signal.setitimer(signal.ITIMER_REAL, 0)
            self._timer = None

    def _check_memory(self, signum, frame):
        """Check current memory usage and take action if limits are exceeded."""
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        logger.info(
            f'Action execution server: Memory usage: {memory_info.rss / 1024**3:.2f}GB'
        )
        # Check RSS (Resident Set Size) - actual memory used
        if memory_info.rss >= self.hard_limit_bytes:
            # Log error and kill the process
            logger.error(
                f'Memory usage ({memory_info.rss / 1024**3:.2f}GB) exceeded hard limit '
                f'({self.hard_limit_bytes / 1024**3:.2f}GB). Terminating process.'
            )
            os.kill(os.getpid(), signal.SIGTERM)
        elif memory_info.rss >= self.soft_limit_bytes:
            # Log warning
            logger.warning(
                f'Warning: Memory usage ({memory_info.rss / 1024**3:.2f}GB) exceeded soft limit '
                f'({self.soft_limit_bytes / 1024**3:.2f}GB)'
            )
