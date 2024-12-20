import json
from typing import Any

import requests


class RequestHTTPError(requests.HTTPError):
    """Exception raised when an error occurs in a request with details."""

    def __init__(self, *args, detail=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.detail = detail

    def __str__(self) -> str:
        s = super().__str__()
        if self.detail is not None:
            s += f'\nDetails: {self.detail}'
        return s


def send_request(
    session: requests.Session,
    method: str,
    url: str,
    timeout: int = 10,
    **kwargs: Any,
) -> requests.Response:
    response = session.request(method, url, timeout=timeout, **kwargs)
    try:
        response.raise_for_status()
    except requests.HTTPError as e:
        try:
            _json = response.json()
        except (requests.exceptions.JSONDecodeError, json.decoder.JSONDecodeError):
            _json = None
        raise RequestHTTPError(
            e,
            response=e.response,
            detail=_json.get('detail') if _json is not None else None,
        ) from e
    return response
