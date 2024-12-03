from typing import Any

import requests


class RequestError(requests.HTTPError):
    """Exception raised when an error occurs in a request with details."""

    def __init__(self, *args, details=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.details = details

    def __str__(self) -> str:
        return f'HTTP Error occurred: {super().__str__()}\nDetails: {self.details or "No additional details available."}'


def send_request(
    session: requests.Session,
    method: str,
    url: str,
    timeout: int = 10,
    **kwargs: Any,
) -> requests.Response:
    response = session.request(method, url, **kwargs)
    try:
        response.raise_for_status()
    except requests.HTTPError as e:
        try:
            _json = response.json()
        except requests.JSONDecodeError:
            raise e
        raise RequestError(e, details=_json.get('detail')) from e
    return response
