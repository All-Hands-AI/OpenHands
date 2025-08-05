import os
import tempfile
import threading
import time
import fcntl
import json
from pathlib import Path
from typing import Any
from zipfile import ZipFile

import httpcore
import httpx
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from openhands.core.config import OpenHandsConfig
from openhands.core.config.mcp_config import (
    MCPConfig,
    MCPSSEServerConfig,
    MCPStdioServerConfig,
)
from openhands.core.exceptions import AgentRuntimeTimeoutError
from openhands.events import EventStream
from openhands.events.action import (
    ActionConfirmationStatus,
    AgentThinkAction,
    BrowseInteractiveAction,
    BrowseURLAction,
    CmdRunAction,
    FileEditAction,
    FileReadAction,
    FileWriteAction,
    IPythonRunCellAction,
)
from openhands.events.action.action import Action
from openhands.events.action.files import FileEditSource
from openhands.events.action.mcp import MCPAction
from openhands.events.observation import (
    AgentThinkObservation,
    ErrorObservation,
    NullObservation,
    Observation,
    UserRejectObservation,
)
from openhands.events.serialization import event_to_dict, observation_from_dict
from openhands.events.serialization.action import ACTION_TYPE_TO_CLASS
from openhands.integrations.provider import PROVIDER_TOKEN_TYPE
from openhands.runtime.base import Runtime
from openhands.runtime.plugins import PluginRequirement
from openhands.runtime.utils.request import send_request
from openhands.runtime.utils.system_stats import update_last_execution_time
from openhands.utils.http_session import HttpSession
from openhands.utils.tenacity_stop import stop_if_should_exit


# Global coordination directory for tracking active requests across all worker processes
_COORDINATION_DIR = None


def _get_coordination_dir():
    """Get or create the coordination directory."""
    global _COORDINATION_DIR
    if _COORDINATION_DIR is None:
        _COORDINATION_DIR = Path(tempfile.gettempdir()) / "openhands_request_coordination"
        _COORDINATION_DIR.mkdir(exist_ok=True)
    return _COORDINATION_DIR


