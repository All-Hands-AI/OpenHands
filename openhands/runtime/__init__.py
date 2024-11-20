from openhands.core.logger import openhands_logger as logger
from openhands.runtime.impl.e2b.sandbox import E2BBox
from openhands.runtime.impl.eventstream.eventstream_runtime import (
    EventStreamRuntime,
)
from openhands.runtime.impl.modal.modal_runtime import ModalRuntime
from openhands.runtime.impl.remote.remote_runtime import RemoteRuntime
from openhands.runtime.impl.runloop.runloop_runtime import RunloopRuntime


def get_runtime_cls(name: str):
    # Local imports to avoid circular imports
    if name == 'eventstream':
        return EventStreamRuntime
    elif name == 'e2b':
        return E2BBox
    elif name == 'remote':
        return RemoteRuntime
    elif name == 'modal':
        logger.debug('Using ModalRuntime')
        return ModalRuntime
    elif name == 'runloop':
        return RunloopRuntime
    else:
        raise ValueError(f'Runtime {name} not supported')


__all__ = [
    'E2BBox',
    'RemoteRuntime',
    'ModalRuntime',
    'RunloopRuntime',
    'EventStreamRuntime',
    'get_runtime_cls',
]
