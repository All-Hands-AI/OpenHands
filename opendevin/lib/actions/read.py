from .util import resolve_path

def read(base_path, file_path):
    file_path = resolve_path(base_path, file_path)
    with open(file_path, 'r') as file:
        return file.read()

