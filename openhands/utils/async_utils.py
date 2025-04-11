import asyncio
from concurrent import futures
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Coroutine, Iterable, List

GENERAL_TIMEOUT: int = 15
EXECUTOR = ThreadPoolExecutor()


async def call_sync_from_async(fn: Callable, *args, **kwargs):
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
    corofn: Callable, timeout: float = GENERAL_TIMEOUT, *args, **kwargs
):
    """
    Shorthand for running a coroutine in the default background thread pool executor
    and awaiting the result
    """

    if corofn is None:
        raise ValueError('corofn is None')
    if not asyncio.iscoroutinefunction(corofn):
        raise ValueError('corofn is not a coroutine function')

    async def arun():
        coro = corofn(*args, **kwargs)
        result = await coro
        return result

    def run():
        loop_for_thread = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop_for_thread)
            return asyncio.run(arun())
        finally:
            loop_for_thread.close()

    future = EXECUTOR.submit(run)
    futures.wait([future], timeout=timeout or None)
    result = future.result()
    return result


async def call_coro_in_bg_thread(
    corofn: Callable, timeout: float = GENERAL_TIMEOUT, *args, **kwargs
):
    """Function for running a coroutine in a background thread."""
    await call_sync_from_async(call_async_from_sync, corofn, timeout, *args, **kwargs)


async def wait_all(
    iterable: Iterable[Coroutine], timeout: int = GENERAL_TIMEOUT
) -> List:
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


async def async_subprocess_run(*args, **kwargs):
    """Run a subprocess command asynchronously."""

    def _run_subprocess():
        import subprocess

        return subprocess.run(*args, **kwargs)

    return await call_sync_from_async(_run_subprocess)


async def async_subprocess_check_output(*args, **kwargs):
    """Run a subprocess command and get output asynchronously."""

    def _check_output():
        import subprocess

        return subprocess.check_output(*args, **kwargs)

    return await call_sync_from_async(_check_output)


async def async_subprocess_popen(*args, **kwargs):
    """Create a subprocess asynchronously."""

    def _popen():
        import subprocess

        return subprocess.Popen(*args, **kwargs)

    return await call_sync_from_async(_popen)


async def async_open_file(path, mode='r', **kwargs):
    """Open a file asynchronously and return its content."""

    def _open_file():
        with open(path, mode, **kwargs) as f:
            if 'r' in mode:
                return f.read()
            return None

    return await call_sync_from_async(_open_file)


async def async_read_file_lines(path, **kwargs):
    """Read file lines asynchronously."""

    def _read_lines():
        with open(path, 'r', **kwargs) as f:
            return f.readlines()

    return await call_sync_from_async(_read_lines)


async def async_write_file(path, content, mode='w', **kwargs):
    """Write to a file asynchronously."""

    def _write_file():
        with open(path, mode, **kwargs) as f:
            f.write(content)

    return await call_sync_from_async(_write_file)


async def async_sleep(seconds):
    """Sleep asynchronously."""

    def _sleep():
        import time

        time.sleep(seconds)

    return await call_sync_from_async(_sleep)
