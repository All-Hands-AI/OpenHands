from pathlib import Path

import pytest

from openhands.runtime.utils import files

SANDBOX_PATH_PREFIX = '/workspace'
WORKSPACE_BASE = 'workspace'


def test_resolve_path():
    assert (
        files.resolve_path('test.txt', '/workspace', WORKSPACE_BASE, SANDBOX_PATH_PREFIX)
        == Path(WORKSPACE_BASE) / 'test.txt'
    )
    assert (
        files.resolve_path('subdir/test.txt', '/workspace', WORKSPACE_BASE, SANDBOX_PATH_PREFIX)
        == Path(WORKSPACE_BASE) / 'subdir' / 'test.txt'
    )
    assert (
        files.resolve_path(Path(SANDBOX_PATH_PREFIX) / 'test.txt', '/workspace', WORKSPACE_BASE, SANDBOX_PATH_PREFIX)
        == Path(WORKSPACE_BASE) / 'test.txt'
    )
    assert (
        files.resolve_path(
            Path(SANDBOX_PATH_PREFIX) / 'subdir' / 'test.txt', '/workspace', WORKSPACE_BASE, SANDBOX_PATH_PREFIX
        )
        == Path(WORKSPACE_BASE) / 'subdir' / 'test.txt'
    )
    assert (
        files.resolve_path(
            Path(SANDBOX_PATH_PREFIX) / 'subdir' / '..' / 'test.txt', '/workspace', WORKSPACE_BASE, SANDBOX_PATH_PREFIX
        )
        == Path(WORKSPACE_BASE) / 'test.txt'
    )
    with pytest.raises(PermissionError):
        files.resolve_path(Path(SANDBOX_PATH_PREFIX) / '..' / 'test.txt', '/workspace', WORKSPACE_BASE, SANDBOX_PATH_PREFIX)
    with pytest.raises(PermissionError):
        files.resolve_path(Path('..') / 'test.txt', '/workspace', WORKSPACE_BASE, SANDBOX_PATH_PREFIX)
    with pytest.raises(PermissionError):
        files.resolve_path(Path('/') / 'test.txt', '/workspace', WORKSPACE_BASE, SANDBOX_PATH_PREFIX)
    assert (
        files.resolve_path('test.txt', '/workspace/test', WORKSPACE_BASE, SANDBOX_PATH_PREFIX)
        == Path(WORKSPACE_BASE) / 'test' / 'test.txt'
    )
