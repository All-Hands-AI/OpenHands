import os
import pty
import subprocess
import select
import socket

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
        # get rid of `b'bash: no job control in this shell\r\n'` and initial shell prompt
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
                # HACK naively assuming the prompt ends with '$'
                # we don't return this chunk because it's the `user@host` line
                if b'$ ' in chunk:
                    self.userhost = chunk.decode()
                    break
                output += chunk
            else:
                break
        # strip off the input command from the output
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
    # print(all_files)
    # total 16
    # drwxr-xr-x   6 zibo  staff   192 Mar 17 01:55 .
    # drwxr-xr-x  18 zibo  staff   576 Mar 16 21:46 ..
    # drwxr-xr-x  12 zibo  staff   384 Mar 17 02:45 .git
    # -rw-r--r--   1 zibo  staff   418 Mar 16 21:46 README.md
    # -rw-r--r--   1 zibo  staff  2354 Mar 17 02:46 console.py
    # drwxr-xr-x   9 zibo  staff   288 Mar 16 21:46 frontend

    empty = terminal.run_command("cd ..")
    all_files = terminal.run_command("ls -al")
    # print(all_files)
    # total 16
    # drwxr-xr-x  18 zibo  staff   576 Mar 16 21:46 .
    # drwxr-x---+ 49 zibo  staff  1568 Mar 17 02:45 ..
    # -rw-r--r--@  1 zibo  staff  6148 Mar  6 01:24 .DS_Store
    # drwxr-xr-x  27 zibo  staff   864 Mar 16 17:30 MetaGPT
    # drwxr-xr-x   6 zibo  staff   192 Mar 17 01:55 OpenDevin
    # ...

    pwd = terminal.run_command("cd -")
    # print(pwd)
    # /Users/zibo/fun/OpenDevin

    git_status = terminal.run_command("git status")
    # print(git_status)
    # On branch dev/terminal
    # Your branch is up to date with 'origin/dev/terminal'.
    #
    # Changes not staged for commit:
    #   (use "git add <file>..." to update what will be committed)
    #   (use "git restore <file>..." to discard changes in working directory)
    #         modified:   console.py
    #
    # no changes added to commit (use "git add" and/or "git commit -a")

    git_log = terminal.run_command("git log")

    # this should print the entire log, with the text looking identical to if you had entered each command one by one
    # print(terminal.history)

    terminal.close()