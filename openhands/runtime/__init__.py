from openhands.core.logger import openhands_logger as logger
from openhands.runtime.impl.e2b.sandbox import E2BBox


def get_runtime_cls(name: str):
    # Local imports to avoid circular imports
    if name == 'eventstream':
        from openhands.runtime.impl.eventstream.eventstream_runtime import (
            EventStreamRuntime,
        )

        return EventStreamRuntime
    elif name == 'e2b':
        from openhands.runtime.impl.e2b.e2b_runtime import E2BRuntime

        return E2BRuntime
    elif name == 'remote':
        from openhands.runtime.impl.remote.remote_runtime import RemoteRuntime

        return RemoteRuntime
    elif name == 'modal':
        logger.debug('Using ModalRuntime')
        from openhands.runtime.impl.modal.modal_runtime import ModalRuntime

        return ModalRuntime
    elif name == 'runloop':
        from openhands.runtime.impl.runloop.runloop_runtime import RunloopRuntime

        return RunloopRuntime
    else:
        raise ValueError(f'Runtime {name} not supported')


__all__ = [
    'E2BBox',
    'get_runtime_cls',
]
