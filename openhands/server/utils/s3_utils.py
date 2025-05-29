import asyncio
import logging
import mimetypes
import os
from typing import Optional

import boto3
from botocore.endpoint import uuid
from botocore.exceptions import ClientError
from fastapi import UploadFile

logger = logging.getLogger(__name__)


class S3Handler:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('S3_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('S3_SECRET_ACCESS_KEY'),
            region_name=os.getenv('S3_REGION', 'ap-southeast-1'),
        )
        self.bucket_name = os.getenv('S3_BUCKET')

    def _get_content_type(self, filename: str) -> str:
        """Determine the content type based on file extension."""
        content_type, _ = mimetypes.guess_type(filename)
        if content_type is None:
            # Default content types for common file extensions
            ext = os.path.splitext(filename)[1].lower()
            content_type_map = {
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.gif': 'image/gif',
                '.webp': 'image/webp',
                '.pdf': 'application/pdf',
                '.mp4': 'video/mp4',
                '.webm': 'video/webm',
                '.ogg': 'video/ogg',
                '.txt': 'text/plain',
                '.json': 'application/json',
                '.zip': 'application/zip',
            }
            content_type = content_type_map.get(ext, 'application/octet-stream')
        return content_type

    async def upload_raw_file(
        self, file_content: bytes, folder_path: str, filename: str
    ):
        try:
            content_type = self._get_content_type(filename)
            logger.info(f'Content type: {content_type}')
            s3_key = f'{folder_path}/{filename}' if folder_path else filename
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType=content_type,
            )
            s3_url = f'https://{self.bucket_name}.s3.amazonaws.com/{s3_key}'
            return s3_url
        except ClientError as e:
            logger.error(f'Error uploading file to S3: {str(e)}')
            return None
        except Exception as e:
            logger.error(f'Unexpected error uploading to S3: {str(e)}')
            return None

    async def upload_file(
        self, file: UploadFile, folder_path: str, filename: Optional[str] = None
    ):
        """
        Upload a file to S3 bucket

        Args:
            file: The file to upload
            folder_path: The folder path in S3 bucket
            filename: Optional custom filename, if not provided uses original filename

        Returns:
            str: The S3 URL of the uploaded file if successful, None otherwise
        """
        try:
            if not filename:
                # check ext of file
                extension = os.path.splitext(file.filename)[1]
                filename = f'{uuid.uuid4().hex}{extension}'

            # Ensure folder path doesn't start with /
            folder_path = folder_path.lstrip('/')

            s3_key = f'{folder_path}/{filename}' if folder_path else filename

            content = await file.read()

            await file.seek(0)

            # Run boto3 (synchronous) in a thread pool
            await asyncio.to_thread(
                self.s3_client.put_object,
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=content,
            )

            # Generate the S3 URL
            s3_url = f'https://{self.bucket_name}.s3.amazonaws.com/{s3_key}'
            logger.info(f'File uploaded successfully to {s3_url}')
            return s3_url

        except ClientError as e:
            logger.error(f'Error uploading file to S3: {str(e)}')
            return None
        except Exception as e:
            logger.error(f'Unexpected error uploading to S3: {str(e)}')
            return None
        finally:
            # Close the file
            await file.close()

    def generate_presigned_url(
        self, s3_key: str, expiration: int = 3600
    ) -> Optional[str]:
        """
        Generate a presigned URL for an S3 object

        Args:
            s3_key: The S3 key (path) of the object
            expiration: URL expiration time in seconds (default 1 hour)

        Returns:
            str: Presigned URL if successful, None otherwise
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': s3_key},
                ExpiresIn=expiration,
            )
            return url
        except ClientError as e:
            logger.error(f'Error generating presigned URL: {str(e)}')
            return None
