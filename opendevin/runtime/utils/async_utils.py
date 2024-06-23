import asyncio
from functools import wraps
from typing import Any, Callable, TypeVar

T = TypeVar('T')

def async_to_sync(func):
    # type: (Callable[..., Any]) -> Callable[..., Any]
    """
    A decorator that allows an asynchronous function to be called in a synchronous context.

    This decorator wraps an asynchronous function and ensures that it can be executed
    synchronously by running the event loop until the coroutine completes. If the current
    event loop is closed or does not exist, a new event loop is created.

    Args:
        func: The function to be wrapped.

    Returns:
        A synchronous callable that executes the function.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # type: (*Any, **Any) -> Any
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        try:
            result = func(*args, **kwargs)
            if asyncio.iscoroutine(result):
                return loop.run_until_complete(result)
            return result
        finally:
            if loop != asyncio.get_event_loop():
                loop.close()

    return wrapper
