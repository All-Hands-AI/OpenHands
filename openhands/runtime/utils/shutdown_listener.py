"""
This module monitors the app for shutdown signals
"""
import asyncio
import signal
import time
from types import FrameType

from uvicorn.server import HANDLED_SIGNALS

_should_continue = None


def _register_signal_handler(sig: signal.Signals):
    original_handler = None

    def handler(sig_: int, frame: FrameType | None):
        global _should_continue
        _should_continue = False
        if original_handler:
            original_handler(sig_, frame)

    original_handler = signal.signal(sig, handler)


def _register_signal_handlers():
    global _should_continue
    if _should_continue is not None:
        return
    _should_continue = True
    for sig in HANDLED_SIGNALS:
        _register_signal_handler(sig)


def should_continue() -> bool:
    _register_signal_handlers()
    return bool(_should_continue)


def sleep_if_should_continue(timeout: float):
    if(timeout <= 1):
        time.sleep(timeout)
        return
    start_time = time.time()
    while (time.time() - start_time) < timeout and should_continue():
        time.sleep(1)


async def asleep_if_should_continue(timeout: float):
    if(timeout <= 1):
        await asyncio.sleep(timeout)
        return
    start_time = time.time()
    while time.time() - start_time < timeout and should_continue():
        await asyncio.sleep(1)
