"""Multiprocessing lock for coordinating Docker container lifecycle operations.

This module provides a global lock that prevents HTTP requests from being sent
while Docker containers are being started or stopped, preventing race conditions
that can occur when Docker's iptables rules are being updated.
"""

import multiprocessing as mp
import os
import tempfile
import time
from contextlib import contextmanager
from typing import Optional

from openhands.core.logger import openhands_logger as logger


class DockerLifecycleLock:
    """Global lock for coordinating Docker container lifecycle operations.

    This lock prevents race conditions that can occur when multiple processes
    are starting/stopping Docker containers simultaneously, which can cause
    iptables rules to be temporarily unavailable and result in connection errors.
    """

    _lock: Optional[mp.Lock] = None
    _lock_file: Optional[str] = None

    @classmethod
    def _get_lock(cls) -> mp.Lock:
        """Get or create the global multiprocessing lock."""
        if cls._lock is None:
            # Use a file-based lock that works across processes
            lock_dir = os.path.join(tempfile.gettempdir(), 'openhands_docker_locks')
            os.makedirs(lock_dir, exist_ok=True)
            cls._lock_file = os.path.join(lock_dir, 'docker_lifecycle.lock')

            # Create a multiprocessing lock that can be shared across processes
            cls._lock = mp.Lock()
            logger.debug('Created global Docker lifecycle lock')

        return cls._lock

    @classmethod
    @contextmanager
    def acquire(cls, timeout: float = 30.0, operation: str = "unknown"):
        """Acquire the Docker lifecycle lock.

        Args:
            timeout: Maximum time to wait for the lock in seconds
            operation: Description of the operation being performed (for logging)

        Yields:
            None

        Raises:
            TimeoutError: If the lock cannot be acquired within the timeout period
        """
        lock = cls._get_lock()
        start_time = time.time()

        logger.debug(f'Attempting to acquire Docker lifecycle lock for: {operation}')

        # Try to acquire the lock with timeout
        acquired = False
        while time.time() - start_time < timeout:
            if lock.acquire(block=False):
                acquired = True
                break
            time.sleep(0.1)  # Small delay to avoid busy waiting

        if not acquired:
            elapsed = time.time() - start_time
            raise TimeoutError(
                f'Failed to acquire Docker lifecycle lock for {operation} '
                f'after {elapsed:.1f} seconds'
            )

        try:
            logger.debug(f'Acquired Docker lifecycle lock for: {operation}')
            yield
        finally:
            lock.release()
            logger.debug(f'Released Docker lifecycle lock for: {operation}')

    @classmethod
    def is_locked(cls) -> bool:
        """Check if the Docker lifecycle lock is currently held.

        Returns:
            True if the lock is currently held, False otherwise
        """
        lock = cls._get_lock()
        # Try to acquire without blocking to check if it's available
        if lock.acquire(block=False):
            lock.release()
            return False
        return True


# Global instance for easy access
docker_lifecycle_lock = DockerLifecycleLock()
