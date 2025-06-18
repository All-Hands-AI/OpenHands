"""
Runtime implementations for OpenHands.
"""

from openhands.runtime.impl.action_execution.action_execution_client import (
    ActionExecutionClient,
)
from openhands.runtime.impl.cli import CLIRuntime

try:
    from openhands.runtime.impl.daytona.daytona_runtime import DaytonaRuntime

    _DAYTONA_AVAILABLE = True
except ImportError:
    _DAYTONA_AVAILABLE = False
    DaytonaRuntime = None  # type: ignore
from openhands.runtime.impl.docker.docker_runtime import DockerRuntime
from openhands.runtime.impl.e2b.e2b_runtime import E2BRuntime
from openhands.runtime.impl.local.local_runtime import LocalRuntime
from openhands.runtime.impl.modal.modal_runtime import ModalRuntime
from openhands.runtime.impl.remote.remote_runtime import RemoteRuntime
from openhands.runtime.impl.runloop.runloop_runtime import RunloopRuntime

__all__ = [
    'ActionExecutionClient',
    'CLIRuntime',
    'DockerRuntime',
    'E2BRuntime',
    'LocalRuntime',
    'ModalRuntime',
    'RemoteRuntime',
    'RunloopRuntime',
]

if _DAYTONA_AVAILABLE:
    __all__.append('DaytonaRuntime')
