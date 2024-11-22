import io
import os

from minio import Minio

from openhands.storage.files import FileStore


class S3FileStore(FileStore):
    def __init__(self) -> None:
        access_key = os.getenv('AWS_ACCESS_KEY_ID')
        secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        endpoint = os.getenv('AWS_S3_ENDPOINT', 's3.amazonaws.com')
        secure = os.getenv('AWS_S3_SECURE', 'true').lower() == 'true'
        self.bucket = os.getenv('AWS_S3_BUCKET')
        self.client = Minio(endpoint, access_key, secret_key, secure=secure)

    def write(self, path: str, contents: str) -> None:
        as_bytes = contents.encode('utf-8')
        stream = io.BytesIO(as_bytes)
        try:
            self.client.put_object(self.bucket, path, stream, len(as_bytes))
        except Exception as e:
            raise FileNotFoundError(f'Failed to write to S3 at path {path}: {e}')

    def read(self, path: str) -> str:
        try:
            return self.client.get_object(self.bucket, path).data.decode('utf-8')
        except Exception as e:
            raise FileNotFoundError(f'Failed to read from S3 at path {path}: {e}')

    def list(self, path: str) -> list[str]:
        if path and path != '/' and not path.endswith('/'):
            path += '/'
        try:
            return [
                obj.object_name for obj in self.client.list_objects(self.bucket, path)
            ]
        except Exception as e:
            raise FileNotFoundError(f'Failed to list S3 objects at path {path}: {e}')

    def delete(self, path: str) -> None:
        try:
            self.client.remove_object(self.bucket, path)
        except Exception as e:
            raise FileNotFoundError(f'Failed to delete S3 object at path {path}: {e}')
