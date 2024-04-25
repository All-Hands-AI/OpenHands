from opendevin import config
from opendevin.action import fileop
from pathlib import Path
import pytest


def test_resolve_path():
    assert fileop.resolve_path('test.txt', '/workspace') == Path(config.get('WORKSPACE_BASE')) / 'test.txt'
    assert fileop.resolve_path('subdir/test.txt', '/workspace') == \
        Path(config.get('WORKSPACE_BASE')) / 'subdir' / 'test.txt'
    assert fileop.resolve_path(Path(fileop.SANDBOX_PATH_PREFIX) / 'test.txt', '/workspace') == \
        Path(config.get('WORKSPACE_BASE')) / 'test.txt'
    assert fileop.resolve_path(Path(fileop.SANDBOX_PATH_PREFIX) / 'subdir' / 'test.txt',
                               '/workspace') == Path(config.get('WORKSPACE_BASE')) / 'subdir' / 'test.txt'
    assert fileop.resolve_path(Path(fileop.SANDBOX_PATH_PREFIX) / 'subdir' / '..' / 'test.txt',
                               '/workspace') == Path(config.get('WORKSPACE_BASE')) / 'test.txt'
    with pytest.raises(PermissionError):
        fileop.resolve_path(Path(fileop.SANDBOX_PATH_PREFIX) / '..' / 'test.txt', '/workspace')
    with pytest.raises(PermissionError):
        fileop.resolve_path(Path('..') / 'test.txt', '/workspace')
    with pytest.raises(PermissionError):
        fileop.resolve_path(Path('/') / 'test.txt', '/workspace')
    assert fileop.resolve_path('test.txt', '/workspace/test') == \
        Path(config.get('WORKSPACE_BASE')) / 'test' / 'test.txt'
