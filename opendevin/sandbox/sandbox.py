import select
import sys
from abc import ABC, abstractmethod
from typing import Dict
from typing import Tuple


class BackgroundCommand:
    """
    Represents a background command execution
    """
    def __init__(self, id: int, command: str, result, pid: int):
        """
        Initialize a BackgroundCommand instance.

        Args:
            id (int): The identifier of the command.
            command (str): The command to be executed.
            result: The result of the command execution.
            pid (int): The process ID (PID) of the command.
        """
        self.id = id
        self.command = command
        self.result = result
        self.pid = pid

    def parse_docker_exec_output(self, logs: bytes) -> Tuple[bytes, bytes]:
        """
        Parses the output of a Docker exec command.

        Args:
            logs (bytes): The raw output logs of the command.

        Returns:
            Tuple[bytes, bytes]: A tuple containing the parsed output and any remaining data.
        """
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
        """
        Read and decode the logs of the command.

        Returns:
            str: The decoded logs of the command.
        """
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
