import os
import pty
import subprocess
import select
import socket

def get_user_host():
    user = os.getenv('USER')
    host = socket.gethostname()
    return f'{user}@{host}'

class BashTerminalEmulator:
    def __init__(self):
        self.master_fd, self.slave_fd = pty.openpty()
        self.process = subprocess.Popen(
            args='/bin/bash',
            stdin=self.slave_fd,
            stdout=self.slave_fd,
            stderr=self.slave_fd,
            close_fds=True
        )
        self._history = []
        os.close(self.slave_fd)
        # clear the initial output
        # TODO not too sure why there's `b'bash: no job control in this shell\r\n'` during init
        self._read_output()

    @property
    def history(self):
        return '\n'.join(self._history)

    def run_command(self, command):
        os.write(self.master_fd, (command + '\n').encode())
        self._history.append(self.userhost + command)
        ret = self._read_output()
        self._history.append(ret)
        return ret

    def _read_output(self):
        output = b""
        while True:
            r, _, _ = select.select([self.master_fd], [], [], 0.1)
            if r:
                chunk = os.read(self.master_fd, 1024)
                # NOTE assuming the prompt ends with '$'
                # we don't return this chunk because it's the `user@host` line
                if b'$ ' in chunk:
                    self.userhost = chunk.decode()
                    break
                output += chunk
            else:
                break
        # strip off the command from the output
        output_lines = output.decode().splitlines()
        if output_lines:
            return '\n'.join(output_lines[1:])
        return ''

    def close(self):
        os.close(self.master_fd)
        self.process.terminate()
        self.process.wait()

if __name__ == '__main__':
    terminal = BashTerminalEmulator()
    all_files = terminal.run_command("ls -al")
    empty = terminal.run_command("cd ..")
    all_files = terminal.run_command("ls -al")
    empty = terminal.run_command("cd -")
    git_status = terminal.run_command("git status")
    git_log = terminal.run_command("git log")
    # print(all_files)
    # print(git_status)
    print(terminal.history)
    terminal.close()