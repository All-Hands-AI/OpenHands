import functools
import logging
import threading
from typing import Dict

from openhands.core.logger import LlmLogType, current_log_level, setup_llm_logger


class SessionContext:
    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self._context = threading.local()
        self.set_sid('default')  # Set default SID

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def set_sid(self, sid: str):
        self._context.sid = sid
        self._context.loggers = {
            LlmLogType.PROMPT: setup_llm_logger(
                LlmLogType.PROMPT, sid, current_log_level
            ),
            LlmLogType.RESPONSE: setup_llm_logger(
                LlmLogType.RESPONSE, sid, current_log_level
            ),
        }

    def get_sid(self) -> str:
        return self._context.sid

    def get_loggers(self) -> Dict[LlmLogType, logging.Logger]:
        return self._context.loggers

    def clear(self):
        self.set_sid('default')  # Reset to default SID


session_context = SessionContext.get_instance()


class SessionContextManager:
    def __init__(self, sid: str):
        self.sid = sid

    def __enter__(self):
        session_context.set_sid(self.sid)
        return session_context

    def __exit__(self, exc_type, exc_val, exc_tb):
        session_context.clear()  # This will set the SID back to 'default'


def get_current_sid() -> str:
    return session_context.get_sid()


def get_current_llm_loggers() -> Dict[LlmLogType, logging.Logger]:
    return session_context.get_loggers()


def with_session_context(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        sid = kwargs.pop('sid', get_current_sid())
        with SessionContextManager(sid):
            return func(*args, **kwargs)

    return wrapper
