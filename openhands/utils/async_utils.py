import asyncio
from concurrent.futures import ThreadPoolExecutor, wait
from typing import Callable, Coroutine, Iterable

GENERAL_TIMEOUT: int = 15
EXECUTOR = ThreadPoolExecutor()


async def call_sync_from_async(fn: Callable, *args, **kwargs):
    """Shorthand for running a function in the default background thread pool executor
    and awaiting the result. The nature of synchronous code is that the future
    returned by this function is not cancellable
    """
    loop = asyncio.get_event_loop()
    coro = loop.run_in_executor(None, lambda: fn(*args, **kwargs))
    result = await coro
    return result


def call_async_from_sync(
    corofn: Callable, timeout: float = GENERAL_TIMEOUT, *args, **kwargs
):
    """Shorthand for running a coroutine in the default background thread pool executor
    and awaiting the result
    """
    """Run a coroutine in a thread-safe way, handling existing event loops."""
    if corofn is None:
        raise ValueError('corofn is None')
    if not asyncio.iscoroutinefunction(corofn):
        raise ValueError('corofn is not a coroutine function')

    async def arun():
        return await corofn(*args, **kwargs)

    def run_in_thread():
        """Run coroutine in a separate thread with its own event loop."""
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(arun())
        finally:
            loop.close()

    # If executor is shut down, just run in this thread
    if getattr(EXECUTOR, '_shutdown', False):
        return run_in_thread()

    try:
        # Check if there’s a running loop in this thread
        asyncio.get_running_loop()
        # Loop is running → run coroutine in executor thread
        future = EXECUTOR.submit(run_in_thread)
        wait([future], timeout=timeout or None)
        return future.result()
    except RuntimeError:
        # No loop running → safe to run in this thread
        return run_in_thread()


async def call_coro_in_bg_thread(
    corofn: Callable, timeout: float = GENERAL_TIMEOUT, *args, **kwargs
):
    """Function for running a coroutine in a background thread."""
    await call_sync_from_async(call_async_from_sync, corofn, timeout, *args, **kwargs)


async def wait_all(
    iterable: Iterable[Coroutine], timeout: int = GENERAL_TIMEOUT
) -> list:
    """Shorthand for waiting for all the coroutines in the iterable given in parallel. Creates
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
    results = []
    errors = []
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
    def __init__(self, exceptions):
        self.exceptions = exceptions

    def __str__(self):
        return '\n'.join(str(e) for e in self.exceptions)


async def run_in_loop(
    coro: Coroutine, loop: asyncio.AbstractEventLoop, timeout: float = GENERAL_TIMEOUT
):
    """Mitigate the dreaded "coroutine was created in a different event loop" error.
    Pass the coroutine to a different event loop if needed.
    """
    running_loop = asyncio.get_running_loop()
    if running_loop == loop:
        result = await coro
        return result

    result = await call_sync_from_async(_run_in_loop, coro, loop, timeout)
    return result


def _run_in_loop(coro: Coroutine, loop: asyncio.AbstractEventLoop, timeout: float):
    future = asyncio.run_coroutine_threadsafe(coro, loop)
    result = future.result(timeout=timeout)
    return result
