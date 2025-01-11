import json
from typing import Any

import requests
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from openhands.core.logger import openhands_logger as logger
from openhands.utils.tenacity_stop import stop_if_should_exit


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


def is_retryable_error(exception):
    """Check if an error is retryable.

    Args:
        exception: The exception to check

    Returns:
        bool: True if the error is retryable, False otherwise
    """
    is_rate_limit = (
        isinstance(exception, requests.HTTPError)
        and exception.response.status_code == 429
    )
    is_connection_error = isinstance(exception, requests.ConnectionError)
    is_timeout = isinstance(exception, requests.Timeout)

    if any([is_rate_limit, is_connection_error, is_timeout]):
        logger.warning(
            f'Encountered retryable error: {type(exception).__name__}: {str(exception)}'
        )
        return True
    return False


def log_retry_attempt(retry_state):
    """Log retry attempt details.

    Args:
        retry_state: The current retry state
    """
    if retry_state.attempt_number > 1:  # Only log retries, not the first attempt
        logger.warning(
            f'Retry attempt {retry_state.attempt_number} after {retry_state.outcome.exception()}'
        )


@retry(
    retry=retry_if_exception(is_retryable_error),
    stop=stop_after_attempt(5) | stop_if_should_exit(),
    wait=wait_exponential(multiplier=2, min=8, max=120),
    before_sleep=log_retry_attempt,
)
def send_request(
    session: requests.Session,
    method: str,
    url: str,
    timeout: int = 30,  # Increased default timeout
    **kwargs: Any,
) -> requests.Response:
    """Send an HTTP request with retry logic.

    Args:
        session: The requests session to use
        method: The HTTP method to use
        url: The URL to send the request to
        timeout: The request timeout in seconds
        **kwargs: Additional arguments to pass to requests

    Returns:
        requests.Response: The response from the server

    Raises:
        RequestHTTPError: If the request fails with an HTTP error
        requests.RequestException: For other request failures
    """
    try:
        logger.debug(f'Sending {method} request to {url}')
        response = session.request(method, url, timeout=timeout, **kwargs)
        response.raise_for_status()
        return response
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
    except (requests.ConnectionError, requests.Timeout) as e:
        logger.debug(f'Request failed: {type(e).__name__}: {str(e)}')
        raise
