

"""
This module monitors the app for shutdown signals
"""
import asyncio
import signal
import time
from types import FrameType

from uvicorn.server import HANDLED_SIGNALS

_is_shutting_down = None


def _register_signal_handler(sig: signal.Signals):
    original_handler = None

    def handler(sig_: int, frame: FrameType | None):
        global _is_shutting_down
        _is_shutting_down = False
        if original_handler:
            original_handler(sig_, frame)

    original_handler = signal.signal(sig, handler)


def _register_signal_handlers():
    global _is_shutting_down
    if _is_shutting_down is not None:
        return
    _is_shutting_down = True
    for sig in HANDLED_SIGNALS:
        _register_signal_handler(sig)


def is_shutting_down() -> bool:
    _register_signal_handlers()
    return _is_shutting_down


def sleep_unless_shutdown(timeout: float):
    if(timeout <= 1):
        time.sleep(timeout)
        return
    start_time = time.time()
    while (time.time() - start_time) < timeout and not is_shutting_down():
        time.sleep(1)


async def asleep_unless_shutdown(timeout: float):
    if(timeout <= 1):
        await asyncio.sleep(timeout)
        return
    start_time = time.time()
    while time.time() - start_time < timeout and not is_shutting_down():
        await asyncio.sleep(1)
