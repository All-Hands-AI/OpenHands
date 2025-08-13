from openhands.runtime.builder.base import RuntimeBuilder

try:
    from openhands.runtime.builder.docker import DockerRuntimeBuilder

    DOCKER_BUILDER_AVAILABLE = True
except ImportError:
    DOCKER_BUILDER_AVAILABLE = False

    # Create a stub class that raises an error when instantiated
    class DockerRuntimeBuilder:  # type: ignore
        def __init__(self, *args, **kwargs):
            raise ImportError(
                'Docker runtime builder is not available. Install docker to enable Docker runtime builder.'
            )


__all__ = ['RuntimeBuilder']

if DOCKER_BUILDER_AVAILABLE:
    __all__.append('DockerRuntimeBuilder')
