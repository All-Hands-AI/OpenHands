from pathlib import Path

import pytest

from opendevin.config import config
from opendevin.action import fileop
from opendevin.schema import ConfigType


def test_resolve_path():
    assert fileop.resolve_path('test.txt', '/workspace') == Path(config.workspace_base) / 'test.txt'
    assert fileop.resolve_path('subdir/test.txt', '/workspace') == \
        Path(config.workspace_base) / 'subdir' / 'test.txt'
    assert fileop.resolve_path(Path(fileop.SANDBOX_PATH_PREFIX) / 'test.txt', '/workspace') == \
        Path(config.workspace_base) / 'test.txt'
    assert fileop.resolve_path(Path(fileop.SANDBOX_PATH_PREFIX) / 'subdir' / 'test.txt',
                               '/workspace') == Path(config.workspace_base) / 'subdir' / 'test.txt'
    assert fileop.resolve_path(Path(fileop.SANDBOX_PATH_PREFIX) / 'subdir' / '..' / 'test.txt',
                               '/workspace') == Path(config.workspace_base) / 'test.txt'
    with pytest.raises(PermissionError):
        fileop.resolve_path(Path(fileop.SANDBOX_PATH_PREFIX) / '..' / 'test.txt', '/workspace')
    with pytest.raises(PermissionError):
        fileop.resolve_path(Path('..') / 'test.txt', '/workspace')
    with pytest.raises(PermissionError):
        fileop.resolve_path(Path('/') / 'test.txt', '/workspace')
    assert fileop.resolve_path('test.txt', '/workspace/test') == \
        Path(config.workspace_base) / 'test' / 'test.txt'
