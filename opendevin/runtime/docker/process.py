import select
import sys

from opendevin.runtime.process import Process


class DockerProcess(Process):
    """
    Represents a background command execution
    """

    def __init__(self, id: int, command: str, result, pid: int):
        """
        Initialize a DockerProcess instance.

        Args:
            id (int): The identifier of the command.
            command (str): The command to be executed.
            result: The result of the command execution.
            pid (int): The process ID (PID) of the command.
        """
        self.id = id
        self._command = command
        self.result = result
        self._pid = pid

    @property
    def pid(self) -> int:
        return self._pid

    @property
    def command(self) -> str:
        return self._command

    def parse_docker_exec_output(self, logs: bytes) -> tuple[bytes, bytes]:
        """
            When you execute a command using `exec` in a docker container, the output produced will be in bytes. this function parses the output of a Docker exec command.

        Example:
            Considering you have a docker container named `my_container` up and running
            $ docker exec my_container echo "Hello OpenDevin!"
            >> b'\x00\x00\x00\x00\x00\x00\x00\x13Hello OpenDevin!'

            Such binary logs will be processed by this function.

            The function handles message types, padding, and byte order to create a usable result. The primary goal is to convert raw container logs into a more structured format for further analysis or display.

            The function also returns a tail of bytes to ensure that no information is lost. It is a way to handle edge cases and maintain data integrity.

            >> output_bytes = b'\x00\x00\x00\x00\x00\x00\x00\x13Hello OpenDevin!'
            >> parsed_output, remaining_bytes = parse_docker_exec_output(output_bytes)

            >> print(parsed_output)
            b'Hello OpenDevin!'

            >> print(remaining_bytes)
            b''

        Args:
            logs (bytes): The raw output logs of the command.

        Returns:
            tuple[bytes, bytes]: A tuple containing the parsed output and any remaining data.
        """
        res = b''
        tail = b''
        i = 0
        byte_order = sys.byteorder
        while i < len(logs):
            prefix = logs[i : i + 8]
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
                res += logs[i + 8 : i + 8 + msg_length]
                i += 8 + msg_length
            else:
                res += logs[i : i + 1]
                i += 1
        return res, tail

    def read_logs(self) -> str:
        """
        Read and decode the logs of the command.

        This function continuously reads the standard output of a subprocess and
        processes the output using the parse_docker_exec_output function to handle
        binary log messages. It concatenates and decodes the output bytes into a
        string, ensuring that no partial messages are lost during reading.

        Dummy Example:

        >> cmd = 'echo "Hello OpenDevin!"'
        >> result = subprocess.Popen(
            cmd, shell=True, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True, cwd='.'
            )
        >> bg_cmd = DockerProcess(id, cmd = cmd, result = result, pid)

        >> logs = bg_cmd.read_logs()
        >> print(logs)
        Hello OpenDevin!

        Returns:
            str: The decoded logs(string) of the command.
        """
        # TODO: get an exit code if process is exited
        logs = b''
        last_remains = b''
        while True:
            ready_to_read, _, _ = select.select([self.result.output], [], [], 0.1)  # type: ignore[has-type]
            if ready_to_read:
                data = self.result.output.read(4096)  # type: ignore[has-type]
                if not data:
                    break
                chunk, last_remains = self.parse_docker_exec_output(last_remains + data)
                logs += chunk
            else:
                break
        return (logs + last_remains).decode('utf-8', errors='replace')
