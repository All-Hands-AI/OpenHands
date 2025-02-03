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

        # Get main process memory usage
        main_memory = main_process.memory_info().rss
        memory_info = {
            'processes': [
                {
                    'type': 'main',
                    'name': main_process.name(),
                    'pid': os.getpid(),
                    'memory_gb': main_memory / 1024**3,
                }
            ]
        }

        # Track total memory and collect child process usage
        total_memory = main_memory
        for child in main_process.children(recursive=True):
            try:
                child_memory = child.memory_info().rss
                total_memory += child_memory
                memory_info['processes'].append(
                    {
                        'type': 'child',
                        'name': child.name(),
                        'pid': child.pid,
                        'memory_gb': child_memory / 1024**3,
                    }
                )
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        memory_info['total_gb'] = total_memory / 1024**3

        # Get system-wide memory usage percentage
        system_memory_percent = psutil.virtual_memory().percent

        # Only create and log report if system memory usage is high (>80%)
        # Create a simple formatted string
        report = 'Memory Usage Report:\n'
        for proc in memory_info['processes']:
            report += f"  [{proc['type']}] {proc['name']} (PID {proc['pid']}): {proc['memory_gb']:.2f}GB\n"
        report += f"Total Memory Usage: {memory_info['total_gb']:.2f}GB"
        report += f'\nSystem Memory Usage: {system_memory_percent:.1f}%'

        if system_memory_percent > 80:
            logger.info(f'(High memory usage): {memory_info}')
        logger.debug(report)
