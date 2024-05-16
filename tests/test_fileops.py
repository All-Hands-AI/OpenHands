from pathlib import Path

import pytest

from opendevin.core.config import config
from opendevin.runtime.server import files

SANDBOX_PATH_PREFIX = '/workspace'


def test_resolve_path():
    assert (
        files.resolve_path('test.txt', '/workspace')
        == Path(config.workspace_base) / 'test.txt'
    )
    assert (
        files.resolve_path('subdir/test.txt', '/workspace')
        == Path(config.workspace_base) / 'subdir' / 'test.txt'
    )
    assert (
        files.resolve_path(Path(SANDBOX_PATH_PREFIX) / 'test.txt', '/workspace')
        == Path(config.workspace_base) / 'test.txt'
    )
    assert (
        files.resolve_path(
            Path(SANDBOX_PATH_PREFIX) / 'subdir' / 'test.txt', '/workspace'
        )
        == Path(config.workspace_base) / 'subdir' / 'test.txt'
    )
    assert (
        files.resolve_path(
            Path(SANDBOX_PATH_PREFIX) / 'subdir' / '..' / 'test.txt', '/workspace'
        )
        == Path(config.workspace_base) / 'test.txt'
    )
    with pytest.raises(PermissionError):
        files.resolve_path(Path(SANDBOX_PATH_PREFIX) / '..' / 'test.txt', '/workspace')
    with pytest.raises(PermissionError):
        files.resolve_path(Path('..') / 'test.txt', '/workspace')
    with pytest.raises(PermissionError):
        files.resolve_path(Path('/') / 'test.txt', '/workspace')
    assert (
        files.resolve_path('test.txt', '/workspace/test')
        == Path(config.workspace_base) / 'test' / 'test.txt'
    )
