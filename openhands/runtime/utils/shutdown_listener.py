"""
This module monitors the app for shutdown signals
"""

import asyncio
import signal
import threading
import time
from functools import wraps
from types import FrameType
from typing import Any, Callable, TypeVar

from uvicorn.server import HANDLED_SIGNALS

T = TypeVar('T')

def signal_operation(operation_name: str) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator for signal operations that handles common error patterns"""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except ValueError as e:
                # Handle signal-related errors
                raise RuntimeError(f'Signal error during {operation_name}: {e}')
            except Exception as e:
                raise RuntimeError(f'Error during {operation_name}: {e}')
        return wrapper
    return decorator


_should_exit = None


@signal_operation("register_handler")
def _register_signal_handler(sig: signal.Signals) -> None:
    original_handler = None

    def handler(sig_: int, frame: FrameType | None) -> None:
        global _should_exit
        _should_exit = True
        if original_handler:
            original_handler(sig_, frame)

    original_handler = signal.signal(sig, handler)


@signal_operation("register_handlers")
def _register_signal_handlers() -> None:
    global _should_exit
    if _should_exit is not None:
        return
    _should_exit = False

    if threading.current_thread() is threading.main_thread():
        for sig in HANDLED_SIGNALS:
            _register_signal_handler(sig)


@signal_operation("check_exit")
def should_exit() -> bool:
    _register_signal_handlers()
    return bool(_should_exit)


@signal_operation("check_continue")
def should_continue() -> bool:
    _register_signal_handlers()
    return not _should_exit


@signal_operation("sync_sleep")
def sleep_if_should_continue(timeout: float) -> None:
    if timeout <= 1:
        time.sleep(timeout)
        return
    start_time = time.time()
    while (time.time() - start_time) < timeout and should_continue():
        time.sleep(1)


@signal_operation("async_sleep")
async def async_sleep_if_should_continue(timeout: float) -> None:
    if timeout <= 1:
        await asyncio.sleep(timeout)
        return
    start_time = time.time()
    while time.time() - start_time < timeout and should_continue():
        await asyncio.sleep(1)

