import os
from pathlib import Path
from typing import Dict, Optional

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from openhands.events import EventSource, EventStream
from openhands.events.observation import FileEditObservation


class FileWatcher(FileSystemEventHandler):
    """Watches a directory for filesystem changes and emits events to the EventStream.
    
    Args:
        directory (str): The directory path to watch for changes
        event_stream (EventStream): The event stream to emit events to
        recursive (bool, optional): Whether to watch subdirectories recursively. Defaults to True.
        patterns (list[str], optional): List of glob patterns to match files against. Defaults to None.
        ignore_patterns (list[str], optional): List of glob patterns to ignore. Defaults to None.
    """

    def __init__(
        self,
        directory: str,
        event_stream: EventStream,
        recursive: bool = True,
        patterns: Optional[list[str]] = None,
        ignore_patterns: Optional[list[str]] = None,
    ):
        super().__init__()
        self.directory = os.path.abspath(directory)
        self.event_stream = event_stream
        self.recursive = recursive
        self.patterns = patterns
        self.ignore_patterns = ignore_patterns or [".git/*", "__pycache__/*", "*.pyc"]
        self.observer = Observer()
        # Keep track of file contents
        self.file_contents: Dict[str, str] = {}
        # Initialize file contents for existing files
        self._initialize_file_contents()

    def _initialize_file_contents(self):
        """Initialize the content cache for existing files in the watched directory."""
        for root, _, files in os.walk(self.directory):
            for file in files:
                abs_path = os.path.join(root, file)
                if not self._should_ignore(abs_path) and self._should_watch(abs_path):
                    try:
                        with open(abs_path, 'r', encoding='utf-8') as f:
                            self.file_contents[abs_path] = f.read()
                    except (IOError, UnicodeDecodeError):
                        # Skip files that can't be read or aren't text files
                        pass

    def start(self):
        """Start watching the directory for changes."""
        self.observer.schedule(self, self.directory, recursive=self.recursive)
        self.observer.start()

    def stop(self):
        """Stop watching the directory."""
        self.observer.stop()
        self.observer.join()

    def _should_ignore(self, path: str) -> bool:
        """Check if the path should be ignored based on ignore patterns."""
        rel_path = os.path.relpath(path, self.directory)
        return any(Path(rel_path).match(pattern) for pattern in self.ignore_patterns)

    def _should_watch(self, path: str) -> bool:
        """Check if the path should be watched based on patterns."""
        if self.patterns is None:
            return True
        rel_path = os.path.relpath(path, self.directory)
        return any(Path(rel_path).match(pattern) for pattern in self.patterns)

    def _read_file_content(self, path: str) -> str:
        """Read the content of a file, returning empty string if it fails."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except (IOError, UnicodeDecodeError):
            return ""

    def on_created(self, event: FileSystemEvent):
        """Handle file creation event."""
        if event.is_directory or self._should_ignore(event.src_path) or not self._should_watch(event.src_path):
            return

        rel_path = os.path.relpath(event.src_path, self.directory)
        new_content = self._read_file_content(event.src_path)
        self.file_contents[event.src_path] = new_content

        observation = FileEditObservation(
            path=rel_path,
            prev_exist=False,
            old_content="",
            new_content=new_content
        )
        self.event_stream.add_event(observation, EventSource.ENVIRONMENT)

    def on_modified(self, event: FileSystemEvent):
        """Handle file modification event."""
        if event.is_directory or self._should_ignore(event.src_path) or not self._should_watch(event.src_path):
            return

        rel_path = os.path.relpath(event.src_path, self.directory)
        old_content = self.file_contents.get(event.src_path, "")
        new_content = self._read_file_content(event.src_path)
        
        # Only emit event if content actually changed
        if old_content != new_content:
            self.file_contents[event.src_path] = new_content
            observation = FileEditObservation(
                path=rel_path,
                prev_exist=True,
                old_content=old_content,
                new_content=new_content
            )
            self.event_stream.add_event(observation, EventSource.ENVIRONMENT)

    def on_deleted(self, event: FileSystemEvent):
        """Handle file deletion event."""
        if event.is_directory or self._should_ignore(event.src_path) or not self._should_watch(event.src_path):
            return

        rel_path = os.path.relpath(event.src_path, self.directory)
        old_content = self.file_contents.get(event.src_path, "")
        
        observation = FileEditObservation(
            path=rel_path,
            prev_exist=True,
            old_content=old_content,
            new_content=""
        )
        self.event_stream.add_event(observation, EventSource.ENVIRONMENT)
        self.file_contents.pop(event.src_path, None)

    def on_moved(self, event: FileSystemEvent):
        """Handle file move/rename event."""
        if event.is_directory or self._should_ignore(event.src_path) or not self._should_watch(event.src_path):
            return

        # Handle source file deletion
        src_rel_path = os.path.relpath(event.src_path, self.directory)
        old_content = self.file_contents.get(event.src_path, "")
        
        observation = FileEditObservation(
            path=src_rel_path,
            prev_exist=True,
            old_content=old_content,
            new_content=""
        )
        self.event_stream.add_event(observation, EventSource.ENVIRONMENT)
        self.file_contents.pop(event.src_path, None)

        # Handle destination file creation
        if not self._should_ignore(event.dest_path) and self._should_watch(event.dest_path):
            dest_rel_path = os.path.relpath(event.dest_path, self.directory)
            self.file_contents[event.dest_path] = old_content
            
            observation = FileEditObservation(
                path=dest_rel_path,
                prev_exist=False,
                old_content="",
                new_content=old_content
            )
            self.event_stream.add_event(observation, EventSource.ENVIRONMENT)