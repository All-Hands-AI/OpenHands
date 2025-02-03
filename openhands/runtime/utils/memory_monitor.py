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
        # Get the main process
        main_process = psutil.Process(os.getpid())

        # Get total memory usage including all children
        total_memory = main_process.memory_info().rss
        logger.info(
            f'Action execution server: Total memory usage (main processes): {total_memory / 1024**3:.2f}GB'
        )
        for child in main_process.children(recursive=True):
            try:
                total_memory += child.memory_info().rss
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                # Skip if process has terminated or we can't access it
                continue

        logger.info(
            f'Action execution server: Total memory usage (main + children processes): {total_memory / 1024**3:.2f}GB'
        )

        # Check total RSS (Resident Set Size) against limits
        if total_memory >= self.hard_limit_bytes:
            logger.error(
                f'Total memory usage ({total_memory / 1024**3:.2f}GB) exceeded hard limit '
                f'({self.hard_limit_bytes / 1024**3:.2f}GB). Terminating process group.'
            )
            # Kill the entire process group
            os.killpg(os.getpgid(os.getpid()), signal.SIGTERM)
        elif total_memory >= self.soft_limit_bytes:
            logger.warning(
                f'Warning: Total memory usage ({total_memory / 1024**3:.2f}GB) exceeded soft limit '
                f'({self.soft_limit_bytes / 1024**3:.2f}GB)'
            )
