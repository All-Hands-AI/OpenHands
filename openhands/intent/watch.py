import os
from pathlib import Path
from typing import Optional

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from openhands.events import EventSource, EventStream
from openhands.events.observation import FileSystemChangeObservation


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

    def on_any_event(self, event: FileSystemEvent):
        """Handle any filesystem event."""
        if event.is_directory:
            return

        if self._should_ignore(event.src_path):
            return

        if not self._should_watch(event.src_path):
            return

        # Convert the absolute path to a path relative to the watched directory
        rel_path = os.path.relpath(event.src_path, self.directory)

        # Map watchdog event types to our observation types
        event_type = event.event_type
        if event_type == "modified":
            change_type = "modified"
        elif event_type == "created":
            change_type = "created"
        elif event_type == "deleted":
            change_type = "deleted"
        elif event_type == "moved":
            change_type = "moved"
            # For moved events, also include the destination path
            dest_rel_path = os.path.relpath(event.dest_path, self.directory)
            rel_path = f"{rel_path} -> {dest_rel_path}"
        else:
            return

        observation = FileSystemChangeObservation(
            path=rel_path,
            change_type=change_type,
        )
        self.event_stream.add_event(observation, EventSource.ENVIRONMENT)