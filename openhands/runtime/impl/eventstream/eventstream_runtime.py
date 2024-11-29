from openhands.runtime.impl.docker.docker_runtime import DockerRuntime


class EventStreamRuntime(DockerRuntime):
    """Default runtime that uses Docker containers for sandboxed execution."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
