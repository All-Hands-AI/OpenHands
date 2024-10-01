import asyncio
from functools import partial, wraps
from typing import Any, Callable, Coroutine, ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")


def sync_to_async(func: Callable[P, R]) -> Callable[P, Coroutine[Any, Any, R]]:
    """
    Convert a function into a coroutine that will run on the default ThreadPoolExecutor
    """

    @wraps(func)
    async def run_in_executor(*args: P.args, **kwargs: P.kwargs) -> R:
        loop = asyncio.get_event_loop()
        pfunc = partial(func, *args, **kwargs)
        return await loop.run_in_executor(None, pfunc)

    return run_in_executor
