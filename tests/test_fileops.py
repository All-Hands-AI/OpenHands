from pathlib import Path

import pytest

from openhands.runtime.utils import files

SANDBOX_PATH_PREFIX = '/workspace'
CONTAINER_PATH = '/workspace'
HOST_PATH = 'workspace'


def test_resolve_path():
    assert (
        files.resolve_path('test.txt', '/workspace', HOST_PATH, CONTAINER_PATH)
        == Path(HOST_PATH) / 'test.txt'
    )
    assert (
        files.resolve_path('subdir/test.txt', '/workspace', HOST_PATH, CONTAINER_PATH)
        == Path(HOST_PATH) / 'subdir' / 'test.txt'
    )
    assert (
        files.resolve_path(
            Path(SANDBOX_PATH_PREFIX) / 'test.txt',
            '/workspace',
            HOST_PATH,
            CONTAINER_PATH,
        )
        == Path(HOST_PATH) / 'test.txt'
    )
    assert (
        files.resolve_path(
            Path(SANDBOX_PATH_PREFIX) / 'subdir' / 'test.txt',
            '/workspace',
            HOST_PATH,
            CONTAINER_PATH,
        )
        == Path(HOST_PATH) / 'subdir' / 'test.txt'
    )
    assert (
        files.resolve_path(
            Path(SANDBOX_PATH_PREFIX) / 'subdir' / '..' / 'test.txt',
            '/workspace',
            HOST_PATH,
            CONTAINER_PATH,
        )
        == Path(HOST_PATH) / 'test.txt'
    )
    with pytest.raises(PermissionError):
        files.resolve_path(
            Path(SANDBOX_PATH_PREFIX) / '..' / 'test.txt',
            '/workspace',
            HOST_PATH,
            CONTAINER_PATH,
        )
    with pytest.raises(PermissionError):
        files.resolve_path(
            Path('..') / 'test.txt', '/workspace', HOST_PATH, CONTAINER_PATH
        )
    with pytest.raises(PermissionError):
        files.resolve_path(
            Path('/') / 'test.txt', '/workspace', HOST_PATH, CONTAINER_PATH
        )
    assert (
        files.resolve_path('test.txt', '/workspace/test', HOST_PATH, CONTAINER_PATH)
        == Path(HOST_PATH) / 'test' / 'test.txt'
    )
