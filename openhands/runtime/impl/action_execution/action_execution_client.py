import os
import tempfile
import threading
from abc import abstractmethod
from pathlib import Path
from typing import Any
from zipfile import ZipFile

import requests
import tenacity

from openhands.core.config import AppConfig
from openhands.core.exceptions import (
    AgentRuntimeNotReadyError,
)
from openhands.events import EventStream
from openhands.runtime.base import Runtime
from openhands.runtime.plugins import PluginRequirement
from openhands.runtime.utils.request import send_request
from openhands.utils.tenacity_stop import stop_if_should_exit


class ActionExecutionClient(Runtime):
    """Base class for runtimes that interact with the action execution server.

    This class contains shared logic between EventStreamRuntime and RemoteRuntime
    for interacting with the HTTP server defined in action_execution_server.py.
    """

    def __init__(
        self,
        config: AppConfig,
        event_stream: EventStream,
        sid: str = 'default',
        plugins: list[PluginRequirement] | None = None,
        env_vars: dict[str, str] | None = None,
        status_callback: Any | None = None,
        attach_to_existing: bool = False,
        headless_mode: bool = True,
    ):
        self.session = requests.Session()
        self.action_semaphore = threading.Semaphore(1)  # Ensure one action at a time
        self._runtime_initialized: bool = False
        self._vscode_url: str | None = None  # initial dummy value
        super().__init__(
            config,
            event_stream,
            sid,
            plugins,
            env_vars,
            status_callback,
            attach_to_existing,
            headless_mode,
        )

    @abstractmethod
    def _get_api_url(self) -> str:
        pass

    def _send_request(
        self,
        method: str,
        url: str,
        is_retry: bool = True,
        **kwargs,
    ) -> requests.Response:
        """Send a request to the action execution server.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: URL to send the request to
            is_retry: Whether to retry the request on failure
            **kwargs: Additional arguments to pass to requests.request()

        Returns:
            Response from the server

        Raises:
            AgentRuntimeError: If the request fails
        """
        if not self._runtime_initialized and not url.endswith('/alive'):
            raise AgentRuntimeNotReadyError('Runtime client is not ready.')

        if is_retry:
            retry_decorator = tenacity.retry(
                stop=tenacity.stop_after_delay(120) | stop_if_should_exit(),
                retry=tenacity.retry_if_exception_type(
                    (ConnectionError, requests.exceptions.ConnectionError)
                ),
                reraise=True,
                wait=tenacity.wait_fixed(2),
            )
            return retry_decorator(send_request)(self.session, method, url, **kwargs)
        else:
            return send_request(self.session, method, url, **kwargs)

    def list_files(self, path: str | None = None) -> list[str]:
        """List files in the sandbox.

        If path is None, list files in the sandbox's initial working directory (e.g., /workspace).
        """

        try:
            data = {}
            if path is not None:
                data['path'] = path

            with send_request(
                self.session,
                'POST',
                f'{self._get_api_url()}/list_files',
                json=data,
                timeout=10,
            ) as response:
                response_json = response.json()
                assert isinstance(response_json, list)
                return response_json
        except requests.Timeout:
            raise TimeoutError('List files operation timed out')

    def copy_from(self, path: str) -> Path:
        """Zip all files in the sandbox and return as a stream of bytes."""

        try:
            params = {'path': path}
            with send_request(
                self.session,
                'GET',
                f'{self._get_api_url()}/download_files',
                params=params,
                stream=True,
                timeout=30,
            ) as response:
                temp_file = tempfile.NamedTemporaryFile(delete=False)
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:  # filter out keep-alive new chunks
                        temp_file.write(chunk)
                return Path(temp_file.name)
        except requests.Timeout:
            raise TimeoutError('Copy operation timed out')

    def copy_to(
        self, host_src: str, sandbox_dest: str, recursive: bool = False
    ) -> None:
        if not os.path.exists(host_src):
            raise FileNotFoundError(f'Source file {host_src} does not exist')

        try:
            if recursive:
                with tempfile.NamedTemporaryFile(
                    suffix='.zip', delete=False
                ) as temp_zip:
                    temp_zip_path = temp_zip.name

                with ZipFile(temp_zip_path, 'w') as zipf:
                    for root, _, files in os.walk(host_src):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(
                                file_path, os.path.dirname(host_src)
                            )
                            zipf.write(file_path, arcname)

                upload_data = {'file': open(temp_zip_path, 'rb')}
            else:
                upload_data = {'file': open(host_src, 'rb')}

            params = {'destination': sandbox_dest, 'recursive': str(recursive).lower()}

            with self._send_request(
                'POST',
                f'{self._get_api_url()}/upload_file',
                is_retry=False,
                files=upload_data,
                params=params,
                timeout=300,
            ) as response:
                self.log(
                    'debug',
                    f'Copy completed: host:{host_src} -> runtime:{sandbox_dest}. Response: {response.text}',
                )
        finally:
            if recursive:
                os.unlink(temp_zip_path)
            self.log(
                'debug', f'Copy completed: host:{host_src} -> runtime:{sandbox_dest}'
            )

    def get_vscode_token(self) -> str:
        if self.vscode_enabled and self._runtime_initialized:
            if (
                hasattr(self, '_vscode_url') and self._vscode_url is not None
            ):  # cached value
                return self._vscode_url

            with send_request(
                self.session,
                'GET',
                f'{self._get_api_url()}/vscode/connection_token',
                timeout=10,
            ) as response:
                response_json = response.json()
                assert isinstance(response_json, dict)
                if response_json['token'] is None:
                    return ''
                return response_json['token']
        else:
            return ''
