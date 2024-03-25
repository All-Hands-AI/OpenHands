from .util import resolve_path

def write(base_path, file_path, contents):
    file_path = resolve_path(base_path, file_path)
    with open(file_path, 'w') as file:
        file.write(contents)
    return ""

