# thread_agent_runner.py
from __future__ import annotations
import threading
import ctypes
import time
from typing import Optional, Callable

from openhands.sdk import BaseConversation

class ThreadAgentRunner:
    """
    Run conversation.run() in a thread and *attempt* to terminate by injecting
    KeyboardInterrupt into that thread. WARNING: unsafe; prefer processes.
    """

    def __init__(self, conversation_factory: BaseConversation):
        # Use a factory so a fresh conversation can be made per run if needed
        self._conversation_factory = conversation_factory
        self._thread: Optional[threading.Thread] = None
        self._done = threading.Event()

    def run_agent(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._done.clear()

        def _target():
            conv = self._conversation_factory
            try:
                conv.run()  # synchronous, blocking
            except (KeyboardInterrupt, SystemExit):
                # Let termination be clean from our perspective
                pass
            finally:
                self._done.set()

        self._thread = threading.Thread(target=_target, daemon=True)
        self._thread.start()

    def wait_for_completion(self, timeout: float | None = None) -> None:
        self._done.wait(timeout=timeout)

    def is_running(self) -> bool:
        return bool(self._thread and self._thread.is_alive())

    def terminate_immediately(self) -> None:
        """
        Try to stop the running thread by injecting KeyboardInterrupt.
        DANGEROUS: may leave program in bad state. Use at your own risk.
        """
        if not self._thread or not self._thread.is_alive():
            return
        tid = self._thread_id(self._thread)
        if tid is None:
            return
        # Inject KeyboardInterrupt into the target thread
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
            ctypes.c_long(tid),
            ctypes.py_object(KeyboardInterrupt),
        )
        if res > 1:
            # Undo if it affected more than one thread
            ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(tid), None)

    @staticmethod
    def _thread_id(thr: threading.Thread) -> Optional[int]:
        # Thread.ident is the CPython thread id usable by PyThreadState_SetAsyncExc
        return thr.ident
