from pydantic import BaseModel

from openhands.runtime.e2b.sandbox import E2BBox


class RuntimeInfo(BaseModel):
    module: str
    class_name: str


# Core runtimes as default
_registered_runtimes: dict[str, RuntimeInfo] = {
    'eventstream': RuntimeInfo(module='client', class_name='EventStreamRuntime'),
    'e2b': RuntimeInfo(module='e2b', class_name='E2bRuntime'),
    'remote': RuntimeInfo(module='remote', class_name='RemoteRuntime'),
}


def register_runtime(name: str, module: str, class_name: str):
    """
    Registers a new runtime with the given name, module, and class name.

    This function allows you to add a new runtime to the system. It takes the name
    of the runtime, the module where the runtime class is defined, and the class name
    of the runtime. The runtime information is stored in the _registered_runtimes
    dictionary, which maps the runtime name to its corresponding RuntimeInfo object.

    Example:
    >>> register_runtime("new_runtime", "new_module", "NewRuntime")
    """
    _registered_runtimes[name] = RuntimeInfo(module=module, class_name=class_name)


def get_runtime_cls(name: str):
    """
    Returns the runtime class based on the given name using the registered runtime information.

    This function dynamically imports and returns the runtime class corresponding to the
    provided name. It uses the information stored in the _registered_runtimes dictionary
    to determine the module and class name for the requested runtime.

    The function performs the following steps:
    1. Retrieves the RuntimeInfo object for the given name from _registered_runtimes.
    2. Dynamically imports the module containing the runtime class.
    3. Retrieves the runtime class from the imported module using getattr.

    If the runtime is not found or cannot be imported, it raises a ValueError.

    Args:
        name (str): The name of the runtime to retrieve.

    Returns:
        type: The runtime class corresponding to the given name.

    Raises:
        ValueError: If the specified runtime is not supported or cannot be imported.

    Example:
        >>> runtime_cls = get_runtime_cls("eventstream")
        >>> runtime_instance = runtime_cls(config, event_stream)
    """
    import importlib

    try:
        runtime_info = _registered_runtimes[name]
        module = importlib.import_module(
            f'openhands.runtime.{runtime_info.module}.runtime'
        )
        return getattr(module, runtime_info.class_name)
    except (ImportError, AttributeError, KeyError):
        raise ValueError(f'Runtime {name} not supported')


__all__ = [
    'E2BBox',
    'get_runtime_cls',
    'register_runtime',
]
