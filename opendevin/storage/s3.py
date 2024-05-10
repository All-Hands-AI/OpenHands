import os

from minio import Minio

from .files import FileStore

AWS_S3_ENDPOINT = 's3.amazonaws.com'


class S3FileStore(FileStore):
    def __init__(self, endpoint: str = AWS_S3_ENDPOINT) -> None:
        access_key = os.getenv('AWS_ACCESS_KEY_ID')
        secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        self.bucket = os.getenv('AWS_S3_BUCKET')
        self.client = Minio(endpoint, access_key, secret_key)

    def write(self, path: str, contents: str) -> None:
        self.client.put_object(self.bucket, path, contents)

    def read(self, path: str) -> str:
        return self.client.get_object(self.bucket, path).data.decode('utf-8')

    def list(self, path: str) -> list[str]:
        return [obj.object_name for obj in self.client.list_objects(self.bucket, path)]

    def delete(self, path: str) -> None:
        self.client.remove_object(self.bucket, path)
