from typing import Type

from openhands.core.config.app_config import AppConfig
from openhands.runtime.base import Runtime
from openhands.runtime.impl.daytona.daytona_runtime import DaytonaRuntime
from openhands.runtime.impl.docker.docker_runtime import (
    DockerRuntime,
)
from openhands.runtime.impl.e2b.e2b_runtime import E2BRuntime
from openhands.runtime.impl.local.local_runtime import LocalRuntime
from openhands.runtime.impl.modal.modal_runtime import ModalRuntime
from openhands.runtime.impl.remote.remote_runtime import RemoteRuntime
from openhands.runtime.impl.runloop.runloop_runtime import RunloopRuntime
from openhands.utils.import_utils import get_impl

# mypy: disable-error-code="type-abstract"
_DEFAULT_RUNTIME_CLASSES: dict[str, Type[Runtime]] = {
    'eventstream': DockerRuntime,
    'docker': DockerRuntime,
    'e2b': E2BRuntime,
    'remote': RemoteRuntime,
    'modal': ModalRuntime,
    'runloop': RunloopRuntime,
    'local': LocalRuntime,
    'daytona': DaytonaRuntime,
}


def get_runtime_cls(config: AppConfig) -> Type[Runtime]:
    """
    If custom_class_name is supplied, resolve that class.
    Otherwise use name to select one of the supplied runtime implementations.
    Raise on invalid selections.
    """
    name = config.runtime
    if name in config.runtime_custom_classses:
        # mypy: disable-error-code="type-abstract"
        return get_impl(Runtime, config.runtime_custom_classses[name])
    if name in _DEFAULT_RUNTIME_CLASSES:
        return _DEFAULT_RUNTIME_CLASSES[name]
    raise ValueError(f'Runtime {name} not supported')


__all__ = [
    'Runtime',
    'E2BBox',
    'RemoteRuntime',
    'ModalRuntime',
    'RunloopRuntime',
    'DockerRuntime',
    'get_runtime_cls',
]
