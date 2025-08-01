import os
from typing import Optional

import docker
from docker.models.containers import Container


def stop_all_containers(prefix: str) -> None:
    docker_client = docker.from_env()
    try:
        containers = docker_client.containers.list(all=True)
        for container in containers:
            try:
                if container.name.startswith(prefix):
                    container.stop()
            except docker.errors.APIError:
                pass
            except docker.errors.NotFound:
                pass
    except docker.errors.NotFound:  # yes, this can happen!
        pass
    finally:
        docker_client.close()


def get_warm_container(
    docker_client: docker.DockerClient, prefix: str
) -> Optional[Container]:
    """
    Get an available warm container if one exists.

    Args:
        docker_client: Docker client instance
        prefix: Container name prefix

    Returns:
        A warm container if available, None otherwise
    """
    try:
        containers = docker_client.containers.list(all=True)
        for container in containers:
            if container.name.startswith(f'{prefix}warm-'):
                return container
        return None
    except docker.errors.NotFound:
        return None
    except Exception:
        return None


def rename_container(container: Container, new_name: str) -> bool:
    """
    Rename a container.

    Args:
        container: Container to rename
        new_name: New name for the container

    Returns:
        True if successful, False otherwise
    """
    try:
        container.rename(new_name)
        return True
    except Exception:
        return False


def ensure_warm_containers(
    docker_client: docker.DockerClient,
    prefix: str,
    image: str,
    command: list[str],
    environment: dict,
    volumes: dict,
    network_mode: Optional[str] = None,
    device_requests: Optional[list] = None,
    docker_runtime_kwargs: Optional[dict] = None,
) -> None:
    """
    Ensure that the specified number of warm containers are available.

    Args:
        docker_client: Docker client instance
        prefix: Container name prefix
        image: Container image
        command: Command to run in the container
        environment: Environment variables
        volumes: Volume mounts
        network_mode: Network mode
        device_requests: Device requests for GPU
        docker_runtime_kwargs: Additional kwargs for docker.containers.run
    """
    num_warm_containers = int(os.environ.get('NUM_WARM_CONTAINERS', '0'))
    if num_warm_containers <= 0:
        return

    # Count existing warm containers
    existing_warm_containers = 0
    try:
        containers = docker_client.containers.list(all=True)
        for container in containers:
            if container.name.startswith(f'{prefix}warm-'):
                existing_warm_containers += 1
    except docker.errors.NotFound:
        pass

    # Create additional warm containers if needed
    for i in range(existing_warm_containers, num_warm_containers):
        warm_container_name = f'{prefix}warm-{i}'
        # Check if container already exists but is stopped
        try:
            container = docker_client.containers.get(warm_container_name)
            if container.status != 'running':
                container.start()
            continue
        except docker.errors.NotFound:
            # Container doesn't exist, create a new one
            pass
        except Exception:
            # If we fail to get the container, just continue to create a new one
            pass

        # Create a new warm container
        # Call with positional and keyword arguments to match the test
        docker_client.containers.run(
            image,
            command=command,
            entrypoint=[],
            network_mode=network_mode,
            ports=None,  # We'll set ports when we actually use the container
            working_dir='/openhands/code/',
            name=warm_container_name,
            detach=True,
            environment=environment,
            volumes=volumes,
            device_requests=device_requests,
            **(docker_runtime_kwargs or {}),
        )
