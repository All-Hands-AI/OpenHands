import os

# This is the path where the workspace is mounted in the container
# The LLM sometimes returns paths with this prefix, so we need to remove it
PATH_PREFIX = "/workspace/"

def resolve_path(base_path, file_path):
    if file_path.startswith(PATH_PREFIX):
        file_path = file_path[len(PATH_PREFIX):]
    return os.path.join(base_path, file_path)
