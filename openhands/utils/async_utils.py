import asyncio
from concurrent import futures
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Coroutine, Iterable, TypeVar

T = TypeVar('T')
R = TypeVar('R')

GENERAL_TIMEOUT: int = 15
EXECUTOR = ThreadPoolExecutor()


async def call_sync_from_async(fn: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    """
    Shorthand for running a function in the default background thread pool executor
    and awaiting the result. The nature of synchronous code is that the future
    returned by this function is not cancellable
    """
    loop = asyncio.get_event_loop()
    coro = loop.run_in_executor(None, lambda: fn(*args, **kwargs))
    result = await coro
    return result


def call_async_from_sync(
    corofn: Callable[..., Coroutine[Any, Any, R]],
    timeout: float = GENERAL_TIMEOUT,
    *args: Any,
    **kwargs: Any,
) -> R:
    """
    Shorthand for running a coroutine in the default background thread pool executor
    and awaiting the result
    """

    if corofn is None:
        raise ValueError('corofn is None')
    if not asyncio.iscoroutinefunction(corofn):
        raise ValueError('corofn is not a coroutine function')

    async def arun() -> R:
        coro = corofn(*args, **kwargs)
        result = await coro
        return result

    def run() -> R:
        loop_for_thread = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop_for_thread)
            return asyncio.run(arun())
        finally:
            loop_for_thread.close()

    if getattr(EXECUTOR, '_shutdown', False):
        result = run()
        return result

    future = EXECUTOR.submit(run)
    futures.wait([future], timeout=timeout or None)
    result = future.result()
    return result


async def call_coro_in_bg_thread(
    corofn: Callable[..., Coroutine[Any, Any, R]],
    timeout: float = GENERAL_TIMEOUT,
    *args: Any,
    **kwargs: Any,
) -> R:
    """Function for running a coroutine in a background thread."""
    return await call_sync_from_async(
        call_async_from_sync, corofn, timeout, *args, **kwargs
    )


async def wait_all(
    iterable: Iterable[Coroutine[Any, Any, T]], timeout: int = GENERAL_TIMEOUT
) -> list[T]:
    """
    Shorthand for waiting for all the coroutines in the iterable given in parallel. Creates
    a task for each coroutine.
    Returns a list of results in the original order. If any single task raised an exception, this is raised.
    If multiple tasks raised exceptions, an AsyncException is raised containing all exceptions.
    """
    tasks = [asyncio.create_task(c) for c in iterable]
    if not tasks:
        return []
    _, pending = await asyncio.wait(tasks, timeout=timeout)
    if pending:
        for task in pending:
            task.cancel()
        raise asyncio.TimeoutError()
    results: list[T] = []
    errors: list[Exception] = []
    for task in tasks:
        try:
            results.append(task.result())
        except Exception as e:
            errors.append(e)
    if errors:
        if len(errors) == 1:
            raise errors[0]
        raise AsyncException(errors)
    return [task.result() for task in tasks]


class AsyncException(Exception):
    def __init__(self, exceptions: list[Exception]) -> None:
        self.exceptions = exceptions

    def __str__(self) -> str:
        return '\n'.join(str(e) for e in self.exceptions)
