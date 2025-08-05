import docker


def stop_all_containers(prefix: str) -> None:
    """Stop all containers with the given prefix.

    This function is already called within a Docker lifecycle lock context
    from DockerRuntime.close(), so we don't need to acquire the lock again here.
    """
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
