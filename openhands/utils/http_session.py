from dataclasses import dataclass, field
from typing import Any, cast

import httpx
from requests.structures import CaseInsensitiveDict

from openhands.core.logger import openhands_logger as logger


@dataclass
class HttpSession:
    """
    request.Session is reusable after it has been closed. This behavior makes it
    likely to leak file descriptors (Especially when combined with tenacity).
    We wrap the session to make it unusable after being closed
    """

    client: httpx.Client | None = field(default_factory=httpx.Client)

    def __getattr__(self, name: str) -> Any:
        if self.client is None:
            logger.error(
                'Session is being used after close!', stack_info=True, exc_info=True
            )
            self.client = httpx.Client()
        return getattr(self.client, name)

    @property
    def headers(self) -> CaseInsensitiveDict[str]:
        if self.client is None:
            logger.error(
                'Session is being used after close!', stack_info=True, exc_info=True
            )
            self.client = httpx.Client()
        # Cast to CaseInsensitiveDict[str] since mypy doesn't know the exact type
        return cast(CaseInsensitiveDict[str], self.client.headers)

    def close(self) -> None:
        if self.client is not None:
            self.client.close()
            self.client = None
