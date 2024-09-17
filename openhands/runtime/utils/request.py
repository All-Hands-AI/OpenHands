from typing import Any, Callable, Type

import requests
from requests.exceptions import ConnectionError, Timeout
from tenacity import (
    retry,
    retry_if_exception,
    retry_if_exception_type,
    stop_after_delay,
    wait_exponential,
)


def is_server_error(exception):
    return (
        isinstance(exception, requests.HTTPError)
        and exception.response.status_code >= 500
    )


def is_404_error(exception):
    return (
        isinstance(exception, requests.HTTPError)
        and exception.response.status_code == 404
    )


DEFAULT_RETRY_EXCEPTIONS = [
    ConnectionError,
    Timeout,
]


def send_request(
    session: requests.Session,
    method: str,
    url: str,
    retry_exceptions: list[Type[Exception]] | None = None,
    retry_fns: list[Callable[[Exception], bool]] | None = None,
    timeout: int = 120,
    **kwargs: Any,
) -> requests.Response:
    exceptions_to_catch = retry_exceptions or DEFAULT_RETRY_EXCEPTIONS
    retry_condition = retry_if_exception_type(
        tuple(exceptions_to_catch)
    ) | retry_if_exception(is_server_error)
    if retry_fns is not None:
        for fn in retry_fns:
            retry_condition |= retry_if_exception(fn)

    @retry(
        stop=stop_after_delay(timeout),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_condition,
        reraise=True,
    )
    def _send_request_with_retry():
        response = session.request(method, url, **kwargs)
        response.raise_for_status()
        return response

    return _send_request_with_retry()
