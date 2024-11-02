import os
import time
from difflib import unified_diff
from pathlib import Path
from typing import Dict, Optional, Set
from threading import Timer

import pathspec
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
        # Always ignore .git directory and its contents
        self.ignore_patterns = {'.git', '.git/*'}
        # Add any explicitly provided ignore patterns
        if ignore_patterns:
            self.ignore_patterns.update(ignore_patterns)

        # Load .gitignore patterns
        self.gitignore_spec = self._load_gitignore()

        self.observer = Observer()
        # Keep track of file contents
        self.file_contents: Dict[str, str] = {}
        # Track files with pending changes
        self.pending_changes: Set[str] = set()
        # Debounce timer for each file
        self.debounce_timers: Dict[str, Timer] = {}
        # Debounce delay in seconds
        self.debounce_delay = 0.1
        # Initialize file contents for existing files
        self._initialize_file_contents()

    def _load_gitignore(self) -> pathspec.PathSpec:
        """Load .gitignore patterns from the watched directory."""
        gitignore_patterns = []

        # Only look for .gitignore in the watched directory
        gitignore_path = os.path.join(self.directory, '.gitignore')
        try:
            if os.path.isfile(gitignore_path):
                with open(gitignore_path, 'r') as f:
                    patterns = f.read().splitlines()
                    # Filter out empty lines and comments
                    patterns = [p for p in patterns if p and not p.startswith('#')]
                    gitignore_patterns.extend(patterns)
        except IOError:
            pass

        return pathspec.PathSpec.from_lines(
            pathspec.patterns.GitWildMatchPattern, gitignore_patterns
        )

    def _initialize_file_contents(self):
        """Initialize the content cache for existing files in the watched directory."""
        for root, dirs, files in os.walk(self.directory, topdown=True):
            # Filter out ignored directories to prevent walking into them
            dirs[:] = [
                d for d in dirs if not self._should_ignore(os.path.join(root, d))
            ]

            # Process files in non-ignored directories
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
        # Cancel any pending timers
        for timer in self.debounce_timers.values():
            timer.cancel()
        self.observer.stop()
        self.observer.join()

    def _handle_debounced_change(self, path: str):
        """Handle a debounced file change event."""
        if path not in self.pending_changes:
            return

        self.pending_changes.remove(path)
        self.debounce_timers.pop(path, None)

        # Skip if file should be ignored
        if self._should_ignore(path) or not self._should_watch(path):
            return

        rel_path = os.path.relpath(path, self.directory)
        old_content = self.file_contents.get(path, '')
        new_content = self._read_file_content(path)

        # Only emit event if content actually changed
        if old_content != new_content:
            diff = self._generate_diff(old_content, new_content, rel_path)
            self.file_contents[path] = new_content

            observation = FileEditObservation(
                path=rel_path,
                prev_exist=True,
                old_content=old_content,
                new_content=new_content,
                content=diff,
            )
            self.event_stream.add_event(observation, EventSource.USER)

    def _schedule_debounced_change(self, path: str):
        """Schedule a debounced change event for a file."""
        # Cancel existing timer if any
        if path in self.debounce_timers:
            self.debounce_timers[path].cancel()

        # Create new timer
        timer = Timer(self.debounce_delay, self._handle_debounced_change, args=[path])
        timer.start()
        self.debounce_timers[path] = timer
        self.pending_changes.add(path)

    def _should_ignore(self, path: str) -> bool:
        """Check if the path should be ignored based on ignore patterns and .gitignore."""
        # Get path relative to watched directory
        rel_path = os.path.relpath(path, self.directory)

        # Convert Windows paths to Unix style for consistency
        rel_path = rel_path.replace(os.sep, '/')

        # First check if any part of the path contains .git
        path_parts = rel_path.split('/')
        for i in range(len(path_parts)):
            if path_parts[i] == '.git':
                return True

        # Then check explicit ignore patterns
        if any(Path(rel_path).match(pattern) for pattern in self.ignore_patterns):
            return True

        # For directories, we need to check both the directory path and path with trailing slash
        is_dir = os.path.isdir(path)
        if is_dir:
            # Check directory path both with and without trailing slash
            return self.gitignore_spec.match_file(
                rel_path
            ) or self.gitignore_spec.match_file(rel_path + '/')

        # For files, just check the path directly
        return self.gitignore_spec.match_file(rel_path)

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
            return ''

    def _generate_diff(self, old_content: str, new_content: str, path: str) -> str:
        """Generate a unified diff between old and new content without context lines."""
        old_lines = old_content.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)

        # Generate diff with no context lines (n=0)
        diff_lines = list(
            unified_diff(
                old_lines, new_lines, fromfile=path, tofile=path, n=0, lineterm=''
            )
        )

        # Remove the file name headers and timestamp lines (first 2 lines)
        if len(diff_lines) > 2:
            diff_lines = diff_lines[2:]

            # Also remove the @@ lines that show line numbers
            diff_lines = [line for line in diff_lines if not line.startswith('@@')]

        return ''.join(diff_lines)

    def on_created(self, event: FileSystemEvent):
        """Handle file creation event."""
        if event.is_directory:
            return

        # Schedule a debounced change
        self._schedule_debounced_change(event.src_path)

    def on_modified(self, event: FileSystemEvent):
        """Handle file modification event."""
        if event.is_directory:
            return

        # Schedule a debounced change
        self._schedule_debounced_change(event.src_path)

    def on_deleted(self, event: FileSystemEvent):
        """Handle file deletion event."""
        if event.is_directory:
            return

        # Cancel any pending changes for this file
        if event.src_path in self.debounce_timers:
            self.debounce_timers[event.src_path].cancel()
            self.debounce_timers.pop(event.src_path)
            self.pending_changes.discard(event.src_path)

        if self._should_ignore(event.src_path) or not self._should_watch(event.src_path):
            return

        rel_path = os.path.relpath(event.src_path, self.directory)
        old_content = self.file_contents.get(event.src_path, '')

        # For deletions, the diff will be all removals
        diff = self._generate_diff(old_content, '', rel_path)

        observation = FileEditObservation(
            path=rel_path,
            prev_exist=True,
            old_content=old_content,
            new_content='',
            content=diff,
        )
        self.event_stream.add_event(observation, EventSource.USER)
        self.file_contents.pop(event.src_path, None)

    def on_moved(self, event: FileSystemEvent):
        """Handle file move/rename event."""
        if event.is_directory:
            return

        # Cancel any pending changes for the source file
        if event.src_path in self.debounce_timers:
            self.debounce_timers[event.src_path].cancel()
            self.debounce_timers.pop(event.src_path)
            self.pending_changes.discard(event.src_path)

        # If this is a neovim swap file or backup file, ignore it
        if (
            event.src_path.endswith('.swp')
            or event.src_path.endswith('.swo')
            or event.src_path.endswith('~')
            or os.path.basename(event.src_path).startswith('4913')
        ):
            return

        if self._should_ignore(event.src_path) or not self._should_watch(event.src_path):
            return

        # Handle source file deletion
        src_rel_path = os.path.relpath(event.src_path, self.directory)
        old_content = self.file_contents.get(event.src_path, '')

        # For the source file, generate a deletion diff
        src_diff = self._generate_diff(old_content, '', src_rel_path)

        observation = FileEditObservation(
            path=src_rel_path,
            prev_exist=True,
            old_content=old_content,
            new_content='',
            content=src_diff,
        )
        self.event_stream.add_event(observation, EventSource.USER)
        self.file_contents.pop(event.src_path, None)

        # Handle destination file creation
        if not self._should_ignore(event.dest_path) and self._should_watch(
            event.dest_path
        ):
            # Schedule a debounced change for the destination file
            self.file_contents[event.dest_path] = old_content
            self._schedule_debounced_change(event.dest_path)
