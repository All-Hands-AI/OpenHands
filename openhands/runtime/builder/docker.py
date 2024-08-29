import docker

from openhands.core.logger import openhands_logger as logger
from openhands.runtime.builder.base import RuntimeBuilder


class DockerRuntimeBuilder(RuntimeBuilder):
    def __init__(self, docker_client: docker.DockerClient):
        self.docker_client = docker_client

    def build(self, path: str, tags: list[str]) -> str:
        target_image_hash_name = tags[0]
        target_image_repo, target_image_hash_tag = target_image_hash_name.split(':')
        target_image_tag = tags[1].split(':')[1] if len(tags) > 1 else None

        try:
            build_logs = self.docker_client.api.build(
                path=path,
                tag=target_image_hash_name,
                rm=True,
                decode=True,
            )
        except docker.errors.BuildError as e:
            logger.error(f'Sandbox image build failed: {e}')
            raise RuntimeError(f'Sandbox image build failed: {e}')

        for log in build_logs:
            if 'stream' in log:
                logger.info(log['stream'].strip())
            elif 'error' in log:
                logger.error(log['error'].strip())
            else:
                logger.info(str(log))

        logger.info(f'Image [{target_image_hash_name}] build finished.')

        assert (
            target_image_tag
        ), f'Expected target image tag [{target_image_tag}] is None'
        image = self.docker_client.images.get(target_image_hash_name)
        image.tag(target_image_repo, target_image_tag)
        logger.info(
            f'Re-tagged image [{target_image_hash_name}] with more generic tag [{target_image_tag}]'
        )

        # Check if the image is built successfully
        image = self.docker_client.images.get(target_image_hash_name)
        if image is None:
            raise RuntimeError(
                f'Build failed: Image {target_image_hash_name} not found'
            )

        tags_str = (
            f'{target_image_hash_tag}, {target_image_tag}'
            if target_image_tag
            else target_image_hash_tag
        )
        logger.info(
            f'Image {target_image_repo} with tags [{tags_str}] built successfully'
        )
        return target_image_hash_name

    def image_exists(self, image_name: str) -> bool:
        """Check if the image exists in the registry (try to pull it first) or in the local store.

        Args:
            image_name (str): The Docker image to check (<image repo>:<image tag>)
        Returns:
            bool: Whether the Docker image exists in the registry or in the local store
        """
        try:
            logger.info(f'Checking, if image {image_name} exists locally.')
            self.docker_client.images.get(image_name)
            logger.info(f'Image {image_name} found locally.')
            return True
        except docker.errors.ImageNotFound:
            try:
                logger.info(
                    'Image not found locally. Trying to pull it, please wait...'
                )
                self.docker_client.images.pull(image_name)
                logger.info(f'Image {image_name} pulled successfully.')
                return True
            except docker.errors.ImageNotFound:
                logger.info('Could not find image locally or in registry.')
                return False
            except Exception:
                logger.info('Could not pull image directly.')
                return False
