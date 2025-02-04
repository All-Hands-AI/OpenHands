from __future__ import annotations

import os
import shutil
from abc import ABC
from dataclasses import dataclass, field
from io import BytesIO, StringIO
from typing import Dict, List, Optional
from unittest import TestCase
from unittest.mock import patch

import botocore.exceptions
from google.api_core.exceptions import NotFound

from openhands.storage.files import FileStore
from openhands.storage.google_cloud import GoogleCloudFileStore
from openhands.storage.local import LocalFileStore
from openhands.storage.memory import InMemoryFileStore
from openhands.storage.s3 import S3FileStore


class _StorageTest(ABC):
    store: FileStore

    def get_store(self) -> FileStore:
        try:
            self.store.delete('')
        except Exception:
            pass
        return self.store

    def test_basic_fileops(self):
        filename = 'test.txt'
        store = self.get_store()
        store.write(filename, 'Hello, world!')
        self.assertEqual(store.read(filename), 'Hello, world!')
        self.assertEqual(store.list(''), [filename])
        store.delete(filename)
        with self.assertRaises(FileNotFoundError):
            store.read(filename)

    def test_complex_path_fileops(self):
        filenames = ['foo.bar.baz', './foo/bar/baz', 'foo/bar/baz', '/foo/bar/baz']
        store = self.get_store()
        for filename in filenames:
            store.write(filename, 'Hello, world!')
            self.assertEqual(store.read(filename), 'Hello, world!')
            store.delete(filename)
            with self.assertRaises(FileNotFoundError):
                store.read(filename)

    def test_list(self):
        store = self.get_store()
        store.write('foo.txt', 'Hello, world!')
        store.write('bar.txt', 'Hello, world!')
        store.write('baz.txt', 'Hello, world!')
        file_names = store.list('')
        file_names.sort()
        self.assertEqual(file_names, ['bar.txt', 'baz.txt', 'foo.txt'])
        store.delete('foo.txt')
        store.delete('bar.txt')
        store.delete('baz.txt')

    def test_deep_list(self):
        store = self.get_store()
        store.write('foo/bar/baz.txt', 'Hello, world!')
        store.write('foo/bar/qux.txt', 'Hello, world!')
        store.write('foo/bar/quux.txt', 'Hello, world!')
        self.assertEqual(store.list(''), ['foo/'])
        self.assertEqual(store.list('foo'), ['foo/bar/'])
        file_names = store.list('foo/bar')
        file_names.sort()
        self.assertEqual(
            file_names, ['foo/bar/baz.txt', 'foo/bar/quux.txt', 'foo/bar/qux.txt']
        )
        store.delete('foo/bar/baz.txt')
        store.delete('foo/bar/qux.txt')
        store.delete('foo/bar/quux.txt')

    def test_directory_deletion(self):
        store = self.get_store()
        # Create a directory structure
        store.write('foo/bar/baz.txt', 'Hello, world!')
        store.write('foo/bar/qux.txt', 'Hello, world!')
        store.write('foo/other.txt', 'Hello, world!')
        store.write('foo/bar/subdir/file.txt', 'Hello, world!')

        # Verify initial structure
        self.assertEqual(store.list(''), ['foo/'])
        self.assertEqual(sorted(store.list('foo')), ['foo/bar/', 'foo/other.txt'])
        self.assertEqual(
            sorted(store.list('foo/bar')),
            ['foo/bar/baz.txt', 'foo/bar/qux.txt', 'foo/bar/subdir/'],
        )

        # Delete a directory
        store.delete('foo/bar')

        # Verify directory and its contents are gone, but other files remain
        self.assertEqual(store.list(''), ['foo/'])
        self.assertEqual(store.list('foo'), ['foo/other.txt'])

        # Delete root directory
        store.delete('foo')

        # Verify everything is gone
        self.assertEqual(store.list(''), [])


class TestLocalFileStore(TestCase, _StorageTest):
    def setUp(self):
        os.makedirs('./_test_files_tmp', exist_ok=True)
        self.store = LocalFileStore('./_test_files_tmp')

    def tearDown(self):
        shutil.rmtree('./_test_files_tmp')


class TestInMemoryFileStore(TestCase, _StorageTest):
    def setUp(self):
        self.store = InMemoryFileStore()


class TestGoogleCloudFileStore(TestCase, _StorageTest):
    def setUp(self):
        with patch('google.cloud.storage.Client', _MockGoogleCloudClient):
            self.store = GoogleCloudFileStore('dear-liza')


