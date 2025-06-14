from pathlib import Path

import pytest

from openhands.runtime.utils import files

SANDBOX_PATH_PREFIX = '/workspace'
HOST_PATH = 'workspace'
SANDBOX_VOLUMES = f'{HOST_PATH}:/workspace:rw'


def test_resolve_path():
    assert (
        files.resolve_path('test.txt', '/workspace', SANDBOX_VOLUMES)
        == Path(HOST_PATH) / 'test.txt'
    )
    assert (
        files.resolve_path('subdir/test.txt', '/workspace', SANDBOX_VOLUMES)
        == Path(HOST_PATH) / 'subdir' / 'test.txt'
    )
    assert (
        files.resolve_path(
            Path(SANDBOX_PATH_PREFIX) / 'test.txt',
            '/workspace',
            SANDBOX_VOLUMES,
        )
        == Path(HOST_PATH) / 'test.txt'
    )
    assert (
        files.resolve_path(
            Path(SANDBOX_PATH_PREFIX) / 'subdir' / 'test.txt',
            '/workspace',
            SANDBOX_VOLUMES,
        )
        == Path(HOST_PATH) / 'subdir' / 'test.txt'
    )
    assert (
        files.resolve_path(
            Path(SANDBOX_PATH_PREFIX) / 'subdir' / '..' / 'test.txt',
            '/workspace',
            SANDBOX_VOLUMES,
        )
        == Path(HOST_PATH) / 'test.txt'
    )
    with pytest.raises(PermissionError):
        files.resolve_path(
            Path(SANDBOX_PATH_PREFIX) / '..' / 'test.txt',
            '/workspace',
            SANDBOX_VOLUMES,
        )
    with pytest.raises(PermissionError):
        files.resolve_path(Path('..') / 'test.txt', '/workspace', SANDBOX_VOLUMES)
    with pytest.raises(PermissionError):
        files.resolve_path(Path('/') / 'test.txt', '/workspace', SANDBOX_VOLUMES)
    assert (
        files.resolve_path('test.txt', '/workspace/test', SANDBOX_VOLUMES)
        == Path(HOST_PATH) / 'test' / 'test.txt'
    )
