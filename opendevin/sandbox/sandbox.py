import select
import sys
from typing import Tuple
from abc import ABC, abstractmethod
from typing import Dict


class BackgroundCommand:
    def __init__(self, id: int, command: str, result, pid: int):
        self.id = id
        self.command = command
        self.result = result
        self.pid = pid

    def parse_docker_exec_output(self, logs: bytes) -> Tuple[bytes, bytes]:
        res = b''
        tail = b''
        i = 0
        byte_order = sys.byteorder
        while i < len(logs):
            prefix = logs[i: i + 8]
            if len(prefix) < 8:
                msg_type = prefix[0:1]
                if msg_type in [b'\x00', b'\x01', b'\x02', b'\x03']:
                    tail = prefix
                break

            msg_type = prefix[0:1]
            padding = prefix[1:4]
            if (
                msg_type in [b'\x00', b'\x01', b'\x02', b'\x03']
                and padding == b'\x00\x00\x00'
            ):
                msg_length = int.from_bytes(prefix[4:8], byteorder=byte_order)
                res += logs[i + 8: i + 8 + msg_length]
                i += 8 + msg_length
            else:
                res += logs[i: i + 1]
                i += 1
        return res, tail

    def read_logs(self) -> str:
        # TODO: get an exit code if process is exited
        logs = b''
        last_remains = b''
        while True:
            ready_to_read, _, _ = select.select(
                [self.result.output], [], [], 0.1)  # type: ignore[has-type]
            if ready_to_read:
                data = self.result.output.read(4096)  # type: ignore[has-type]
                if not data:
                    break
                chunk, last_remains = self.parse_docker_exec_output(
                    last_remains + data)
                logs += chunk
            else:
                break
        return (logs + last_remains).decode('utf-8', errors='replace')


class Sandbox(ABC):
    background_commands: Dict[int, BackgroundCommand] = {}

    @abstractmethod
    def execute(self, cmd: str) -> Tuple[int, str]:
        pass

    @abstractmethod
    def execute_in_background(self, cmd: str):
        pass

    @abstractmethod
    def kill_background(self, id: int):
        pass

    @abstractmethod
    def read_logs(self, id: int) -> str:
        pass

    @abstractmethod
    def close(self):
        pass
