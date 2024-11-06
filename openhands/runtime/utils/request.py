from typing import Any

import requests
from requests.exceptions import (
    ChunkedEncodingError,
    ConnectionError,
)
from urllib3.exceptions import IncompleteRead


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


def is_429_error(exception):
    return (
        isinstance(exception, requests.HTTPError)
        and exception.response.status_code == 429
    )


def is_503_error(exception):
    return (
        isinstance(exception, requests.HTTPError)
        and exception.response.status_code == 503
    )


def is_502_error(exception):
    return (
        isinstance(exception, requests.HTTPError)
        and exception.response.status_code == 502
    )


DEFAULT_RETRY_EXCEPTIONS = [
    ConnectionError,
    IncompleteRead,
    ChunkedEncodingError,
]


def send_request(
    session: requests.Session,
    method: str,
    url: str,
    timeout: int = 10,
    **kwargs: Any,
) -> requests.Response:
    response = session.request(method, url, **kwargs)
    response.raise_for_status()
    return response
