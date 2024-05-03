from pathlib import Path

import pytest

from opendevin import config
from opendevin.events.action import files
from opendevin.schema import ConfigType

SANDBOX_PATH_PREFIX = '/workspace'


def test_resolve_path():
    assert (
        files.resolve_path('test.txt', '/workspace')
        == Path(config.get(ConfigType.WORKSPACE_BASE)) / 'test.txt'
    )
    assert (
        files.resolve_path('subdir/test.txt', '/workspace')
        == Path(config.get(ConfigType.WORKSPACE_BASE)) / 'subdir' / 'test.txt'
    )
    assert (
        files.resolve_path(Path(SANDBOX_PATH_PREFIX) / 'test.txt', '/workspace')
        == Path(config.get(ConfigType.WORKSPACE_BASE)) / 'test.txt'
    )
    assert (
        files.resolve_path(
            Path(SANDBOX_PATH_PREFIX) / 'subdir' / 'test.txt', '/workspace'
        )
        == Path(config.get(ConfigType.WORKSPACE_BASE)) / 'subdir' / 'test.txt'
    )
    assert (
        files.resolve_path(
            Path(SANDBOX_PATH_PREFIX) / 'subdir' / '..' / 'test.txt', '/workspace'
        )
        == Path(config.get(ConfigType.WORKSPACE_BASE)) / 'test.txt'
    )
    with pytest.raises(PermissionError):
        files.resolve_path(Path(SANDBOX_PATH_PREFIX) / '..' / 'test.txt', '/workspace')
    with pytest.raises(PermissionError):
        files.resolve_path(Path('..') / 'test.txt', '/workspace')
    with pytest.raises(PermissionError):
        files.resolve_path(Path('/') / 'test.txt', '/workspace')
    assert (
        files.resolve_path('test.txt', '/workspace/test')
        == Path(config.get(ConfigType.WORKSPACE_BASE)) / 'test' / 'test.txt'
    )
