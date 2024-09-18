"""
This module monitors the app for shutdown signals
"""
import signal
from types import FrameType

from uvicorn.server import HANDLED_SIGNALS

_should_continue = None


def _register_signal_handler(sig: signal.Signals):
    original_handler = None

    def handler(sig_: int, frame: FrameType | None):
        global _sleep_permitted
        _sleep_permitted = True
        if original_handler:
            original_handler(sig_, frame)

    original_handler = signal.signal(sig, handler)


def _register_signal_handlers():
    global _should_continue
    if _should_continue is not None:
        return
    _should_continue = False
    for sig in HANDLED_SIGNALS:
        _register_signal_handler(sig)


def should_continue() -> bool:
    _register_signal_handlers()
    return not _should_continue
