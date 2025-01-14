from dataclasses import dataclass, field

import requests


@dataclass
class HttpSession:
    """
    request.Session is reusable after it has been closed. This behavior makes it
    likely to leak file descriptors (Especially when combined with tenacity).
    We wrap the session to make it unusable after being closed
    """

    session: requests.Session | None = field(default_factory=requests.Session)

    def __getattr__(self, name):
        if self.session is not None:
            raise ValueError('session_was_closed')
        return object.__getattribute__(self.session, name)

    def close(self):
        if self.session is not None:
            self.session.close()
        self.session = None
