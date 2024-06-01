import re
import time

from pexpect import exceptions

from opendevin.core.schema import CancellableStream


class SSHCancellableStream(CancellableStream):
    def __init__(self, ssh, cmd, timeout):
        super().__init__(self.read_output())
        self.ssh = ssh
        self.cmd = cmd
        self.timeout = timeout

    def close(self):
        self.closed = True

    def exit_code(self):
        self.ssh.sendline('echo $?')
        success = self.ssh.prompt(timeout=self.timeout)
        if not success:
            return -1

        _exit_code = self.ssh.before.strip()
        return int(_exit_code)

    def read_output(self):
        st = time.time()
        buf = ''
        crlf = '\r\n'
        lf = '\n'
        prompt_len = len(self.ssh.PROMPT)
        while True:
            try:
                if self.closed:
                    break
                _output = self.ssh.read_nonblocking(timeout=1)
                if not _output:
                    continue

                buf += _output

                if len(buf) < prompt_len:
                    continue

                match = re.search(self.ssh.PROMPT, buf)
                if match:
                    idx, _ = match.span()
                    yield buf[:idx].replace(crlf, lf)
                    buf = ''
                    break

                res = buf[:-prompt_len]
                if len(res) == 0 or res.find(crlf) == -1:
                    continue
                buf = buf[-prompt_len:]
                yield res.replace(crlf, lf)
            except exceptions.TIMEOUT:
                if time.time() - st < self.timeout:
                    match = re.search(self.ssh.PROMPT, buf)
                    if match:
                        idx, _ = match.span()
                        yield buf[:idx].replace(crlf, lf)
                        break
                    continue
                else:
                    yield buf.replace(crlf, lf)
                break
            except exceptions.EOF:
                break
