from dataclasses import dataclass, field
from typing import MutableMapping

import requests

from openhands.core.logger import openhands_logger as logger

SESSION = requests.Session()


@dataclass
class HttpSession:
    """
    This class gives us the flexibility to handle http connections efficiently, pooling where
    possible. Each session has different http headers, though we use a single shared httpx client
    instance. (Which is thread safe).
    We maintain a close method mostly to track unclosed connections, though reuse of the class after
    close is not prevented.
    """

    _headers: MutableMapping[str, str] = field(default_factory=dict)
    is_closed: bool = False

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

    def request(self, method, *args, **kwargs):
        if self.is_closed:
            logger.error(
                'Session is being used after close!', stack_info=True, exc_info=True
            )
            self.is_closed = False
        headers = {**self._headers}
        if 'headers' in kwargs:
            headers.update(**kwargs['headers'])
        kwargs['headers'] = headers
        response = SESSION.request(method, *args, **kwargs)
        return response

    @property
    def headers(self) -> MutableMapping[str, str]:
        return self._headers

    def close(self) -> None:
        self.is_closed = True
        # This closes all TCP sessions which are not currently in use, but doesn't
        # prevent new connections. Closing periodically seems smart.
        SESSION.close()
