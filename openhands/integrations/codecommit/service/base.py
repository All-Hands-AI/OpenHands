
"""Base mixin for AWS CodeCommit service."""

from __future__ import annotations

import boto3
from botocore.exceptions import ClientError
from pydantic import SecretStr

from openhands.core.logger import openhands_logger as logger
from openhands.integrations.provider import ProviderToken


class CodeCommitBaseMixin:
    """Base mixin for AWS CodeCommit service."""

    def __init__(
        self,
        token: ProviderToken | SecretStr | None = None,
        base_domain: str | None = None,
    ) -> None:
        """Initialize the CodeCommit service.

        Args:
            token: The AWS access key ID and secret access key
            base_domain: The AWS region
        """
        self.token = token
        self.region = base_domain or 'us-east-1'  # Default to us-east-1 if no region specified
        
        # Initialize boto3 client
        self._init_client()

    def _init_client(self) -> None:
        """Initialize the boto3 client for CodeCommit."""
        if isinstance(self.token, ProviderToken):
            # Extract access key and secret key from ProviderToken
            access_key = self.token.token.get_secret_value() if self.token.token else None
            secret_key = self.token.secret.get_secret_value() if self.token.secret else None
            region = self.token.host or self.region
            
            self.client = boto3.client(
                'codecommit',
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region
            )
        elif isinstance(self.token, SecretStr):
            # If only access key is provided (not recommended)
            logger.warning("Using only access key for AWS CodeCommit is not recommended")
            self.client = boto3.client(
                'codecommit',
                aws_access_key_id=self.token.get_secret_value(),
                region_name=self.region
            )
        else:
            # Use default credentials from environment or config
            self.client = boto3.client('codecommit', region_name=self.region)

    async def get_user(self) -> dict:
        """Get the current user information.
        
        AWS CodeCommit doesn't have a direct equivalent to get user info,
        so we'll return the caller identity from STS.
        """
        try:
            # Use STS to get caller identity
            sts_client = boto3.client(
                'sts',
                aws_access_key_id=self.token.token.get_secret_value() if isinstance(self.token, ProviderToken) and self.token.token else None,
                aws_secret_access_key=self.token.secret.get_secret_value() if isinstance(self.token, ProviderToken) and self.token.secret else None,
                region_name=self.region
            )
            
            identity = sts_client.get_caller_identity()
            return {
                'id': identity['UserId'],
                'username': identity['Arn'].split('/')[-1],
                'name': identity['Arn'].split('/')[-1],
                'email': None,  # AWS doesn't provide email through this API
            }
        except ClientError as e:
            logger.error(f"Failed to get AWS identity: {e}")
            raise
