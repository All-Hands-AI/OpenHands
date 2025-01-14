import builtins
import logging
import os
import socket
import time
import traceback
from dataclasses import dataclass, field
from threading import Thread
from typing import Any

from openhands.utils.shutdown_listener import should_continue


@dataclass(frozen=True)
class FD:
    subject: Any
    stack: list[str]
    created_at: float = field(default_factory=time.time)


FDS: dict[int, FD] = {}
UNCLOSED_TIMEOUT = 180
INTERVAL = 15


def get_self(args, kwargs):
    if len(args) >= 1:
        return args[0]
    else:
        return kwargs['self']


original_open = builtins.open
original_init = socket.socket.__init__
original_close = socket.socket.close
original_detach = socket.socket.detach
logger = logging.getLogger(__name__)


def print_error(msg: str, traceback: list[str]):
    output = [f'\n===== {msg} =====\n']
    output.extend(traceback[:-1])
    logger.error(''.join(output))


def patched_open(*args, **kwargs):
    file_obj = original_open(*args, **kwargs)
    id_ = id(file_obj)
    original_close = file_obj.close

    def patched_close(*args, **kwargs):
        FDS.pop(id_, None)
        result = original_close(*args, **kwargs)
        return result

    file_obj.close = patched_close
    FDS[id_] = FD(file_obj, traceback.format_stack())
    return file_obj


def patched_init(*args, **kwargs):
    result = original_init(*args, **kwargs)
    self = get_self(args, kwargs)
    id_ = id(self)
    FDS[id_] = FD(self, traceback.format_stack())
    return result


def patched_close(*args, **kwargs):
    self = get_self(args, kwargs)
    id_ = id(self)
    FDS.pop(id_, None)
    result = original_close(*args, **kwargs)
    return result


def patched_detach(*args, **kwargs):
    self = get_self(args, kwargs)
    id_ = id(self)
    FDS.pop(id_, None)
    result = original_detach(*args, **kwargs)
    return result


def run():
    while should_continue():
        time.sleep(INTERVAL)
        threshold = time.time() - UNCLOSED_TIMEOUT
        for id_, fd in list(FDS.items()):
            if fd.created_at < threshold:
                FDS.pop(id_)
                print_error('UNCLOSED', fd.stack)
    for fd in FDS.values():
        print_error('UNCLOSED', fd.stack)


if os.environ.get('DEBUG') == '1':
    builtins.open = patched_open
    socket.socket.__init__ = patched_init  # type: ignore
    socket.socket.close = patched_close  # type: ignore
    socket.socket.detach = patched_detach  # type: ignore
    Thread(target=run, daemon=True).start()
