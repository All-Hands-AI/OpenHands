# -*- coding: utf-8 -*-

import os
from shutil import rmtree


def remove(path):
    if os.path.exists(path):
        if os.path.isdir(path):
            rmtree(path)
        else:
            os.remove(path)


# find all indices of a list of strings that match a regex
def findall_regex(items, regex):
    found = list()
    for i in range(0, len(items)):
        k = regex.match(items[i])
        if k:
            found.append(i)
            k = None

    return found


def split_by_regex(items, regex):
    splits = list()
    indices = findall_regex(items, regex)
    k = None
    for i in indices:
        if k is None:
            splits.append(items[0:i])
            k = i
        else:
            splits.append(items[k:i])
            k = i

    splits.append(items[k:])

    return splits


# http://stackoverflow.com/questions/377017/test-if-executable-exists-in-python
def which(program):
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None