class TestS3FileStore(TestCase, _StorageTest):
    def setUp(self):
        with patch('boto3.client', lambda service, **kwargs: _MockS3Client()):
            self.store = S3FileStore('dear-liza')


# I would have liked to use cloud-storage-mocker here but the python versions were incompatible :(
# If we write tests for the S3 storage class I would definitely recommend we use moto.
class _MockGoogleCloudClient:
    def bucket(self, name: str):
        assert name == 'dear-liza'
        return _MockGoogleCloudBucket()


@dataclass
class _MockGoogleCloudBucket:
    blobs_by_path: Dict[str, _MockGoogleCloudBlob] = field(default_factory=dict)

    def blob(self, path: Optional[str] = None) -> _MockGoogleCloudBlob:
        return self.blobs_by_path.get(path) or _MockGoogleCloudBlob(self, path)

    def list_blobs(self, prefix: Optional[str] = None) -> List[_MockGoogleCloudBlob]:
        blobs = list(self.blobs_by_path.values())
        if prefix and prefix != '/':
            blobs = [blob for blob in blobs if blob.name.startswith(prefix)]
        return blobs


@dataclass
class _MockGoogleCloudBlob:
    bucket: _MockGoogleCloudBucket
    name: str
    content: Optional[str | bytes] = None

    def open(self, op: str):
        if op == 'r':
            if self.content is None:
                raise FileNotFoundError()
            return StringIO(self.content)
        if op == 'w':
            return _MockGoogleCloudBlobWriter(self)

    def delete(self):
        if self.name not in self.bucket.blobs_by_path:
            raise NotFound('Blob not found')
        del self.bucket.blobs_by_path[self.name]


@dataclass
class _MockGoogleCloudBlobWriter:
    blob: _MockGoogleCloudBlob
    content: str | bytes = None

    def __enter__(self):
        return self

    def write(self, __b):
        assert (
            self.content is None
        )  # We don't support buffered writes in this mock for now, as it is not needed
        self.content = __b

    def __exit__(self, exc_type, exc_val, exc_tb):
        blob = self.blob
        blob.content = self.content
        blob.bucket.blobs_by_path[blob.name] = blob


class _MockS3Client:
    def __init__(self):
        self.objects_by_bucket: Dict[str, Dict[str, _MockS3Object]] = {}

    def put_object(self, Bucket: str, Key: str, Body: str | bytes) -> None:
        if Bucket not in self.objects_by_bucket:
            self.objects_by_bucket[Bucket] = {}
        self.objects_by_bucket[Bucket][Key] = _MockS3Object(Key, Body)

    def get_object(self, Bucket: str, Key: str) -> Dict:
        if Bucket not in self.objects_by_bucket:
            raise botocore.exceptions.ClientError(
                {
                    'Error': {
                        'Code': 'NoSuchBucket',
                        'Message': f"The bucket '{Bucket}' does not exist",
                    }
                },
                'GetObject',
            )
        if Key not in self.objects_by_bucket[Bucket]:
            raise botocore.exceptions.ClientError(
                {
                    'Error': {
                        'Code': 'NoSuchKey',
                        'Message': f"The specified key '{Key}' does not exist",
                    }
                },
                'GetObject',
            )
        content = self.objects_by_bucket[Bucket][Key].content
        if isinstance(content, bytes):
            return {'Body': BytesIO(content)}
        return {'Body': StringIO(content)}

    def list_objects_v2(self, Bucket: str, Prefix: str = '') -> Dict:
        if Bucket not in self.objects_by_bucket:
            raise botocore.exceptions.ClientError(
                {
                    'Error': {
                        'Code': 'NoSuchBucket',
                        'Message': f"The bucket '{Bucket}' does not exist",
                    }
                },
                'ListObjectsV2',
            )
        objects = self.objects_by_bucket[Bucket]
        contents = [
            {'Key': key}
            for key in objects.keys()
            if not Prefix or key.startswith(Prefix)
        ]
        return {'Contents': contents} if contents else {}

    def delete_object(self, Bucket: str, Key: str) -> None:
        if Bucket not in self.objects_by_bucket:
            raise botocore.exceptions.ClientError(
                {
                    'Error': {
                        'Code': 'NoSuchBucket',
                        'Message': f"The bucket '{Bucket}' does not exist",
                    }
                },
                'DeleteObject',
            )
        self.objects_by_bucket[Bucket].pop(Key, None)


@dataclass
class _MockS3Object:
    key: str
    content: str | bytes
