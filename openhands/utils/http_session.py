import os
import ssl
from dataclasses import dataclass, field
from threading import Lock
from typing import MutableMapping

import httpx

from openhands.core.logger import openhands_logger as logger


def _env_insecure_skip_verify() -> bool:
    truthy = {'1', 'true', 'yes', 'on'}
    for env_var in ('OPENHANDS_INSECURE_SKIP_VERIFY', 'INSECURE_SKIP_VERIFY'):
        value = os.environ.get(env_var)
        if value is not None:
            return value.strip().lower() in truthy
    return False


_client_lock = Lock()
_verify_certificates: bool = not _env_insecure_skip_verify()
_client: httpx.Client | None = None


def httpx_verify_option() -> ssl.SSLContext | bool:
    """Return the verify option to pass when creating an HTTPX client."""

    if _env_insecure_skip_verify():
        return False
    return ssl.create_default_context()


def _build_client(verify: bool) -> httpx.Client:
    if verify:
        return httpx.Client(verify=ssl.create_default_context())
    return httpx.Client(verify=False)


def _get_client() -> httpx.Client:
    global _client
    if _client is None:
        with _client_lock:
            if _client is None:
                _client = _build_client(_verify_certificates)
    return _client


def configure_http_session(*, verify: bool | None = None) -> None:
    """Configure the shared HTTPX client used by HttpSession."""

    global _client, _verify_certificates

    target_verify = _verify_certificates
    if verify is not None:
        target_verify = verify
    elif _client is None:
        # Ensure we honour environment variables on first configuration
        target_verify = not _env_insecure_skip_verify()

    if target_verify == _verify_certificates and _client is not None:
        return

    with _client_lock:
        if _client is not None:
            _client.close()
        _verify_certificates = target_verify
        _client = _build_client(_verify_certificates)


@dataclass
class HttpSession:
    """request.Session is reusable after it has been closed. This behavior makes it
    likely to leak file descriptors (Especially when combined with tenacity).
    We wrap the session to make it unusable after being closed
    """

    _is_closed: bool = False
    headers: MutableMapping[str, str] = field(default_factory=dict)

    def request(self, *args, **kwargs):
        if self._is_closed:
            logger.error(
                'Session is being used after close!', stack_info=True, exc_info=True
            )
            self._is_closed = False
        headers = kwargs.get('headers') or {}
        headers = {**self.headers, **headers}
        kwargs['headers'] = headers
        return _get_client().request(*args, **kwargs)

    def stream(self, *args, **kwargs):
        if self._is_closed:
            logger.error(
                'Session is being used after close!', stack_info=True, exc_info=True
            )
            self._is_closed = False
        headers = kwargs.get('headers') or {}
        headers = {**self.headers, **headers}
        kwargs['headers'] = headers
        return _get_client().stream(*args, **kwargs)

    def get(self, *args, **kwargs):
        return self.request('GET', *args, **kwargs)

    def post(self, *args, **kwargs):
        return self.request('POST', *args, **kwargs)

    def patch(self, *args, **kwargs):
        return self.request('PATCH', *args, **kwargs)

    def put(self, *args, **kwargs):
        return self.request('PUT', *args, **kwargs)

    def delete(self, *args, **kwargs):
        return self.request('DELETE', *args, **kwargs)

    def options(self, *args, **kwargs):
        return self.request('OPTIONS', *args, **kwargs)

    def close(self) -> None:
        self._is_closed = True
