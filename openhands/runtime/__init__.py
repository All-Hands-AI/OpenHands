from openhands.runtime.base import Runtime
from openhands.runtime.impl.cli.cli_runtime import CLIRuntime
from openhands.runtime.impl.docker.docker_runtime import (
    DockerRuntime,
)
from openhands.runtime.impl.local.local_runtime import LocalRuntime
from openhands.runtime.impl.remote.remote_runtime import RemoteRuntime
from openhands.utils.import_utils import get_impl

# mypy: disable-error-code="type-abstract"
_DEFAULT_RUNTIME_CLASSES: dict[str, type[Runtime]] = {
    'eventstream': DockerRuntime,
    'docker': DockerRuntime,
    'remote': RemoteRuntime,
    'local': LocalRuntime,
    'cli': CLIRuntime,
}


def get_runtime_cls(name: str) -> type[Runtime]:
    """
    If name is one of the predefined runtime names (e.g. 'docker'), return its class.
    Otherwise attempt to resolve name as subclass of Runtime and return it.
    Raise on invalid selections.
    """
    if name in _DEFAULT_RUNTIME_CLASSES:
        return _DEFAULT_RUNTIME_CLASSES[name]
    try:
        return get_impl(Runtime, name)
    except Exception as e:
        known_keys = _DEFAULT_RUNTIME_CLASSES.keys()
        raise ValueError(
            f'Runtime {name} not supported, known are: {known_keys}'
        ) from e


__all__ = [
    'Runtime',
    'RemoteRuntime',
    'DockerRuntime',
    'CLIRuntime',
    'get_runtime_cls',
]
