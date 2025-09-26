# process_agent_runner.py
from __future__ import annotations

import multiprocessing as mp
import os
import signal
import sys
from typing import Callable, Optional


class ProcessAgentRunner:
    """
    Run conversation.run() in a *separate process* so we can terminate immediately
    (even mid-step) without unsafe thread hacks.

    Usage:
        runner = ProcessAgentRunner(conversation_factory)
        runner.run_agent()
        runner.wait_for_completion()
        # on double Ctrl-C:
        runner.terminate_immediately()
    """

    def __init__(
        self,
        conversation_factory: Callable[[], object],   # must be picklable
        start_method: Optional[str] = None,           # default "spawn" cross-platform
        kill_grace_seconds: float = 1.5,              # SIGTERM grace before SIGKILL (POSIX)
    ):
        self._ctx = mp.get_context(start_method or "spawn")
        self._factory = conversation_factory
        self._proc: Optional[mp.Process] = None
        self._done = self._ctx.Event()
        self._kill_grace_seconds = kill_grace_seconds

    def run_agent(self) -> None:
        if self._proc and self._proc.is_alive():
            return
        self._done.clear()
        self._proc = self._ctx.Process(
            target=_child_entry,
            args=(self._factory, self._done),
            daemon=True,
        )
        self._proc.start()

    def wait_for_completion(self, timeout: float | None = None) -> None:
        if not self._proc:
            return
        self._proc.join(timeout)

    def is_running(self) -> bool:
        return bool(self._proc and self._proc.is_alive())

    def terminate_immediately(self) -> None:
        """Kill the agent process right now (and its children on POSIX)."""
        if not self._proc or not self._proc.is_alive():
            return

        pid = self._proc.pid
        if pid is None:
            return

        try:
            if os.name == "posix":
                # Kill whole process group (child calls setsid()).
                pgid = os.getpgid(pid)
                os.killpg(pgid, signal.SIGTERM)
                self._proc.join(self._kill_grace_seconds)
                if self._proc.is_alive():
                    os.killpg(pgid, signal.SIGKILL)
            else:
                # Windows: terminate the process (children may persist unless using Job Objects).
                self._proc.terminate()
        except Exception:
            # Last resort
            try:
                self._proc.kill()
            except Exception:
                pass

    def close(self) -> None:
        if self._proc and self._proc.is_alive():
            self.terminate_immediately()
        self._proc = None


def _child_entry(conversation_factory: Callable[[], object], done_event: mp.Event) -> None:
    """Child process: build conversation and run synchronously."""
    # New process group so parent can kill the entire tree on POSIX.
    if os.name == "posix":
        os.setsid()

    try:
        conv = conversation_factory()
        conv.run()  # blocking, synchronous; safe to kill via signals
    except KeyboardInterrupt:
        pass
    except Exception:
        # Log to child stderr so you can see failures
        import traceback
        traceback.print_exc()
    finally:
        done_event.set()
        try:
            sys.stdout.flush()
            sys.stderr.flush()
        except Exception:
            pass
