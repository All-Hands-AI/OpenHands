import base64
import io
import tarfile
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import requests

from openhands.core.logger import openhands_logger
from openhands.runtime.image_source.build_image_source import BuildImageSource
from openhands.runtime.image_source.image_source_abc import ImageSourceABC
from openhands.runtime.utils.request import send_request_with_retry
from openhands.runtime.utils.shutdown_listener import (
    should_continue,
    sleep_if_should_continue,
)
from openhands.utils.async_utils import sync_from_async


@dataclass
class RemoteImageSource(ImageSourceABC):
    api_url: str
    key: str
    target_image_tag: Optional[str] = field(default=None)
    session: requests.Session = field(default_factory=requests.Session)

    async def get_image(self) -> str:
        source = BuildImageSource(
            docker_client=None  # Forcing none here because we don't actually interract with docker.
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            source.build_project(temp_path)
            source.unzip_tarball(temp_path)
            source.create_dockerfile(temp_path)
            payload = self.create_payload(temp_path)
            build_id = await self.begin_build(payload)
            image = await self.wait_for_build(build_id)
            return image

        # Do a regular build but without the docker portion!
        # Instead, upload to the build

    def create_payload(self, path: Path):
        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode='w:gz') as tar:
            tar.add(path, arcname='.')
        tar_buffer.seek(0)

        # Encode the tar file as base64
        base64_encoded_tar = base64.b64encode(tar_buffer.getvalue()).decode('utf-8')

        # Prepare the multipart form data
        payload = [
            ('context', ('context.tar.gz', base64_encoded_tar)),
            ('target_image', (None, self.target_image_tag)),
        ]
        return payload

    async def begin_build(self, payload) -> str:
        # Send the POST request to /build (Begins the build process)
        response = await sync_from_async(
            send_request_with_retry,
            self.session,
            'POST',
            f'{self.api_url}/build',
            files=payload,
            timeout=30,
        )

        if response.status_code != 202:
            openhands_logger.error(f'Build initiation failed: {response.text}')
            raise RuntimeError(f'Build initiation failed: {response.text}')

        build_data = response.json()
        build_id = build_data['build_id']
        openhands_logger.info(f'Build initiated with ID: {build_id}')
        return build_id

    async def wait_for_build(self, build_id: str):
        # Poll /build_status until the build is complete
        start_time = time.time()
        timeout = 30 * 60  # 20 minutes in seconds
        while should_continue():
            if time.time() - start_time > timeout:
                openhands_logger.error('Build timed out after 30 minutes')
                raise RuntimeError('Build timed out after 30 minutes')

            status_response = await sync_from_async(
                send_request_with_retry,
                self.session,
                'GET',
                f'{self.api_url}/build_status',
                params={'build_id': build_id},
                timeout=30,
            )

            if status_response.status_code != 200:
                openhands_logger.error(
                    f'Failed to get build status: {status_response.text}'
                )
                raise RuntimeError(
                    f'Failed to get build status: {status_response.text}'
                )

            status_data = status_response.json()
            status = status_data['status']
            openhands_logger.info(f'Build status: {status}')

            if status == 'SUCCESS':
                openhands_logger.info(f"Successfully built {status_data['image']}")
                return status_data['image']
            elif status in [
                'FAILURE',
                'INTERNAL_ERROR',
                'TIMEOUT',
                'CANCELLED',
                'EXPIRED',
            ]:
                error_message = status_data.get(
                    'error', f'Build failed with status: {status}'
                )
                openhands_logger.error(error_message)
                raise RuntimeError(error_message)

            # Wait before polling again
            sleep_if_should_continue(30)

        raise RuntimeError('Build interrupted (likely received SIGTERM or SIGINT).')
