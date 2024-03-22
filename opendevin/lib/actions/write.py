import os

def write(base_path, path, contents):
    path = os.path.join(base_path, path)
    with open(path, 'w') as file:
        file.write(contents)
    return ""

