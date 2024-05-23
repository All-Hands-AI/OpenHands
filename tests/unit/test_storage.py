import os
import shutil

import pytest

from opendevin.storage.local import LocalFileStore
from opendevin.storage.memory import InMemoryFileStore


@pytest.fixture
def setup_env():
    os.makedirs('./_test_files_tmp', exist_ok=True)

    yield

    shutil.rmtree('./_test_files_tmp')


def test_basic_fileops(setup_env):
    filename = 'test.txt'
    for store in [LocalFileStore('./_test_files_tmp'), InMemoryFileStore()]:
        store.write(filename, 'Hello, world!')
        assert store.read(filename) == 'Hello, world!'
        assert store.list('') == [filename]
        store.delete(filename)
        with pytest.raises(FileNotFoundError):
            store.read(filename)


def test_complex_path_fileops(setup_env):
    filenames = ['foo.bar.baz', './foo/bar/baz', 'foo/bar/baz', '/foo/bar/baz']
    for store in [LocalFileStore('./_test_files_tmp'), InMemoryFileStore()]:
        for filename in filenames:
            store.write(filename, 'Hello, world!')
            assert store.read(filename) == 'Hello, world!'
            store.delete(filename)
            with pytest.raises(FileNotFoundError):
                store.read(filename)


def test_list(setup_env):
    for store in [LocalFileStore('./_test_files_tmp'), InMemoryFileStore()]:
        store.write('foo.txt', 'Hello, world!')
        store.write('bar.txt', 'Hello, world!')
        store.write('baz.txt', 'Hello, world!')
        assert store.list('').sort() == ['foo.txt', 'bar.txt', 'baz.txt'].sort()
        store.delete('foo.txt')
        store.delete('bar.txt')
        store.delete('baz.txt')


def test_deep_list(setup_env):
    for store in [LocalFileStore('./_test_files_tmp'), InMemoryFileStore()]:
        store.write('foo/bar/baz.txt', 'Hello, world!')
        store.write('foo/bar/qux.txt', 'Hello, world!')
        store.write('foo/bar/quux.txt', 'Hello, world!')
        assert store.list('') == ['foo/'], f'for class {store.__class__}'
        assert store.list('foo') == ['foo/bar/']
        assert (
            store.list('foo/bar').sort()
            == ['foo/bar/baz.txt', 'foo/bar/qux.txt', 'foo/bar/quux.txt'].sort()
        )
        store.delete('foo/bar/baz.txt')
        store.delete('foo/bar/qux.txt')
        store.delete('foo/bar/quux.txt')
