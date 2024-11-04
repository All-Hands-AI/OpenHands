import io
import os
from functools import wraps
from minio import Minio
from openhands.storage.files import FileStore

def s3_operation(func):
    @wraps(func)
    def wrapper(self, path: str, *args, **kwargs):
        try:
            return func(self, path, *args, **kwargs)
        except Exception as e:
            operation = func.__name__
            raise FileNotFoundError(f'Failed to {operation} S3 {"object" if operation != "list" else "objects"} at path {path}: {e}')
    return wrapper

class S3FileStore(FileStore):
    def __init__(self) -> None:
        access_key = os.getenv('AWS_ACCESS_KEY_ID')
        secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        endpoint = os.getenv('AWS_S3_ENDPOINT', 's3.amazonaws.com')
        secure = os.getenv('AWS_S3_SECURE', 'true').lower() == 'true'
        self.bucket = os.getenv('AWS_S3_BUCKET')
        self.client = Minio(endpoint, access_key, secret_key, secure=secure)

    @s3_operation
    def write(self, path: str, contents: str) -> None:
        as_bytes = contents.encode('utf-8')
        stream = io.BytesIO(as_bytes)
        self.client.put_object(self.bucket, path, stream, len(as_bytes))

    @s3_operation
    def read(self, path: str) -> str:
        return self.client.get_object(self.bucket, path).data.decode('utf-8')

    @s3_operation
    def list(self, path: str) -> list[str]:
        return [obj.object_name for obj in self.client.list_objects(self.bucket, path)]

    @s3_operation
    def delete(self, path: str) -> None:
        self.client.remove_object(self.bucket, path)

