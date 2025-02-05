from dataclasses import dataclass, field

import requests

from openhands.core.logger import openhands_logger as logger


@dataclass
class HttpSession:
    """
    request.Session is reusable after it has been closed. This behavior makes it
    likely to leak file descriptors (Especially when combined with tenacity).
    We wrap the session to make it unusable after being closed
    """

    session: requests.Session | None = field(default_factory=requests.Session)

    def __getattr__(self, name):
        if self.session is None:
            logger.error(
                'Session is being used after close!', stack_info=True, exc_info=True
            )
        return object.__getattribute__(self.session, name)

    def close(self):
        if self.session is not None:
            self.session.close()
