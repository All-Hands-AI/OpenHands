from dataclasses import dataclass, field
from typing import MutableMapping

import httpx

from openhands.core.logger import openhands_logger as logger

CLIENT = httpx.Client()


@dataclass
class HttpSession:
    """
    request.Session is reusable after it has been closed. This behavior makes it
    likely to leak file descriptors (Especially when combined with tenacity).
    We wrap the session to make it unusable after being closed
    """

    _is_closed: bool = False
    headers: MutableMapping[str, str] = field(default_factory=dict)

    def request(self, *args, **kwargs):
        if self._is_closed:
            logger.error(
                'Session is being used after close!', stack_info=True, exc_info=True
            )
            self._is_closed = False
        headers = kwargs.get('headers') or {}
        headers = {**self.headers, **headers}
        kwargs['headers'] = headers
        return CLIENT.request(*args, **kwargs)

    def stream(self, *args, **kwargs):
        if self._is_closed:
            logger.error(
                'Session is being used after close!', stack_info=True, exc_info=True
            )
            self._is_closed = False
        headers = kwargs.get('headers') or {}
        headers = {**self.headers, **headers}
        kwargs['headers'] = headers
        return CLIENT.stream(*args, **kwargs)

    def get(self, *args, **kwargs):
        return self.request('GET', *args, **kwargs)

    def post(self, *args, **kwargs):
        return self.request('POST', *args, **kwargs)

    def patch(self, *args, **kwargs):
        return self.request('PATCH', *args, **kwargs)

    def put(self, *args, **kwargs):
        return self.request('PUT', *args, **kwargs)

    def delete(self, *args, **kwargs):
        return self.request('DELETE', *args, **kwargs)

    def options(self, *args, **kwargs):
        return self.request('OPTIONS', *args, **kwargs)

    def close(self) -> None:
        self._is_closed = True
