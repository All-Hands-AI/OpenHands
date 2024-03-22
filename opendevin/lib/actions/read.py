import os

def read(base_path, file_path):
    file_path = os.path.join(base_path, file_path)
    with open(file_path, 'r') as file:
        return file.read()

