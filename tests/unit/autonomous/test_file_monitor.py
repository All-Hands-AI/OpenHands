"""
Tests for File monitor
"""

import asyncio
from pathlib import Path

import pytest

from openhands.autonomous.perception.base import EventPriority, EventType
from openhands.autonomous.perception.file_monitor import FileMonitor


class TestFileMonitor:
    """Tests for FileMonitor class"""

    def test_create_monitor(self, temp_dir):
        """Test creating a file monitor"""
        monitor = FileMonitor(watch_path=str(temp_dir), check_interval=1)

        assert monitor.watch_path == temp_dir
        assert monitor.check_interval == 1

    def test_should_watch(self, temp_dir):
        """Test file watching logic"""
        monitor = FileMonitor(watch_path=str(temp_dir))

        # Should watch Python files
        assert monitor._should_watch(Path("test.py"))

        # Should not watch pyc files
        assert not monitor._should_watch(Path("test.pyc"))

        # Should not watch __pycache__
        assert not monitor._should_watch(Path("__pycache__/test.py"))

        # Should not watch .git
        assert not monitor._should_watch(Path(".git/config"))

    def test_custom_patterns(self, temp_dir):
        """Test custom watch patterns"""
        monitor = FileMonitor(
            watch_path=str(temp_dir),
            patterns=['*.txt', '*.md'],
            ignore_patterns=['*.log'],
        )

        assert monitor._should_watch(Path("README.md"))
        assert monitor._should_watch(Path("notes.txt"))
        assert not monitor._should_watch(Path("test.py"))
        assert not monitor._should_watch(Path("debug.log"))

    @pytest.mark.asyncio
    async def test_detect_new_file(self, temp_dir):
        """Test detecting a new file"""
        monitor = FileMonitor(watch_path=str(temp_dir), check_interval=0.1)

        # Initial scan
        monitor._scan_files()
        initial_count = len(monitor.file_state)

        # Create a new file
        new_file = temp_dir / "test.py"
        new_file.write_text("print('hello')")

        # Wait a bit for file system
        await asyncio.sleep(0.1)

        # Check for changes
        events = await monitor.check()

        # Should detect new file
        assert len(events) == 1
        assert events[0].event_type == EventType.FILE_CREATED
        assert 'test.py' in events[0].data['path']

    @pytest.mark.asyncio
    async def test_detect_modified_file(self, temp_dir):
        """Test detecting a modified file"""
        # Create initial file
        test_file = temp_dir / "test.py"
        test_file.write_text("print('hello')")

        # Create monitor after file exists
        monitor = FileMonitor(watch_path=str(temp_dir), check_interval=0.1)

        # Check baseline - no events
        events = await monitor.check()
        assert len(events) == 0

        # Modify file
        await asyncio.sleep(0.1)  # Ensure different mtime
        test_file.write_text("print('hello world')")

        await asyncio.sleep(0.1)

        # Check for changes
        events = await monitor.check()

        # Should detect modification
        assert len(events) == 1
        assert events[0].event_type == EventType.FILE_MODIFIED
        assert 'test.py' in events[0].data['path']

    @pytest.mark.asyncio
    async def test_detect_deleted_file(self, temp_dir):
        """Test detecting a deleted file"""
        # Create initial file
        test_file = temp_dir / "test.py"
        test_file.write_text("print('hello')")

        # Create monitor
        monitor = FileMonitor(watch_path=str(temp_dir), check_interval=0.1)

        # Delete file
        test_file.unlink()

        # Check for changes
        events = await monitor.check()

        # Should detect deletion
        assert len(events) == 1
        assert events[0].event_type == EventType.FILE_DELETED

    def test_determine_file_priority(self, temp_dir):
        """Test file priority determination"""
        monitor = FileMonitor(watch_path=str(temp_dir))

        # Critical - Dockerfile
        priority = monitor._determine_file_priority(Path("Dockerfile"))
        assert priority == EventPriority.CRITICAL

        # Critical - requirements.txt
        priority = monitor._determine_file_priority(Path("requirements.txt"))
        assert priority == EventPriority.CRITICAL

        # High - source code in src/
        priority = monitor._determine_file_priority(Path("src/main.py"))
        assert priority == EventPriority.HIGH

        # Medium - tests
        priority = monitor._determine_file_priority(Path("tests/test_main.py"))
        assert priority == EventPriority.MEDIUM

        # Low - other files
        priority = monitor._determine_file_priority(Path("notes.txt"))
        assert priority == EventPriority.LOW

    @pytest.mark.asyncio
    async def test_multiple_file_changes(self, temp_dir):
        """Test detecting multiple file changes"""
        monitor = FileMonitor(watch_path=str(temp_dir), check_interval=0.1)

        # Create multiple files
        (temp_dir / "file1.py").write_text("content1")
        (temp_dir / "file2.py").write_text("content2")
        (temp_dir / "file3.py").write_text("content3")

        await asyncio.sleep(0.1)

        # Check for changes
        events = await monitor.check()

        # Should detect all three
        assert len(events) == 3
        assert all(e.event_type == EventType.FILE_CREATED for e in events)
