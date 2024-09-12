import ssl
from typing import Any, Type

import requests
from requests.exceptions import HTTPError, RequestException, Timeout
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

DEFAULT_RETRY_EXCEPTIONS = [
    ssl.SSLCertVerificationError,
    RequestException,
    HTTPError,
    Timeout,
]


def send_request(
    session: requests.Session,
    method: str,
    url: str,
    retry_exceptions: list[Type[Exception]] | None = None,
    n_attempts: int = 30,
    **kwargs: Any,
) -> requests.Response:
    if retry_exceptions is None:
        retry_exceptions = DEFAULT_RETRY_EXCEPTIONS

    @retry(
        stop=stop_after_attempt(n_attempts),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type(tuple(retry_exceptions)),
        reraise=True,
    )
    def _send_request_with_retry():
        response = session.request(method, url, **kwargs)
        response.raise_for_status()
        return response

    return _send_request_with_retry()
