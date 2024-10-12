import hashlib
import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import docker
from docker import DockerClient
from docker.models.images import Image

from openhands.core.logger import openhands_logger
from openhands.runtime.image_source.build_image_source import BuildImageSource
from openhands.runtime.image_source.image_source_abc import ImageSourceABC
from openhands.utils.docker_utils import get_local_image

INTERMEDIATE_NAME_PREFIX = 'oh-intermediate-'


@dataclass
class DevBuildImageSource(ImageSourceABC):
    """
    Image source for development where rebuilds are frequent, and caching as
    much as possible as an intermediate image makes sense
    """

    base_image_name: str = field(default='nikolaik/python-nodejs:python3.12-nodejs22')
    extra_deps: Optional[str] = field(default=None)
    docker_client: DockerClient = field(default_factory=DockerClient.from_env)
    _image: Optional[str] = None

    async def get_image(self) -> str:
        if self._image:
            return self._image

        source = BuildImageSource(
            base_image_name=self.base_image_name,
            extra_deps=self.extra_deps,
            docker_client=self.docker_client,
        )
        image_name = await source.build_image_name()
        image = get_local_image(image_name, self.docker_client)
        if not image:
            image = await self.build_image(image_name)
        self._image = image
        return image

    async def build_image(self, image_name: str) -> Image:
        intermediate_image = await self.get_intermediate_image()
        self.remove_old_images(BuildImageSource.sandbox_image_name_prefix)
        source = BuildImageSource(
            base_image_name=intermediate_image.tags[0],
            extra_deps=self.extra_deps,
            docker_file='dev_Dockerfile.j2',
            docker_client=self.docker_client,
        )
        image = await source.build_image(image_name)
        return image

    async def get_intermediate_image(self) -> Image:
        intermediate_image_name = self.get_intermediate_image_name()
        intermediate_image = get_local_image(
            intermediate_image_name, self.docker_client
        )
        if not intermediate_image:
            intermediate_image = await self.build_intermediate_image(
                intermediate_image_name
            )
        return intermediate_image

    async def build_intermediate_image(self, intermediate_image_name: str) -> Image:
        self.remove_old_images(INTERMEDIATE_NAME_PREFIX)
        openhands_logger.info(f'building_intermediate_image:{intermediate_image_name}')
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            code_path = Path(temp_path, 'code')
            code_path.mkdir()
            shutil.copy('pyproject.toml', Path(code_path, 'pyproject.toml'))
            Path(code_path, 'oh').mkdir()
            Path(code_path, 'oh', '__init__.py').touch()
            source = BuildImageSource(
                target_image_name=None,
                target_image_tag=None,
                docker_file='intermediate_Dockerfile.j2',
            )
            source.create_dockerfile(temp_path)
            source.execute_docker_build(temp_path, intermediate_image_name)
            image = self.docker_client.images.get(intermediate_image_name)
            return image

    def get_intermediate_image_name(self) -> Image:
        md5 = hashlib.md5()
        with open('pyproject.toml', mode='rb') as f:
            for data in f:
                md5.update(data)
        return INTERMEDIATE_NAME_PREFIX + md5.hexdigest()

    def remove_old_images(self, prefix: str):
        try:
            images = self.docker_client.images.list()
            for image in images:
                try:
                    if next(
                        (True for tag in image.tags if tag.startswith(prefix)),
                        False,
                    ):
                        openhands_logger.info(f'remove_old_image:{image.tags[0]}')
                        image.remove(force=True)
                except docker.errors.APIError:
                    pass
                except docker.errors.NotFound:
                    pass
        except docker.errors.NotFound:  # yes, this can happen!
            pass
