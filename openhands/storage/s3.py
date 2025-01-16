import os
from typing import Optional

import boto3
import botocore

from openhands.storage.files import FileStore


class S3FileStore(FileStore):
    def __init__(self, bucket_name: Optional[str] = None) -> None:
        if bucket_name is None:
            bucket_name = os.environ['FILE_STORE_BUCKET']
        self.bucket = bucket_name
        self.client = boto3.client('s3')

    def write(self, path: str, contents: str) -> None:
        try:
            self.client.put_object(Bucket=self.bucket, Key=path, Body=contents)
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
