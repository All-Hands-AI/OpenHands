import os
from typing import List, Optional

from google.api_core.exceptions import NotFound
from google.cloud import storage

from openhands.storage.files import FileStore


class GoogleCloudFileStore(FileStore):
    def __init__(self, bucket_name: Optional[str] = None) -> None:
        """
        Create a new FileStore. If GOOGLE_APPLICATION_CREDENTIALS is defined in the
        environment it will be used for authentication. Otherwise access will be
        anonymous.
        """
        if bucket_name is None:
            bucket_name = os.environ['GOOGLE_CLOUD_BUCKET_NAME']
        self.storage_client = storage.Client()
        self.bucket = self.storage_client.bucket(bucket_name)

    def write(self, path: str, contents: str | bytes) -> None:
        blob = self.bucket.blob(path)
        mode = 'wb' if isinstance(contents, bytes) else 'w'
        with blob.open(mode) as f:
            f.write(contents)

    def read(self, path: str) -> str:
        blob = self.bucket.blob(path)
        try:
            with blob.open('r') as f:
                return f.read()
        except NotFound as err:
            raise FileNotFoundError(err)

    def list(self, path: str) -> List[str]:
        if not path or path == '/':
            path = ''
        elif not path.endswith('/'):
            path += '/'
        # The delimiter logic screens out directories, so we can't use it. :(
        # For example, given a structure:
        #   foo/bar/zap.txt
        #   foo/bar/bang.txt
        #   ping.txt
        # prefix=None, delimiter="/"   yields  ["ping.txt"]  # :(
        # prefix="foo", delimiter="/"  yields  []  # :(
        blobs = set()
        prefix_len = len(path)
        for blob in self.bucket.list_blobs(prefix=path):
            name = blob.name
            if name == path:
                continue
            try:
                index = name.index('/', prefix_len + 1)
                if index != prefix_len:
                    blobs.add(name[: index + 1])
            except ValueError:
                blobs.add(name)
        return list(blobs)

    def delete(self, path: str) -> None:
        blob = self.bucket.blob(path)
        blob.delete()
