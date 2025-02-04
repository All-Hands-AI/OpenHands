"""Process information utilities."""

import os
import socket
from dataclasses import dataclass


@dataclass
class ProcessInfo:
    """Process information."""

    pid: int
    username: str
    hostname: str
    working_dir: str
    py_interpreter_path: str


def get_process_info() -> ProcessInfo:
    """Get information about the current process.

    Returns:
        ProcessInfo: Information about the current process.
    """
    return ProcessInfo(
        pid=os.getpid(),
        username=os.getenv('USER', 'root'),
        hostname=socket.gethostname(),
        working_dir=os.getcwd(),
        py_interpreter_path=os.path.abspath(os.sys.executable),
    )
