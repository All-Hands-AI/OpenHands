from typing import TYPE_CHECKING, Type

from .docker.local_box import LocalBox
from .docker.ssh_box import DockerSSHBox
from .e2b.sandbox import E2BBox
from .sandbox import Sandbox

if TYPE_CHECKING:
    from .runtime import Runtime


def get_runtime_cls(name: str) -> Type['Runtime']:
    # Local imports to avoid circular imports
    if name == 'server':
        from .server.runtime import ServerRuntime

        return ServerRuntime
    elif name == 'client':
        from .client.runtime import EventStreamRuntime

        return EventStreamRuntime
    elif name == 'e2b':
        from .e2b.runtime import E2BRuntime

        return E2BRuntime
    else:
        raise ValueError(f'Runtime {name} not supported')


__all__ = [
    'DockerSSHBox',
    'E2BBox',
    'LocalBox',
    'Sandbox',
    'get_runtime_cls',
]