class FileBasedRequestCoordinator:
    """File-based coordination system for tracking active requests and lifecycle operations."""

    def __init__(self):
        self.coord_dir = _get_coordination_dir()
        self.active_requests_file = self.coord_dir / "active_requests.json"
        self.lifecycle_lock_file = self.coord_dir / "lifecycle.lock"

        # Initialize active requests file if it doesn't exist
        if not self.active_requests_file.exists():
            self._write_active_requests(0)

    def _write_active_requests(self, count: int):
        """Write the active request count to file."""
        with open(self.active_requests_file, 'w') as f:
            json.dump({'count': count}, f)

    def _read_active_requests(self) -> int:
        """Read the active request count from file."""
        try:
            with open(self.active_requests_file, 'r') as f:
                data = json.load(f)
                return data.get('count', 0)
        except (FileNotFoundError, json.JSONDecodeError):
            return 0

    def increment_requests(self):
        """Atomically increment the active request count."""
        # Ensure file exists
        if not self.active_requests_file.exists():
            self._write_active_requests(0)

        with open(self.active_requests_file, 'r+') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                f.seek(0)
                data = json.load(f)
                count = data.get('count', 0)
            except json.JSONDecodeError:
                count = 0

            count += 1
            f.seek(0)
            json.dump({'count': count}, f)
            f.truncate()

    def decrement_requests(self):
        """Atomically decrement the active request count."""
        # Ensure file exists
        if not self.active_requests_file.exists():
            self._write_active_requests(0)

        with open(self.active_requests_file, 'r+') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                f.seek(0)
                data = json.load(f)
                count = data.get('count', 0)
            except json.JSONDecodeError:
                count = 0

            count = max(0, count - 1)
            f.seek(0)
            json.dump({'count': count}, f)
            f.truncate()

    def wait_for_no_active_requests(self, timeout: float = 30.0) -> bool:
        """Wait until there are no active requests."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self._read_active_requests() == 0:
                return True
            time.sleep(0.1)
        return False

    def acquire_lifecycle_lock(self, timeout: float = 30.0) -> bool:
        """Acquire the lifecycle lock, preventing new requests."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                # Try to create the lock file exclusively
                fd = os.open(self.lifecycle_lock_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.close(fd)
                return True
            except FileExistsError:
                time.sleep(0.1)
        return False

    def release_lifecycle_lock(self):
        """Release the lifecycle lock, allowing new requests."""
        try:
            self.lifecycle_lock_file.unlink()
        except FileNotFoundError:
            pass  # Already released

    def is_lifecycle_operation_active(self) -> bool:
        """Check if a lifecycle operation is currently active."""
        return self.lifecycle_lock_file.exists()


# Global coordinator instance
_coordinator = None


def _get_coordinator():
    """Get or create the global coordinator."""
    global _coordinator
    if _coordinator is None:
        _coordinator = FileBasedRequestCoordinator()
    return _coordinator


def _is_retryable_error(exception):
    return isinstance(
        exception, (
            httpx.ReadError,
            httpcore.ReadError,
            httpx.RemoteProtocolError,
            httpcore.RemoteProtocolError,
            httpx.ConnectError,
            httpcore.ConnectError,
            ConnectionError,
            OSError  # Covers errno 111 (Connection refused)
        )
    )


class ActionExecutionClient(Runtime):
    """Base class for runtimes that interact with the action execution server.

    This class contains shared logic between DockerRuntime and RemoteRuntime
    for interacting with the HTTP server defined in action_execution_server.py.
    """

    def __init__(
        self,
        config: OpenHandsConfig,
        event_stream: EventStream,
        sid: str = 'default',
        plugins: list[PluginRequirement] | None = None,
        env_vars: dict[str, str] | None = None,
        status_callback: Any | None = None,
        attach_to_existing: bool = False,
        headless_mode: bool = True,
        user_id: str | None = None,
        git_provider_tokens: PROVIDER_TOKEN_TYPE | None = None,
    ):
        self.session = HttpSession()
        self.action_semaphore = threading.Semaphore(1)
        self._runtime_closed: bool = False
        self._vscode_token: str | None = None  # initial dummy value
        self._last_updated_mcp_stdio_servers: list[MCPStdioServerConfig] = []

        # Get file-based coordinator for request tracking across processes
        self._coordinator = _get_coordinator()

        super().__init__(
            config,
            event_stream,
            sid,
            plugins,
            env_vars,
            status_callback,
            attach_to_existing,
            headless_mode,
            user_id,
            git_provider_tokens,
        )

    @property
    def action_execution_server_url(self) -> str:
        raise NotImplementedError('Action execution server URL is not implemented')

    @retry(
        retry=retry_if_exception(_is_retryable_error),
        stop=stop_after_attempt(8) | stop_if_should_exit(),
        wait=wait_exponential(multiplier=1, min=2, max=30),
    )
    def _send_action_server_request(
        self,
        method: str,
        url: str,
        **kwargs,
    ) -> httpx.Response:
        """Send a request to the action execution server.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: URL to send the request to
            **kwargs: Additional arguments to pass to requests.request()

        Returns:
            Response from the server

        Raises:
            AgentRuntimeError: If the request fails
        """
        # For regular HTTP requests to containers, we don't need the Docker lifecycle lock
        # since we're just making HTTP calls to running containers. We only track the request.
        self._acquire_request_slot()
        try:
            return send_request(self.session, method, url, **kwargs)
        finally:
            self._release_request_slot()

    def check_if_alive(self) -> None:
        response = self._send_action_server_request(
            'GET',
            f'{self.action_execution_server_url}/alive',
            timeout=10,  # Increased timeout for more robustness
        )
        assert response.is_closed

    def list_files(self, path: str | None = None) -> list[str]:
        """List files in the sandbox.

        If path is None, list files in the sandbox's initial working directory (e.g., /workspace).
        """

        try:
            data = {}
            if path is not None:
                data['path'] = path

            response = self._send_action_server_request(
                'POST',
                f'{self.action_execution_server_url}/list_files',
                json=data,
                timeout=10,
            )
            assert response.is_closed
            response_json = response.json()
            assert isinstance(response_json, list)
            return response_json
        except httpx.TimeoutException:
            raise TimeoutError('List files operation timed out')

    def copy_from(self, path: str) -> Path:
        """Zip all files in the sandbox and return as a stream of bytes."""
        try:
            params = {'path': path}
            with self.session.stream(
                'GET',
                f'{self.action_execution_server_url}/download_files',
                params=params,
                timeout=30,
            ) as response:
                with tempfile.NamedTemporaryFile(
                    suffix='.zip', delete=False
                ) as temp_file:
                    for chunk in response.iter_bytes():
                        temp_file.write(chunk)
                    temp_file.flush()
                    return Path(temp_file.name)
        except httpx.TimeoutException:
            raise TimeoutError('Copy operation timed out')

    def copy_to(
        self, host_src: str, sandbox_dest: str, recursive: bool = False
    ) -> None:
        if not os.path.exists(host_src):
            raise FileNotFoundError(f'Source file {host_src} does not exist')

        temp_zip_path: str | None = None  # Define temp_zip_path outside the try block

        try:
            params = {'destination': sandbox_dest, 'recursive': str(recursive).lower()}
            file_to_upload = None
            upload_data = {}

            if recursive:
                # Create and write the zip file inside the try block
                with tempfile.NamedTemporaryFile(
                    suffix='.zip', delete=False
                ) as temp_zip:
                    temp_zip_path = temp_zip.name

                try:
                    with ZipFile(temp_zip_path, 'w') as zipf:
                        for root, _, files in os.walk(host_src):
                            for file in files:
                                file_path = os.path.join(root, file)
                                arcname = os.path.relpath(
                                    file_path, os.path.dirname(host_src)
                                )
                                zipf.write(file_path, arcname)

                    self.log(
                        'debug',
                        f'Opening temporary zip file for upload: {temp_zip_path}',
                    )
                    file_to_upload = open(temp_zip_path, 'rb')
                    upload_data = {'file': file_to_upload}
                except Exception as e:
                    # Ensure temp file is cleaned up if zipping fails
                    if temp_zip_path and os.path.exists(temp_zip_path):
                        os.unlink(temp_zip_path)
                    raise e  # Re-raise the exception after cleanup attempt
            else:
                file_to_upload = open(host_src, 'rb')
                upload_data = {'file': file_to_upload}

            params = {'destination': sandbox_dest, 'recursive': str(recursive).lower()}

            response = self._send_action_server_request(
                'POST',
                f'{self.action_execution_server_url}/upload_file',
                files=upload_data,
                params=params,
                timeout=300,
            )
            self.log(
                'debug',
                f'Copy completed: host:{host_src} -> runtime:{sandbox_dest}. Response: {response.text}',
            )
        finally:
            if file_to_upload:
                file_to_upload.close()

            # Cleanup the temporary zip file if it was created
            if temp_zip_path and os.path.exists(temp_zip_path):
                try:
                    os.unlink(temp_zip_path)
                except Exception as e:
                    self.log(
                        'error',
                        f'Failed to delete temporary zip file {temp_zip_path}: {e}',
                    )

    def get_vscode_token(self) -> str:
        if self.vscode_enabled and self.runtime_initialized:
            if self._vscode_token is not None:  # cached value
                return self._vscode_token
            response = self._send_action_server_request(
                'GET',
                f'{self.action_execution_server_url}/vscode/connection_token',
                timeout=10,
            )
            response_json = response.json()
            assert isinstance(response_json, dict)
            if response_json['token'] is None:
                return ''
            self._vscode_token = response_json['token']
            return response_json['token']
        else:
            return ''

    def send_action_for_execution(self, action: Action) -> Observation:
        if (
            isinstance(action, FileEditAction)
            and action.impl_source == FileEditSource.LLM_BASED_EDIT
        ):
            return self.llm_based_edit(action)

        # set timeout to default if not set
        if action.timeout is None:
            if isinstance(action, CmdRunAction) and action.blocking:
                raise RuntimeError('Blocking command with no timeout set')
            # We don't block the command if this is a default timeout action
            action.set_hard_timeout(self.config.sandbox.timeout, blocking=False)

        with self.action_semaphore:
            if not action.runnable:
                if isinstance(action, AgentThinkAction):
                    return AgentThinkObservation('Your thought has been logged.')
                return NullObservation('')
            if (
                hasattr(action, 'confirmation_state')
                and action.confirmation_state
                == ActionConfirmationStatus.AWAITING_CONFIRMATION
            ):
                return NullObservation('')
            action_type = action.action  # type: ignore[attr-defined]
            if action_type not in ACTION_TYPE_TO_CLASS:
                raise ValueError(f'Action {action_type} does not exist.')
            if not hasattr(self, action_type):
                return ErrorObservation(
                    f'Action {action_type} is not supported in the current runtime.',
                    error_id='AGENT_ERROR$BAD_ACTION',
                )
            if (
                getattr(action, 'confirmation_state', None)
                == ActionConfirmationStatus.REJECTED
            ):
                return UserRejectObservation(
                    'Action has been rejected by the user! Waiting for further user input.'
                )

            assert action.timeout is not None

            # Pre-validate runtime health before executing action
            try:
                execution_action_body: dict[str, Any] = {
                    'action': event_to_dict(action),
                }
                response = self._send_action_server_request(
                    'POST',
                    f'{self.action_execution_server_url}/execute_action',
                    json=execution_action_body,
                    # wait a few more seconds to get the timeout error from client side
                    timeout=action.timeout + 5,
                )
                assert response.is_closed
                output = response.json()
                obs = observation_from_dict(output)
                obs._cause = action.id  # type: ignore[attr-defined]
            except httpx.TimeoutException:
                raise AgentRuntimeTimeoutError(
                    f'Runtime failed to return execute_action before the requested timeout of {action.timeout}s'
                )
            finally:
                update_last_execution_time()
            return obs

    def run(self, action: CmdRunAction) -> Observation:
        return self.send_action_for_execution(action)

    def run_ipython(self, action: IPythonRunCellAction) -> Observation:
        return self.send_action_for_execution(action)

    def read(self, action: FileReadAction) -> Observation:
        return self.send_action_for_execution(action)

    def write(self, action: FileWriteAction) -> Observation:
        return self.send_action_for_execution(action)

    def edit(self, action: FileEditAction) -> Observation:
        return self.send_action_for_execution(action)

    def browse(self, action: BrowseURLAction) -> Observation:
        return self.send_action_for_execution(action)

    def browse_interactive(self, action: BrowseInteractiveAction) -> Observation:
        return self.send_action_for_execution(action)

    def get_mcp_config(
        self, extra_stdio_servers: list[MCPStdioServerConfig] | None = None
    ) -> MCPConfig:
        import sys

        # Check if we're on Windows - MCP is disabled on Windows
        if sys.platform == 'win32':
            # Return empty MCP config on Windows
            self.log('debug', 'MCP is disabled on Windows, returning empty config')
            return MCPConfig(sse_servers=[], stdio_servers=[])

        # Add the runtime as another MCP server
        updated_mcp_config = self.config.mcp.model_copy()

        # Get current stdio servers
        current_stdio_servers: list[MCPStdioServerConfig] = list(
            updated_mcp_config.stdio_servers
        )
        if extra_stdio_servers:
            current_stdio_servers.extend(extra_stdio_servers)

        # Check if there are any new servers using the __eq__ operator
        new_servers = [
            server
            for server in current_stdio_servers
            if server not in self._last_updated_mcp_stdio_servers
        ]

        self.log(
            'debug',
            f'adding {len(new_servers)} new stdio servers to MCP config: {new_servers}',
        )

        # Only send update request if there are new servers
        if new_servers:
            # Use a union of current servers and last updated servers for the update
            # This ensures we don't lose any servers that might be missing from either list
            combined_servers = current_stdio_servers.copy()
            for server in self._last_updated_mcp_stdio_servers:
                if server not in combined_servers:
                    combined_servers.append(server)

            stdio_tools = [
                server.model_dump(mode='json') for server in combined_servers
            ]
            stdio_tools.sort(key=lambda x: x.get('name', ''))  # Sort by server name

            self.log(
                'debug',
                f'Updating MCP server with {len(new_servers)} new stdio servers (total: {len(combined_servers)})',
            )
            response = self._send_action_server_request(
                'POST',
                f'{self.action_execution_server_url}/update_mcp_server',
                json=stdio_tools,
                timeout=60,
            )
            result = response.json()
            if response.status_code != 200:
                self.log('warning', f'Failed to update MCP server: {response.text}')
            else:
                if result.get('router_error_log'):
                    self.log(
                        'warning',
                        f'Some MCP servers failed to be added: {result["router_error_log"]}',
                    )

                # Update our cached list with combined servers after successful update
                self._last_updated_mcp_stdio_servers = combined_servers.copy()
                self.log(
                    'debug',
                    f'Successfully updated MCP stdio servers, now tracking {len(combined_servers)} servers',
                )
            self.log(
                'info',
                f'Updated MCP config: {updated_mcp_config.sse_servers}',
            )
        else:
            self.log('debug', 'No new stdio servers to update')

        if len(self._last_updated_mcp_stdio_servers) > 0:
            # We should always include the runtime as an MCP server whenever there's > 0 stdio servers
            updated_mcp_config.sse_servers.append(
                MCPSSEServerConfig(
                    url=self.action_execution_server_url.rstrip('/') + '/mcp/sse',
                    api_key=self.session_api_key,
                )
            )

        return updated_mcp_config

    async def call_tool_mcp(self, action: MCPAction) -> Observation:
        import sys

        from openhands.events.observation import ErrorObservation

        # Check if we're on Windows - MCP is disabled on Windows
        if sys.platform == 'win32':
            self.log('info', 'MCP functionality is disabled on Windows')
            return ErrorObservation('MCP functionality is not available on Windows')

        # Import here to avoid circular imports
        from openhands.mcp.utils import call_tool_mcp as call_tool_mcp_handler
        from openhands.mcp.utils import create_mcp_clients

        # Get the updated MCP config
        updated_mcp_config = self.get_mcp_config()
        self.log(
            'debug',
            f'Creating MCP clients with servers: {updated_mcp_config.sse_servers}',
        )

        # Create clients for this specific operation
        mcp_clients = await create_mcp_clients(
            updated_mcp_config.sse_servers, updated_mcp_config.shttp_servers, self.sid
        )

        # Call the tool and return the result
        # No need for try/finally since disconnect() is now just resetting state
        result = await call_tool_mcp_handler(mcp_clients, action)
        return result

    def _acquire_request_slot(self) -> None:
        """Acquire a request slot, waiting if a lifecycle operation is in progress."""
        # Wait for any lifecycle operation to complete
        start_time = time.time()
        while self._coordinator.is_lifecycle_operation_active():
            if time.time() - start_time > self.config.sandbox.timeout:
                raise RuntimeError("Timeout waiting for lifecycle operation to complete")
            time.sleep(5)

        # Increment active request count
        self._coordinator.increment_requests()

    def _release_request_slot(self) -> None:
        """Release a request slot."""
        self._coordinator.decrement_requests()

    def _wait_for_active_requests(self, timeout: float = 30.0) -> bool:
        """Wait for all active requests to complete.

        Returns True if all requests completed, False if timeout occurred.
        """
        return self._coordinator.wait_for_no_active_requests(timeout)

    def _begin_lifecycle_operation(self, timeout: float = 30.0) -> bool:
        """Begin a lifecycle operation, blocking new requests and waiting for active ones.

        Returns True if operation can proceed, False if timeout occurred.
        """
        # Try to acquire the lifecycle lock
        if not self._coordinator.acquire_lifecycle_lock(timeout):
            return False

        # Wait for active requests to complete
        if self._wait_for_active_requests(timeout):
            return True
        else:
            # Timeout occurred, release the lock
            self._coordinator.release_lifecycle_lock()
            return False

    def _end_lifecycle_operation(self) -> None:
        """End a lifecycle operation, allowing new requests."""
        self._coordinator.release_lifecycle_lock()

    def close(self) -> None:
        # Make sure we don't close the session multiple times
        # Can happen in evaluation
        if self._runtime_closed:
            return
        self._runtime_closed = True
        self.session.close()
