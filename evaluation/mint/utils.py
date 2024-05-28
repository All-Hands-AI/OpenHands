import functools


# use cache to avoid loading the same file multiple times
# which can leads to too many open files error
@functools.lru_cache(maxsize=128)
def load_file(filepath: str) -> str:
    with open(filepath, 'r') as f:
        content = f.read()
    return content
