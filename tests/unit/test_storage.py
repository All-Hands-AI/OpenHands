import os

import pytest

from opendevin.storage.local import LocalFileStore
from opendevin.storage.memory import InMemoryFileStore


def test_basic_fileops():
    filename = 'test.txt'
    for store in [LocalFileStore('./_test_files_tmp'), InMemoryFileStore()]:
        store.write(filename, 'Hello, world!')
        assert store.read(filename) == 'Hello, world!'
        store.delete(filename)
        with pytest.raises(FileNotFoundError):
            store.read(filename)
    os.rmdir('./_test_files_tmp')


def test_complex_path_fileops():
    filenames = ['foo.bar.baz', './foo/bar/baz', 'foo/bar/baz', '/foo/bar/baz']
    for store in [LocalFileStore('./_test_files_tmp'), InMemoryFileStore()]:
        for filename in filenames:
            store.write(filename, 'Hello, world!')
            assert store.read(filename) == 'Hello, world!'
            store.delete(filename)
            with pytest.raises(FileNotFoundError):
                store.read(filename)
    os.rmdir('./_test_files_tmp/foo/bar')
    os.rmdir('./_test_files_tmp/foo')
    os.rmdir('./_test_files_tmp')
