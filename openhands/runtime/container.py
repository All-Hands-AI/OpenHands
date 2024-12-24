"""Container-related types and utilities."""

import docker


class ContainerInfo:
    """Information about a running container that a Runtime needs."""

    def __init__(
        self,
        container_id: str,
        api_url: str,
        host_port: int,
        container_port: int,
        container: docker.models.containers.Container,
    ):
        self.container_id = container_id
        self.api_url = api_url
        self.host_port = host_port
        self.container_port = container_port
        self.container = container
