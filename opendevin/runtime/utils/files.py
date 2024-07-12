import os
from typing import List, Optional

from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern


def list_files(full_path: str, entries: Optional[List[str]] = None) -> List[str]:
    # Check if .gitignore exists
    gitignore_path = os.path.join(full_path, '.gitignore')
    if os.path.exists(gitignore_path):
        # Use PathSpec to parse .gitignore
        with open(gitignore_path, 'r') as f:
            spec = PathSpec.from_lines(GitWildMatchPattern, f.readlines())
    else:
        # Fallback to default exclude list if .gitignore doesn't exist
        default_exclude = [
            '.git',
            '.DS_Store',
            '.svn',
            '.hg',
            '.idea',
            '.vscode',
            '.settings',
            '.pytest_cache',
            '__pycache__',
            'node_modules',
            'vendor',
            'build',
            'dist',
            'bin',
            'logs',
            'log',
            'tmp',
            'temp',
            'coverage',
            'venv',
            'env',
        ]
        spec = PathSpec.from_lines(GitWildMatchPattern, default_exclude)

    if not entries:
        entries = os.listdir(full_path)

    # Filter entries using PathSpec
    filtered_entries = [
        entry
        for entry in entries
        if not spec.match_file(os.path.relpath(entry, str(full_path)))
    ]

    # Separate directories and files
    directories = []
    files = []
    for entry in filtered_entries:
        # Remove leading slash and any parent directory components
        entry_relative = entry.lstrip('/').split('/')[-1]

        # Construct the full path by joining the base path with the relative entry path
        full_entry_path = os.path.join(full_path, entry_relative)
        if os.path.exists(full_entry_path):
            is_dir = os.path.isdir(full_entry_path)
            if is_dir:
                directories.append(entry)
            else:
                files.append(entry)

    # Sort directories and files separately
    directories.sort(key=lambda s: s.lower())
    files.sort(key=lambda s: s.lower())

    # Combine sorted directories and files
    sorted_entries = directories + files
    return sorted_entries
