import os
from .util import resolve_path

def write(base_path, path, contents):
    file_path = resolve_path(base_path, file_path)
    with open(path, 'w') as file:
        file.write(contents)
    return ""

