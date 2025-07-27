#!/usr/bin/env python3
"""
Get git changes in the current working directory relative to the remote origin if possible.
NOTE: Since this is run as a script, there should be no imports from project files!
"""

import glob
import json
import os
import subprocess
from pathlib import Path


def run(cmd: str, cwd: str) -> str:
    result = subprocess.run(
        args=cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd
    )
    byte_content = result.stderr or result.stdout or b''

    if result.returncode != 0:
        raise RuntimeError(
            f'error_running_cmd:{result.returncode}:{byte_content.decode()}'
        )
    return byte_content.decode().strip()


def get_valid_ref(repo_dir: str) -> str | None:
    try:
        current_branch = run('git --no-pager rev-parse --abbrev-ref HEAD', repo_dir)
    except RuntimeError:
        # Not a git repository (Or no commits)
        return None

    try:
        default_branch = (
            run('git --no-pager remote show origin | grep "HEAD branch"', repo_dir)
            .split()[-1]
            .strip()
        )
    except RuntimeError:
        # Git repository does not have a remote origin - use current
        return current_branch

    ref_current_branch = f'origin/{current_branch}'
    ref_non_default_branch = f'$(git --no-pager merge-base HEAD "$(git --no-pager rev-parse --abbrev-ref origin/{default_branch})")'
    ref_default_branch = f'origin/{default_branch}'
    ref_new_repo = '$(git --no-pager rev-parse --verify 4b825dc642cb6eb9a060e54bf8d69288fbee4904)'  # compares with empty tree

    refs = [
        ref_current_branch,
        ref_non_default_branch,
        ref_default_branch,
        ref_new_repo,
    ]
    # Find a ref that exists...
    for ref in refs:
        try:
            result = run(f'git --no-pager rev-parse --verify {ref}', repo_dir)
            return result
        except RuntimeError:
            # invalid ref - try next
            continue

    return None


def get_changes_in_repo(repo_dir: str) -> list[dict[str, str]]:
    # Gets the status relative to the origin default branch - not the same as `git status`

    ref = get_valid_ref(repo_dir)
    if not ref:
        return []

    try:
        # Get changed files
        changed_files = run(
            f'git --no-pager diff --name-status {ref}', repo_dir
        ).splitlines()
        changes = []
        for line in changed_files:
            if not line.strip():
                continue

            # Handle different output formats from git diff --name-status
            # Depending on git config, format can be either:
            # * "A file.txt"
            # * "A       file.txt"
            parts = line.split(maxsplit=1)
            if len(parts) != 2:
                continue

            status, path = parts
            status = status.strip()
            path = path.strip()

            if status == '??':
                status = 'A'
            elif status == '*':
                status = 'M'
            if status in {'M', 'A', 'D', 'R', 'C', 'U'}:
                changes.append(
                    {
                        'status': status,
                        'path': path,
                    }
                )

        # Get untracked files
        untracked_files = run(
            'git --no-pager ls-files --others --exclude-standard', repo_dir
        ).splitlines()
        for path in untracked_files:
            if path:
                changes.append({'status': 'A', 'path': path})
    except RuntimeError:
        # Unknown error
        pass

    return changes


def get_git_changes(cwd: str) -> list[dict[str, str]]:
    git_dirs = {
        os.path.dirname(f)[2:]
        for f in glob.glob('./*/.git', root_dir=cwd, recursive=True)
    }

    # First try the workspace directory
    changes = get_changes_in_repo(cwd)

    # Filter out any changes which are in one of the git directories
    changes = [
        change
        for change in changes
        if next(
            iter(git_dir for git_dir in git_dirs if change['path'].startswith(git_dir)),
            None,
        )
        is None
    ]

    # Add changes from git directories
    for git_dir in git_dirs:
        git_dir_changes = get_changes_in_repo(str(Path(cwd, git_dir)))
        for change in git_dir_changes:
            change['path'] = git_dir + '/' + change['path']
            changes.append(change)

    changes.sort(key=lambda change: change['path'])

    return changes


if __name__ == '__main__':
    changes = get_git_changes(os.getcwd())
    print(json.dumps(changes))
