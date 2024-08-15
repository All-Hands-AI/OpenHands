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
        self.session = requests.Session()
        self.session.headers.update({'X-API-Key': self.api_key})

    def build(self, path: str, tags: list[str]) -> str:
        """Builds a Docker image using the Runtime API's /build endpoint."""
        # Create a tar archive of the build context
        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode='w:gz') as tar:
            tar.add(path, arcname='.')
        tar_buffer.seek(0)

        # Prepare the request payload
        payload = {
            'context': tar_buffer.getvalue(),
            'target_image': tags[0],
            'tags': tags[1:],  # Exclude the first tag as it's already the target_image
        }

        # Send the POST request
        response = self.session.post(f'{self.api_url}/build', json=payload)
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
        response = self.session.get(f'{self.api_url}/image_exists', params=params)

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
