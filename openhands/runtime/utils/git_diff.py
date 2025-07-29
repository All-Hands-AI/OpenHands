#!/usr/bin/env python3
"""
Get git diff in a single git file for the closest git repo in the file system
NOTE: Since this is run as a script, there should be no imports from project files!
"""

import json
import os
import subprocess
import sys
from pathlib import Path


def get_closest_git_repo(path: Path) -> Path | None:
    while True:
        path = path.parent
        git_path = Path(path, '.git')
        if git_path.is_dir():
            return path
        if path.parent == path:
            return None


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
    ref_default_branch = 'origin/' + default_branch
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
            run(f'git --no-pager rev-parse --verify {ref}', repo_dir)
            return ref
        except RuntimeError:
            # invalid ref - try next
            continue

    return None


def get_git_diff(relative_file_path: str) -> dict[str, str]:
    path = Path(os.getcwd(), relative_file_path).resolve()
    closest_git_repo = get_closest_git_repo(path)
    if not closest_git_repo:
        raise ValueError('no_repo')
    current_rev = get_valid_ref(str(closest_git_repo))
    try:
        original = run(
            f'git show "{current_rev}:{path.relative_to(closest_git_repo)}"',
            str(closest_git_repo),
        )
    except RuntimeError:
        original = ''
    try:
        with open(path, 'r') as f:
            modified = '\n'.join(f.read().splitlines())
    except FileNotFoundError:
        modified = ''
    return {
        'modified': modified,
        'original': original,
    }


if __name__ == '__main__':
    diff = get_git_diff(sys.argv[-1])
    print(json.dumps(diff))
