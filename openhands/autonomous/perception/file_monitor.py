"""
File System Monitor

Monitors file system for changes to track code evolution.
"""

import asyncio
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

from openhands.autonomous.perception.base import (
    BaseMonitor,
    EventPriority,
    EventType,
    PerceptionEvent,
)

logger = logging.getLogger(__name__)


class FileMonitor(BaseMonitor):
    """
    Monitors file system for changes

    Tracks:
    - File creation
    - File modification
    - File deletion
    """

    def __init__(
        self,
        watch_path: str,
        check_interval: int = 30,
        patterns: Optional[List[str]] = None,
        ignore_patterns: Optional[List[str]] = None,
    ):
        """
        Args:
            watch_path: Path to monitor
            check_interval: Check interval in seconds
            patterns: File patterns to watch (e.g., ['*.py', '*.js'])
            ignore_patterns: Patterns to ignore (e.g., ['*.pyc', '__pycache__'])
        """
        super().__init__(name="FileMonitor", check_interval=check_interval)

        self.watch_path = Path(watch_path)
        self.patterns = patterns or ['*.py', '*.js', '*.ts', '*.yml', '*.yaml', '*.json', '*.md']
        self.ignore_patterns = ignore_patterns or [
            '*.pyc',
            '__pycache__',
            '.git',
            'node_modules',
            '.venv',
            'venv',
            '.pytest_cache',
            '.mypy_cache',
            '*.egg-info',
        ]

        # State: file path -> (size, mtime, content_hash)
        self.file_state: Dict[str, tuple[int, float, str]] = {}

        # Initialize state
        self._scan_files()

    def _should_watch(self, path: Path) -> bool:
        """Check if a file should be watched"""
        # Check ignore patterns
        for pattern in self.ignore_patterns:
            if pattern.startswith('*.'):
                if path.suffix == pattern[1:]:
                    return False
            elif pattern in str(path):
                return False

        # Check watch patterns
        if not self.patterns:
            return True

        for pattern in self.patterns:
            if pattern.startswith('*.'):
                if path.suffix == pattern[1:]:
                    return True
            elif path.match(pattern):
                return True

        return False

    def _get_file_hash(self, path: Path) -> str:
        """Get hash of file content"""
        try:
            with open(path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            logger.debug(f"Failed to hash {path}: {e}")
            return ""

    def _scan_files(self):
        """Scan all files and build state"""
        try:
            for path in self.watch_path.rglob('*'):
                if path.is_file() and self._should_watch(path):
                    try:
                        stat = path.stat()
                        content_hash = self._get_file_hash(path)
                        self.file_state[str(path)] = (stat.st_size, stat.st_mtime, content_hash)
                    except Exception as e:
                        logger.debug(f"Failed to stat {path}: {e}")

            logger.info(f"FileMonitor initialized: watching {len(self.file_state)} files")
        except Exception as e:
            logger.error(f"Failed to scan files: {e}")

    async def check(self) -> List[PerceptionEvent]:
        """Check for file changes"""
        events = []

        # Get current files
        current_files: Set[str] = set()

        try:
            for path in self.watch_path.rglob('*'):
                if path.is_file() and self._should_watch(path):
                    path_str = str(path)
                    current_files.add(path_str)

                    try:
                        stat = path.stat()
                        content_hash = self._get_file_hash(path)
                        current_state = (stat.st_size, stat.st_mtime, content_hash)

                        # Check if file is new or modified
                        if path_str not in self.file_state:
                            # New file
                            events.append(
                                PerceptionEvent(
                                    event_type=EventType.FILE_CREATED,
                                    priority=self._determine_file_priority(path),
                                    timestamp=datetime.now(),
                                    source=self.name,
                                    data={
                                        'path': path_str,
                                        'size': stat.st_size,
                                        'relative_path': str(path.relative_to(self.watch_path)),
                                    },
                                )
                            )
                            logger.debug(f"New file: {path_str}")

                        elif current_state != self.file_state[path_str]:
                            # Modified file
                            events.append(
                                PerceptionEvent(
                                    event_type=EventType.FILE_MODIFIED,
                                    priority=self._determine_file_priority(path),
                                    timestamp=datetime.now(),
                                    source=self.name,
                                    data={
                                        'path': path_str,
                                        'size': stat.st_size,
                                        'relative_path': str(path.relative_to(self.watch_path)),
                                        'old_size': self.file_state[path_str][0],
                                    },
                                )
                            )
                            logger.debug(f"Modified file: {path_str}")

                        # Update state
                        self.file_state[path_str] = current_state

                    except Exception as e:
                        logger.debug(f"Failed to check {path}: {e}")

        except Exception as e:
            logger.error(f"Failed to scan files: {e}")
            return events

        # Check for deleted files
        deleted_files = set(self.file_state.keys()) - current_files
        for path_str in deleted_files:
            events.append(
                PerceptionEvent(
                    event_type=EventType.FILE_DELETED,
                    priority=EventPriority.LOW,
                    timestamp=datetime.now(),
                    source=self.name,
                    data={'path': path_str},
                )
            )
            logger.debug(f"Deleted file: {path_str}")
            del self.file_state[path_str]

        return events

    def _determine_file_priority(self, path: Path) -> EventPriority:
        """Determine priority based on file type and location"""
        path_str = str(path).lower()

        # Critical: Config files, dependencies
        critical_files = [
            'dockerfile',
            'docker-compose',
            'requirements.txt',
            'package.json',
            'setup.py',
            'pyproject.toml',
        ]
        if any(cf in path_str for cf in critical_files):
            return EventPriority.CRITICAL

        # High: Source code in main directories
        if any(d in path_str for d in ['/src/', '/lib/', '/app/', '/core/']):
            return EventPriority.HIGH

        # Medium: Tests, docs
        if any(d in path_str for d in ['/test/', '/docs/']):
            return EventPriority.MEDIUM

        # Low: Everything else
        return EventPriority.LOW
