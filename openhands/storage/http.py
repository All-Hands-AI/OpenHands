import json
import os
import urllib.parse
from typing import Union

import httpx
from requests.exceptions import RequestException

from openhands.core.logger import openhands_logger as logger
from openhands.storage.files import FileStore


class HTTPFileStore(FileStore):
    """
    A FileStore implementation that uses HTTP requests to store and retrieve files.

    This implementation allows storing files on a remote HTTP server that implements
    a simple REST API for file operations.

    The server should implement the following endpoints:
    - POST /files/{path} - Write a file
    - GET /files/{path} - Read a file
    - OPTIONS /files/{path} - List files in a directory
    - DELETE /files/{path} - Delete a file or directory

    Authentication can be provided via API key, basic auth, or bearer token.
    """
    base_url: str
    client: httpx.Client

    def __init__(
        self,
        base_url: str,
        client: httpx.Client | None = None,
    ) -> None:
        """
        Initialize the HTTP file store.

        Args:
            base_url: The base URL of the HTTP file server
            api_key: Optional API key for authentication
            username: Optional username for basic authentication
            password: Optional password for basic authentication
            bearer_token: Optional bearer token for authentication
            timeout: Request timeout in seconds
            verify_ssl: Whether to verify SSL certificates
        """
        self.base_url = base_url.rstrip('/')
        if not client:
            headers = {}
            if os.getenv('SESSION_API_KEY'):
                headers['X-Session-API-Key'] = os.getenv('SESSION_API_KEY')
            client = httpx.Client(headers=headers)
        self.client = client

    def _get_file_url(self, path: str) -> str:
        """
        Get the full URL for a file path.

        Args:
            path: The file path

        Returns:
            The full URL
        """
        # Ensure path starts with a slash
        if not path.startswith('/'):
            path = '/' + path

        # URL encode the path
        encoded_path = urllib.parse.quote(path)
        return f'{self.base_url}/files{encoded_path}'

    def write(self, path: str, contents: Union[str, bytes]) -> None:
        """
        Write contents to a file.

        Args:
            path: The file path
            contents: The file contents (string or bytes)

        Raises:
            FileNotFoundError: If the file cannot be written
        """
        url = self._get_file_url(path)

        try:
            # Convert string to bytes if needed
            if isinstance(contents, str):
                contents = contents.encode('utf-8')

            response = self.client.post(url, data=contents)

            if response.status_code not in (200, 201, 204):
                raise FileNotFoundError(
                    f'Error: Failed to write to path {path}. '
                    f'Status code: {response.status_code}, Response: {response.text}'
                )

            logger.debug(f'Successfully wrote to {path}')

        except RequestException as e:
            raise FileNotFoundError(f'Error: Failed to write to path {path}: {str(e)}')

    def read(self, path: str) -> str:
        """
        Read contents from a file.

        Args:
            path: The file path

        Returns:
            The file contents as a string

        Raises:
            FileNotFoundError: If the file cannot be read
        """
        url = self._get_file_url(path)

        try:
            response = self.client.get(url)

            if response.status_code != 200:
                raise FileNotFoundError(
                    f'Error: Failed to read from path {path}. '
                    f'Status code: {response.status_code}, Response: {response.text}'
                )

            return response.text

        except RequestException as e:
            raise FileNotFoundError(f'Error: Failed to read from path {path}: {str(e)}')

    def list(self, path: str) -> list[str]:
        """
        List files in a directory.

        Args:
            path: The directory path

        Returns:
            A list of file paths

        Raises:
            FileNotFoundError: If the directory cannot be listed
        """
        url = f'{self._get_file_url(path)}'

        try:
            response = self.client.options(url)

            if response.status_code != 200:
                if response.status_code == 404:
                    return []

                raise FileNotFoundError(
                    f'Error: Failed to list path {path}. '
                    f'Status code: {response.status_code}, Response: {response.text}'
                )

            try:
                files = response.json()
                if not isinstance(files, list):
                    raise FileNotFoundError(
                        f'Error: Invalid response format when listing path {path}. '
                        f'Expected a list, got: {type(files)}'
                    )
                return files
            except json.JSONDecodeError:
                raise FileNotFoundError(
                    f'Error: Invalid JSON response when listing path {path}. '
                    f'Response: {response.text}'
                )

        except RequestException as e:
            raise FileNotFoundError(f'Error: Failed to list path {path}: {str(e)}')

    def delete(self, path: str) -> None:
        """
        Delete a file or directory.

        Args:
            path: The file or directory path

        Raises:
            FileNotFoundError: If the file or directory cannot be deleted
        """
        url = self._get_file_url(path)

        try:
            response = self.client.delete(url)

            # 404 is acceptable for delete operations
            if response.status_code not in (200, 202, 204, 404):
                raise FileNotFoundError(
                    f'Error: Failed to delete path {path}. '
                    f'Status code: {response.status_code}, Response: {response.text}'
                )

            logger.debug(f'Successfully deleted {path}')

        except RequestException as e:
            raise FileNotFoundError(f'Error: Failed to delete path {path}: {str(e)}')
