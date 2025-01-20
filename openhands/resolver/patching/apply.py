# -*- coding: utf-8 -*-

import os.path
import subprocess
import tempfile

from .exceptions import HunkApplyException, SubprocessException
from .snippets import remove, which


def _apply_diff_with_subprocess(diff, lines, reverse=False):
    # call out to patch program
    patchexec = which('patch')
    if not patchexec:
        raise SubprocessException('cannot find patch program', code=-1)

    tempdir = tempfile.gettempdir()

    filepath = os.path.join(tempdir, 'wtp-' + str(hash(diff.header)))
    oldfilepath = filepath + '.old'
    newfilepath = filepath + '.new'
    rejfilepath = filepath + '.rej'
    patchfilepath = filepath + '.patch'
    with open(oldfilepath, 'w') as f:
        f.write('\n'.join(lines) + '\n')

    with open(patchfilepath, 'w') as f:
        f.write(diff.text)

    args = [
        patchexec,
        '--reverse' if reverse else '--forward',
        '--quiet',
        '--no-backup-if-mismatch',
        '-o',
        newfilepath,
        '-i',
        patchfilepath,
        '-r',
        rejfilepath,
        oldfilepath,
    ]
    ret = subprocess.call(args)

    with open(newfilepath) as f:
        lines = f.read().splitlines()

    try:
        with open(rejfilepath) as f:
            rejlines = f.read().splitlines()
    except IOError:
        rejlines = None

    remove(oldfilepath)
    remove(newfilepath)
    remove(rejfilepath)
    remove(patchfilepath)

    # do this last to ensure files get cleaned up
    if ret != 0:
        raise SubprocessException('patch program failed', code=ret)

    return lines, rejlines


def _reverse(changes):
    def _reverse_change(c):
        return c._replace(old=c.new, new=c.old)

    return [_reverse_change(c) for c in changes]


def apply_diff(diff, text, reverse=False, use_patch=False):
    try:
        lines = text.splitlines()
    except AttributeError:
        lines = list(text)

    if use_patch:
        return _apply_diff_with_subprocess(diff, lines, reverse)

    n_lines = len(lines)

    changes = _reverse(diff.changes) if reverse else diff.changes
    
    # Add bounds checking for each change
    for old, new, line, hunk in changes:
        if old is not None and line is not None:
            # Check if the old line number is valid
            if old <= 0 or old > n_lines:
                raise HunkApplyException(
                    f'Invalid line number {old} (file has {n_lines} lines)',
                    hunk=hunk
                )
            
            # Safely check line content
            try:
                current_line = lines[old - 1]
                if current_line != line:
                    raise HunkApplyException(
                        f'Context mismatch at line {old}:\n'
                        f'Expected: "{line}"\n'
                        f'Found: "{current_line}"',
                        hunk=hunk
                    )
            except IndexError:
                raise HunkApplyException(
                    f'Failed to access line {old} (file has {n_lines} lines)',
                    hunk=hunk
                )

    # Apply changes with bounds checking
    result_lines = lines.copy()  # Work on a copy to prevent partial modifications
    offset = 0  # Track line number changes

    for old, new, line, hunk in changes:
        try:
            if old is not None and new is None:
                # Delete line
                if 0 <= (old - 1 + offset) < len(result_lines):
                    del result_lines[old - 1 + offset]
                    offset -= 1
            elif old is None and new is not None:
                # Insert line
                insert_pos = new - 1 + offset
                if 0 <= insert_pos <= len(result_lines):
                    result_lines.insert(insert_pos, line)
                    offset += 1
            elif old is not None and new is not None:
                # Replace line
                if 0 <= (old - 1 + offset) < len(result_lines):
                    result_lines[old - 1 + offset] = line
        except IndexError as e:
            raise HunkApplyException(
                f'Failed to apply change at line {old or new}: {str(e)}',
                hunk=hunk
            )

    return result_lines
