from typing import Optional

from docker import DockerClient
from docker.errors import ImageNotFound
from docker.models.images import Image

from openhands.core.logger import openhands_logger


def get_local_image(
    image_name: str,
    docker_client: DockerClient,
) -> Optional[Image]:
    try:
        image = docker_client.images.get(image_name)
        openhands_logger.debug(f'image_exists_locally:{image_name}')
        return image
    except ImageNotFound:
        openhands_logger.info(f'image_does_not_exist_locally:{image_name}')
        return None


def pull_image(image_name: str, docker_client: DockerClient):
    openhands_logger.info(f'pulling_image:{image_name}')
    if ':' in image_name:
        image_repo, image_tag = image_name.split(':', 1)
    else:
        image_repo = image_name
        image_tag = None

    for line in docker_client.api.pull(
        image_repo, tag=image_tag, stream=True, decode=True
    ):
        progress_detail = line.get('progressDetail')
        if not progress_detail:
            continue
        current = progress_detail.get('current')
        total = progress_detail.get('total')
        if current and total:
            openhands_logger.debug('pull_progress:{current}/{total}')
    openhands_logger.info('image_pulled')
