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
    # check that the source text matches the context of the diff
    for old, new, line, hunk in changes:
        # might have to check for line is None here for ed scripts
        if old is not None and line is not None:
            if old > n_lines:
                raise HunkApplyException(
                    'context line {n}, "{line}" does not exist in source'.format(
                        n=old, line=line
                    ),
                    hunk=hunk,
                )
            if lines[old - 1] != line:
                raise HunkApplyException(
                    'context line {n}, "{line}" does not match "{sl}"'.format(
                        n=old, line=line, sl=lines[old - 1]
                    ),
                    hunk=hunk,
                )

    # for calculating the old line
    r = 0
    i = 0

    for old, new, line, hunk in changes:
        if old is not None and new is None:
            del lines[old - 1 - r + i]
            r += 1
        elif old is None and new is not None:
            lines.insert(new - 1, line)
            i += 1
        elif old is not None and new is not None:
            # Sometimes, people remove hunks from patches, making these
            # numbers completely unreliable. Because they're jerks.
            pass

    return lines
