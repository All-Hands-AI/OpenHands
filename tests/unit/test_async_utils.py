import asyncio

import pytest

from openhands.utils.async_utils import (
    AsyncException,
    call_async_from_sync,
    call_sync_from_async,
    wait_all,
)


@pytest.mark.asyncio
async def test_await_all():
    # Mock function demonstrating some calculation - always takes a minimum of 0.1 seconds
    async def dummy(value: int):
        await asyncio.sleep(0.1)
        return value * 2

    # wait for 10 calculations - serially this would take 1 second
    coro = wait_all(dummy(i) for i in range(10))

    # give the task only 0.3 seconds to complete (This verifies they occur in parallel)
    task = asyncio.create_task(coro)
    await asyncio.wait([task], timeout=0.3)

    # validate the results (We need to sort because they can return in any order)
    results = list(await task)
    expected = [i * 2 for i in range(10)]
    assert expected == results


@pytest.mark.asyncio
async def test_await_all_single_exception():
    # Mock function demonstrating some calculation - always takes a minimum of 0.1 seconds
    async def dummy(value: int):
        await asyncio.sleep(0.1)
        if value == 1:
            raise ValueError('Invalid value 1')  # Throw an exception on every odd value
        return value * 2

    # expect an exception to be raised.
    with pytest.raises(ValueError, match='Invalid value 1'):
        await wait_all(dummy(i) for i in range(10))


@pytest.mark.asyncio
async def test_await_all_multi_exception():
    # Mock function demonstrating some calculation - always takes a minimum of 0.1 seconds
    async def dummy(value: int):
        await asyncio.sleep(0.1)
        if value & 1:
            raise ValueError(
                f'Invalid value {value}'
            )  # Throw an exception on every odd value
        return value * 2

    # expect an exception to be raised.
    with pytest.raises(AsyncException):
        await wait_all(dummy(i) for i in range(10))


@pytest.mark.asyncio
async def test_await_all_timeout():
    result = 0

    # Mock function updates a nonlocal variable after a delay
    async def dummy(value: int):
        nonlocal result
        await asyncio.sleep(0.2)
        result += value

    # expect an exception to be raised.
    with pytest.raises(asyncio.TimeoutError):
        await wait_all((dummy(i) for i in range(10)), 0.1)

    # Wait and then check the shared result - this makes sure that pending tasks were cancelled.
    asyncio.sleep(0.2)
    assert result == 0


@pytest.mark.asyncio
async def test_call_sync_from_async():
    def dummy(value: int = 2):
        return value * 2

    result = await call_sync_from_async(dummy)
    assert result == 4
    result = await call_sync_from_async(dummy, 3)
    assert result == 6
    result = await call_sync_from_async(dummy, value=5)
    assert result == 10


@pytest.mark.asyncio
async def test_call_sync_from_async_error():
    def dummy():
        raise ValueError()

    with pytest.raises(ValueError):
        await call_sync_from_async(dummy)


def test_call_async_from_sync():
    async def dummy(value: int):
        return value * 2

    result = call_async_from_sync(dummy, 0, 3)
    assert result == 6


def test_call_async_from_sync_error():
    async def dummy(value: int):
        raise ValueError()

    with pytest.raises(ValueError):
        call_async_from_sync(dummy, 0, 3)


def test_call_async_from_sync_background_tasks():
    events = []

    async def bg_task():
        # This background task should finish after the dummy task
        events.append('bg_started')
        asyncio.sleep(0.2)
        events.append('bg_finished')

    async def dummy(value: int):
        events.append('dummy_started')
        # This coroutine kicks off a background task
        asyncio.create_task(bg_task())
        events.append('dummy_started')

    call_async_from_sync(dummy, 0, 3)

    # We check that the function did not return until all coroutines completed
    # (Even though some of these were started as background tasks)
    expected = ['dummy_started', 'dummy_started', 'bg_started', 'bg_finished']
    assert expected == events
