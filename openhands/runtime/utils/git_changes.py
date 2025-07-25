#!/usr/bin/env python3
'''
Get git changes in the current working directory
'''

import glob
import json
import os
import subprocess


def run(cmd: str, cwd: str):
    result = subprocess.run(
        args=cmd.split(' '),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=cwd
    )
    return result


def git_status(cwd: str) -> list[dict[str, str]]:
    changes = []
    result = run('git status --porcelain -uall', cwd)
    if result.returncode == 0:
        lines = result.stdout.decode().split('\n')
        for line in lines:
            line = line.strip().split(' ', 1)
            if len(line) != 2:
                continue
            status, path = line
            if status == '??':
                status = 'A'
            elif status == '*':
                status = 'M'
            if status in {'M', 'A', 'D', 'R', 'C', 'U'}:
                changes.append({
                    'status': status,
                    'path': path,
                })
    return changes


def get_git_changes(cwd: str) -> list[dict[str, str]]:
    git_dirs = {
        os.path.dirname(f)[2:]
        for f in glob.glob('./*/.git', root_dir=cwd, recursive=True)
    }

    # First try the workspace directory
    changes = git_status(cwd)

    # Filter out any changes which are in one of the git directories
    changes = [
        change for change in changes
        if next(iter(
            git_dir for git_dir in git_dirs if change['path'].startswith(git_dir)
        ), None) is None
    ]

    # Add changes from git directories
    for git_dir in git_dirs:
        git_dir_changes = git_status(git_dir)
        for change in git_dir_changes:
            change['path'] = git_dir + '/' + change['path']
            changes.append(change)

    changes.sort(key=lambda change: change['path'])

    return changes


if __name__ == '__main__':
    changes = get_git_changes(os.getcwd())
    print(json.dumps(changes))
