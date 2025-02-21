from dataclasses import dataclass, field
from typing import Any, cast

import requests
from requests.structures import CaseInsensitiveDict

from openhands.core.logger import openhands_logger as logger


@dataclass
class HttpSession:
    """
    request.Session is reusable after it has been closed. This behavior makes it
    likely to leak file descriptors (Especially when combined with tenacity).
    We wrap the session to make it unusable after being closed
    """

    session: requests.Session | None = field(default_factory=requests.Session)

    def __getattr__(self, name: str) -> Any:
        if self.session is None:
            logger.error(
                'Session is being used after close!', stack_info=True, exc_info=True
            )
            raise RuntimeError('Session is being used after close!')
        return getattr(self.session, name)

    @property
    def headers(self) -> CaseInsensitiveDict[str]:
        if self.session is None:
            logger.error(
                'Session is being used after close!', stack_info=True, exc_info=True
            )
            raise RuntimeError('Session is being used after close!')
        # Cast to CaseInsensitiveDict[str] since mypy doesn't know the exact type
        return cast(CaseInsensitiveDict[str], self.session.headers)

    def close(self) -> None:
        if self.session is not None:
            self.session.close()
            self.session = None
