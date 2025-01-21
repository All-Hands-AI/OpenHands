import os

import boto3
import botocore

from openhands.storage.files import FileStore


class S3FileStore(FileStore):
    def __init__(self, bucket_name: str | None) -> None:
        access_key = os.getenv('AWS_ACCESS_KEY_ID')
        secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        endpoint = os.getenv('AWS_S3_ENDPOINT')
        secure = os.getenv('AWS_S3_SECURE', 'true').lower() == 'true'
        if bucket_name is None:
            bucket_name = os.environ['AWS_S3_BUCKET']
        self.bucket = bucket_name
        self.client = boto3.client(
            's3',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            endpoint_url=endpoint,
            use_ssl=secure,
        )

    def write(self, path: str, contents: str | bytes) -> None:
        try:
            as_bytes = (
                contents.encode('utf-8') if isinstance(contents, str) else contents
            )
            self.client.put_object(Bucket=self.bucket, Key=path, Body=as_bytes)
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'AccessDenied':
                raise FileNotFoundError(
                    f"Error: Access denied to bucket '{self.bucket}'."
                )
            elif e.response['Error']['Code'] == 'NoSuchBucket':
                raise FileNotFoundError(
                    f"Error: The bucket '{self.bucket}' does not exist."
                )
            raise FileNotFoundError(
                f"Error: Failed to write to bucket '{self.bucket}' at path {path}: {e}"
            )

    def read(self, path: str) -> str:
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=path)
            return response['Body'].read().decode('utf-8')
        except botocore.exceptions.ClientError as e:
            # Catch all S3-related errors
            if e.response['Error']['Code'] == 'NoSuchBucket':
                raise FileNotFoundError(
                    f"Error: The bucket '{self.bucket}' does not exist."
                )
            elif e.response['Error']['Code'] == 'NoSuchKey':
                raise FileNotFoundError(
                    f"Error: The object key '{path}' does not exist in bucket '{self.bucket}'."
                )
            else:
                raise FileNotFoundError(
                    f"Error: Failed to read from bucket '{self.bucket}' at path {path}: {e}"
                )
        except Exception as e:
            raise FileNotFoundError(
                f"Error: Failed to read from bucket '{self.bucket}' at path {path}: {e}"
            )

    def list(self, path: str) -> list[str]:
        if path and path != '/' and not path.endswith('/'):
            path += '/'
        try:
            response = self.client.list_objects_v2(Bucket=self.bucket, Prefix=path)
            # Check if 'Contents' exists in the response
            if 'Contents' in response:
                objects = [obj['Key'] for obj in response['Contents']]
                return objects
            else:
                return list()
        except botocore.exceptions.ClientError as e:
            # Catch all S3-related errors
            if e.response['Error']['Code'] == 'NoSuchBucket':
                raise FileNotFoundError(
                    f"Error: The bucket '{self.bucket}' does not exist."
                )
            elif e.response['Error']['Code'] == 'AccessDenied':
                raise FileNotFoundError(
                    f"Error: Access denied to bucket '{self.bucket}'."
                )
            else:
                raise FileNotFoundError(f"Error: {e.response['Error']['Message']}")
        except Exception as e:
            raise FileNotFoundError(
                f"Error: Failed to read from bucket '{self.bucket}' at path {path}: {e}"
            )

    def delete(self, path: str) -> None:
        try:
            self.client.delete_object(Bucket=self.bucket, Key=path)
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchBucket':
                raise FileNotFoundError(
                    f"Error: The bucket '{self.bucket}' does not exist."
                )
            elif e.response['Error']['Code'] == 'AccessDenied':
                raise FileNotFoundError(
                    f"Error: Access denied to bucket '{self.bucket}'."
                )
            elif e.response['Error']['Code'] == 'NoSuchKey':
                raise FileNotFoundError(
                    f"Error: The object key '{path}' does not exist in bucket '{self.bucket}'."
                )
            else:
                raise FileNotFoundError(
                    f"Error: Failed to delete key '{path}' from bucket '{self.bucket}': {e}"
                )
        except Exception as e:
            raise FileNotFoundError(
                f"Error: Failed to delete key '{path}' from bucket '{self.bucket}: {e}"
            )
