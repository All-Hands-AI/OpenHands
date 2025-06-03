import os

import requests

from openhands.core.logger import openhands_logger as logger


class Imagen:
    def __init__(self):
        self.base_url = os.getenv('IMAGEN_SERVICE_BASE_URL')
        if not self.base_url:
            logger.warning(
                'IMAGEN_SERVICE_BASE_URL environment variable is not set. Branding functionality will be disabled.'
            )

    def annotate_branding_into_base64_image(self, base64_image: str) -> str:
        if not base64_image or not isinstance(base64_image, str):
            logger.error('Invalid base64_image input. Must be a non-empty string.')
            return base64_image

        endpoint = f'{self.base_url}/watermark-base64'
        try:
            body = {'image_base64': base64_image, 'watermark_type': 'v3'}
            response = requests.post(endpoint, json=body, timeout=30)

            if response.status_code == 200:
                return response.json()['image_base64']
            else:
                logger.error(f'Error annotating branding into image: {response.text}')
                return base64_image
        except Exception as e:
            logger.error(f'Error annotating branding into image: {e}')
            # if some thing gone wrong, return the original image
            return base64_image
