from dataclasses import dataclass, field

from docker import DockerClient

from openhands.runtime.image_source.image_source_abc import ImageSourceABC
from openhands.utils.docker_utils import get_local_image, pull_image


@dataclass
class SpecificImageSource(ImageSourceABC):
    """
    Use case where we have a specific docker image we want to use (ie: Production) and we do not
    want to build one.
    """

    image: str
    docker_client: DockerClient = field(default_factory=DockerClient.from_env)

    async def get_image(self) -> str:
        docker_client = self.docker_client
        image = get_local_image(self.image, docker_client)
        if not image:
            pull_image(self.image, docker_client)
            image = get_local_image(self.image, docker_client)
        return image.tags[0]  # type: ignore
