import importlib
from functools import lru_cache
from typing import TypeVar

T = TypeVar('T')


def import_from(qual_name: str):
    """Import the value from the qualified name given"""
    parts = qual_name.split('.')
    module_name = '.'.join(parts[:-1])
    module = importlib.import_module(module_name)
    result = getattr(module, parts[-1])
    return result


@lru_cache()
def get_impl(cls: type[T], impl_name: str | None) -> type[T]:
    """Import a named implementation of the specified class"""
    if impl_name is None:
        return cls
    impl_class = import_from(impl_name)
    assert cls == impl_class or issubclass(impl_class, cls)
    return impl_class
