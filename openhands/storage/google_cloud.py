import os

from minio import Minio

from openhands.storage.s3 import S3FileStore

GOOGLE_CLOUD_STORAGE_ENDPOINT = 'storage.googleapis.com'


class GoogleCloudFileStore(S3FileStore):
    def __init__(self, endpoint: str = GOOGLE_CLOUD_STORAGE_ENDPOINT) -> None:
        access_key = os.getenv('GOOGLE_CLOUD_STORAGE_ACCESS_KEY')
        secret_key = os.getenv('GOOGLE_CLOUD_STORAGE_SECRET_KEY')
        self.bucket = os.getenv('GOOGLE_CLOUD_STORAGE_BUCKET')
        self.client = Minio(endpoint, access_key, secret_key)
