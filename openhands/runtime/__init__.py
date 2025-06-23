from openhands.runtime.base import Runtime
from openhands.runtime.impl.cli.cli_runtime import CLIRuntime
from openhands.runtime.impl.docker.docker_runtime import (
    DockerRuntime,
)
from openhands.runtime.impl.kubernetes.kubernetes_runtime import KubernetesRuntime
from openhands.runtime.impl.local.local_runtime import LocalRuntime
from openhands.runtime.impl.remote.remote_runtime import RemoteRuntime
from openhands.utils.import_utils import get_impl

# mypy: disable-error-code="type-abstract"
_DEFAULT_RUNTIME_CLASSES: dict[str, type[Runtime]] = {
    'eventstream': DockerRuntime,
    'docker': DockerRuntime,
    'remote': RemoteRuntime,
    'local': LocalRuntime,
    'kubernetes': KubernetesRuntime,
    'cli': CLIRuntime,
}

# Try to import third-party runtimes if available
_THIRD_PARTY_RUNTIME_CLASSES: dict[str, type[Runtime]] = {}

try:
    from third_party.runtime.impl.daytona.daytona_runtime import DaytonaRuntime

    _THIRD_PARTY_RUNTIME_CLASSES['daytona'] = DaytonaRuntime
except ImportError:
    pass

try:
    from third_party.runtime.impl.e2b.e2b_runtime import E2BRuntime

    _THIRD_PARTY_RUNTIME_CLASSES['e2b'] = E2BRuntime
except ImportError:
    pass

try:
    from third_party.runtime.impl.modal.modal_runtime import ModalRuntime

    _THIRD_PARTY_RUNTIME_CLASSES['modal'] = ModalRuntime
except ImportError:
    pass

try:
    from third_party.runtime.impl.runloop.runloop_runtime import RunloopRuntime

    _THIRD_PARTY_RUNTIME_CLASSES['runloop'] = RunloopRuntime
except ImportError:
    pass

# Combine core and third-party runtimes
_ALL_RUNTIME_CLASSES = {**_DEFAULT_RUNTIME_CLASSES, **_THIRD_PARTY_RUNTIME_CLASSES}


def get_runtime_cls(name: str) -> type[Runtime]:
    """
    If name is one of the predefined runtime names (e.g. 'docker'), return its class.
    Otherwise attempt to resolve name as subclass of Runtime and return it.
    Raise on invalid selections.
    """
    if name in _ALL_RUNTIME_CLASSES:
        return _ALL_RUNTIME_CLASSES[name]
    try:
        return get_impl(Runtime, name)
    except Exception as e:
        known_keys = _ALL_RUNTIME_CLASSES.keys()
        raise ValueError(
            f'Runtime {name} not supported, known are: {known_keys}'
        ) from e


# Build __all__ list dynamically based on available runtimes
__all__ = [
    'Runtime',
    'RemoteRuntime',
    'DockerRuntime',
    'KubernetesRuntime',
    'CLIRuntime',
    'LocalRuntime',
    'get_runtime_cls',
]

# Add third-party runtimes to __all__ if they're available
if 'daytona' in _THIRD_PARTY_RUNTIME_CLASSES:
    __all__.append('DaytonaRuntime')
if 'e2b' in _THIRD_PARTY_RUNTIME_CLASSES:
    __all__.append('E2BRuntime')
if 'modal' in _THIRD_PARTY_RUNTIME_CLASSES:
    __all__.append('ModalRuntime')
if 'runloop' in _THIRD_PARTY_RUNTIME_CLASSES:
    __all__.append('RunloopRuntime')
