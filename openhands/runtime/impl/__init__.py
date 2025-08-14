"""Runtime implementations for OpenHands."""

from openhands.runtime.impl.action_execution.action_execution_client import (
    ActionExecutionClient,
)
from openhands.runtime.impl.cli import CLIRuntime
from openhands.runtime.impl.local.local_runtime import LocalRuntime
from openhands.runtime.impl.remote.remote_runtime import RemoteRuntime

try:
    from openhands.runtime.impl.docker.docker_runtime import DockerRuntime

    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False

    # Create a stub class that raises an error when instantiated
    class DockerRuntime:  # type: ignore
        def __init__(self, *args, **kwargs):
            raise ImportError(
                'Docker runtime is not available. Install docker to enable Docker runtime.'
            )


__all__ = [
    'ActionExecutionClient',
    'CLIRuntime',
    'LocalRuntime',
    'RemoteRuntime',
]

if DOCKER_AVAILABLE:
    __all__.append('DockerRuntime')
