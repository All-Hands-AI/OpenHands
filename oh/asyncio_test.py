import asyncio
from typing import Awaitable, TypeVar

T = TypeVar("T")


async def async_countdown(number: int, delay: int):
    print(f"TRACE:{number}")
    if number > 0:
        await delayed(async_countdown(number - 1, delay), delay)


async def delayed(coro: Awaitable[T], delay: int) -> T:
    await asyncio.sleep(delay)
    result = await coro
    return result


async def main():
    # This runs and waits
    # await asyncio.wait(
    #    [asyncio.create_task(async_countdown(10, 1)) for _ in range(5)]
    # )

    # This runs but does not wait
    foo = [asyncio.create_task(async_countdown(10, 1)) for _ in range(5)]
    await asyncio.sleep(12)


if __name__ == "__main__":
    asyncio.run(main())


# loop = asyncio.get_event_loop()
# loop.run_until_complete(asyncio.gather(
#    immediate_coroutine(),
#    wrapper(2.0, wrapped_coroutine)
# ))
