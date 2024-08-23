from typing import List

from google.cloud import storage

from openhands.storage.files import FileStore


class GoogleCloudFileStore(FileStore):
    def __init__(self, bucket_name: str) -> None:
        """
        Create a new FileStore. If GOOGLE_APPLICATION_CREDENTIALS is defined in the
        environment it will be used for authentication. Otherwise access will be 
        anonymous.
        """
        self.storage_client = storage.Client()
        self.bucket = self.storage_client.bucket(bucket_name)

    def write(self, path: str, contents: str | bytes) -> None:
        blob = self.bucket.blob(path)
        with blob.open("w") as f:
            f.write(contents)

    def read(self, path: str) -> str:
        blob = self.bucket.blob(path)
        with blob.open("r") as f:
            return f.read()

    def list(self, path: str) -> List[str]:
        # The delimiter logic screens out directories, so we can't use it. :(
        # For example, given a structure:
        #   foo/bar/zap.txt
        #   foo/bar/bang.txt
        # prefix=None, delimiter="/" yields []
        # prefix="foo", delimiter="/" yields []
        blobs = set()
        for blob in self.bucket.list_blobs(prefix=path):
            name = blob.name
            try:
                index = name.index("/", len(path))
                name = name[:index]
            except ValueError:
                pass
            blobs.add(name)
        return list(blobs)


    def delete(self, path: str) -> None:
        self.bucket.delete(path)
