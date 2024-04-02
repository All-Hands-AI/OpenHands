# Adopot from dockerpty/io.py
# dockerpty: io.py
#
# Copyright 2014 Chris Corbyn <chris@w3style.co.uk>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import fcntl
import errno


def set_blocking(fd, blocking=True):
    """
    Set the given file-descriptor blocking or non-blocking.

    Returns the original blocking status.
    """

    old_flag = fcntl.fcntl(fd, fcntl.F_GETFL)

    if blocking:
        new_flag = old_flag & ~ os.O_NONBLOCK
    else:
        new_flag = old_flag | os.O_NONBLOCK

    fcntl.fcntl(fd, fcntl.F_SETFL, new_flag)

    return not bool(old_flag & os.O_NONBLOCK)


class Stream(object):
    """
    Generic Stream class.

    This is a file-like abstraction on top of os.read() and os.write(), which
    add consistency to the reading of sockets and files alike.
    """

    """
    Recoverable IO/OS Errors.
    """
    ERRNO_RECOVERABLE = [
        errno.EINTR,
        errno.EDEADLK,
        errno.EWOULDBLOCK,
    ]

    def __init__(self, fd):
        """
        Initialize the Stream for the file descriptor `fd`.

        The `fd` object must have a `fileno()` method.
        """
        self.fd = fd
        self.buffer = b''
        self.close_requested = False
        self.closed = False

    def fileno(self):
        """
        Return the fileno() of the file descriptor.
        """

        return self.fd.fileno()

    def set_blocking(self, value):
        if hasattr(self.fd, 'setblocking'):
            self.fd.setblocking(value)
            return True
        else:
            return set_blocking(self.fd, value)

    def read(self, n=4096):
        """
        Return `n` bytes of data from the Stream, or None at end of stream.
        """

        while True:
            try:
                if hasattr(self.fd, 'recv'):
                    return self.fd.recv(n)
                return os.read(self.fd.fileno(), n)
            except EnvironmentError as e:
                if e.errno not in Stream.ERRNO_RECOVERABLE:
                    raise e


    def write(self, data):
        """
        Write `data` to the Stream. Not all data may be written right away.
        Use select to find when the stream is writeable, and call do_write()
        to flush the internal buffer.
        """

        if not data:
            return None

        self.buffer += data
        self.do_write()

        return len(data)

    def do_write(self):
        """
        Flushes as much pending data from the internal write buffer as possible.
        """
        while True:
            try:
                written = 0

                if hasattr(self.fd, 'send'):
                    written = self.fd.send(self.buffer)
                else:
                    written = os.write(self.fd.fileno(), self.buffer)

                self.buffer = self.buffer[written:]

                # try to close after writes if a close was requested
                if self.close_requested and len(self.buffer) == 0:
                    self.close()

                return written
            except EnvironmentError as e:
                if e.errno not in Stream.ERRNO_RECOVERABLE:
                    raise e

    def needs_write(self):
        """
        Returns True if the stream has data waiting to be written.
        """
        return len(self.buffer) > 0

    def close(self):
        self.close_requested = True

        # We don't close the fd immediately, as there may still be data pending
        # to write.
        if not self.closed and len(self.buffer) == 0:
            self.closed = True
            if hasattr(self.fd, 'close'):
                self.fd.close()
            else:
                os.close(self.fd.fileno())

    def __repr__(self):
        return "{cls}({fd})".format(cls=type(self).__name__, fd=self.fd)
