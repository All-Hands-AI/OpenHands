#!/usr/bin/env python3
'''
Get git diff in a single git file for the closest git repo in the file system
'''

import argparse
import glob
import json
import os
from pathlib import Path
import subprocess
import sys


def get_closest_git_repo(path: Path) -> Path | None:
    while True:
        path = path.parent
        git_path = Path(path, '.git')
        if git_path.is_dir():
            return path
        if path.parent == path:
            return None



def run(cmd: list[str], cwd: str):
    result = subprocess.run(
        args=cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=cwd
    )
    return result


def get_git_diff(relative_file_path: str) -> dict[str, str]:
    path = Path(os.getcwd(), relative_file_path).resolve()
    closest_git_repo = get_closest_git_repo(path)
    if not closest_git_repo:
        raise ValueError('no_repo')
    rev_result = run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], str(closest_git_repo))
    current_rev = rev_result.stdout.decode().strip()
    original_result = run(['git', 'show', f'{current_rev}:{path.relative_to(closest_git_repo)}'], str(closest_git_repo))
    try:
        with open(path, 'r') as f:
            modified = f.read()
    except FileNotFoundError:
        modified = ''
    return {
        'modified': modified,
        'original': original_result.stdout.decode(),
    }


if __name__ == '__main__':
    diff = get_git_diff(sys.argv[-1])
    print(json.dumps(diff))
