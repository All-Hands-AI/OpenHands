import base64
import io
import tarfile

import requests

from opendevin.core.logger import opendevin_logger as logger
from opendevin.runtime.builder import RuntimeBuilder


class RemoteRuntimeBuilder(RuntimeBuilder):
    """This class interacts with the remote Runtime API for building and managing container images."""

    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url
        self.api_key = api_key

    def build(self, path: str, tags: list[str]) -> str:
        """Builds a Docker image using the Runtime API's /build endpoint."""
        # Create a tar archive of the build context
        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode='w:gz') as tar:
            tar.add(path, arcname='.')
        tar_buffer.seek(0)

        # Encode the tar file as base64
        base64_encoded_tar = base64.b64encode(tar_buffer.getvalue()).decode('utf-8')

        # Prepare the multipart form data
        files = [
            ('context', ('context.tar.gz', base64_encoded_tar)),
            ('target_image', (None, tags[0])),
        ]

        # Add additional tags if present
        for tag in tags[1:]:
            files.append(('tags', (None, tag)))

        # Send the POST request
        headers = {'X-API-Key': self.api_key}
        response = requests.post(f'{self.api_url}/build', files=files, headers=headers)

        if response.status_code != 200:
            logger.error(f'Build failed: {response.text}')
            raise RuntimeError(f'Build failed: {response.text}')

        result = response.json()

        logger.info(f"Successfully built {result['image']}")
        logger.info(f"Build status: {result['status']}")

        return result['image']

    def image_exists(self, image_name: str) -> bool:
        """Checks if an image exists in the remote registry using the /image_exists endpoint."""
        params = {'image': image_name}
        session = requests.Session()
        session.headers.update({'X-API-Key': self.api_key})
        response = session.get(f'{self.api_url}/image_exists', params=params)

        if response.status_code != 200:
            logger.error(f'Failed to check image existence: {response.text}')
            raise RuntimeError(f'Failed to check image existence: {response.text}')

        result = response.json()

        if result['exists']:
            logger.info(
                f"Image {image_name} exists. Created at: {result['created_at']}, Size: {result['size']}"
            )
        else:
            logger.info(f'Image {image_name} does not exist.')

        return result['exists']
