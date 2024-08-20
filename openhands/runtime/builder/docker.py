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
                print(log['stream'].strip())
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
        """Check if the image exists in the registry (try to pull it first) AND in the local store.

        Args:
            image_name (str): The Docker image to check (<image repo>:<image tag>)
        Returns:
            bool: Whether the Docker image exists in the registry and in the local store
        """
        # Try to pull the Docker image from the registry
        try:
            self.docker_client.images.pull(image_name)
        except Exception:
            logger.info(f'Cannot pull image {image_name} directly')

        images = self.docker_client.images.list()
        if images:
            for image in images:
                if image_name in image.tags:
                    return True
        return False
