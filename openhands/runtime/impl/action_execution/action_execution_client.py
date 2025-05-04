import os
import tempfile
import threading
from pathlib import Path
from typing import Any
from zipfile import ZipFile

import httpcore
import httpx
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from openhands.core.config import AppConfig
from openhands.core.config.mcp_config import MCPConfig, MCPSSEServerConfig
from openhands.core.exceptions import (
    AgentRuntimeTimeoutError,
)
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
from openhands.utils.http_session import HttpSession
from openhands.utils.tenacity_stop import stop_if_should_exit


def _is_retryable_error(exception):
    return isinstance(
        exception, (httpx.RemoteProtocolError, httpcore.RemoteProtocolError)
    )


class ActionExecutionClient(Runtime):
    """Base class for runtimes that interact with the action execution server.

    This class contains shared logic between DockerRuntime and RemoteRuntime
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
        user_id: str | None = None,
        git_provider_tokens: PROVIDER_TOKEN_TYPE | None = None,
    ):
        self.session = HttpSession()
        self.action_semaphore = threading.Semaphore(1)  # Ensure one action at a time
        self._runtime_initialized: bool = False
        self._runtime_closed: bool = False
        self._vscode_token: str | None = None  # initial dummy value
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

    @property
    def runtime_initialized(self) -> bool:
        return self._runtime_initialized

    @retry(
        retry=retry_if_exception(_is_retryable_error),
        stop=stop_after_attempt(5) | stop_if_should_exit(),
        wait=wait_exponential(multiplier=1, min=4, max=15),
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
        return send_request(self.session, method, url, **kwargs)

    def check_if_alive(self) -> None:
        response = self._send_action_server_request(
            'GET',
            f'{self.action_execution_server_url}/alive',
            timeout=5,
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
            if recursive:
                os.unlink(temp_zip_path)
            self.log(
                'debug', f'Copy completed: host:{host_src} -> runtime:{sandbox_dest}'
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

    def get_updated_mcp_config(self) -> MCPConfig:
        # Add the runtime as another MCP server
        updated_mcp_config = self.config.mcp.model_copy()
        # Send a request to the action execution server to updated MCP config
        stdio_tools = [
            server.model_dump(mode='json')
            for server in updated_mcp_config.stdio_servers
        ]
        self.log('debug', f'Updating MCP server to: {stdio_tools}')
        response = self._send_action_server_request(
            'POST',
            f'{self.action_execution_server_url}/update_mcp_server',
            json=stdio_tools,
            timeout=10,
        )
        if response.status_code != 200:
            raise RuntimeError(f'Failed to update MCP server: {response.text}')

        # No API key by default. Child runtime can override this when appropriate
        updated_mcp_config.sse_servers.append(
            MCPSSEServerConfig(
                url=self.action_execution_server_url.rstrip('/') + '/sse', api_key=None
            )
        )
        self.log(
            'debug',
            f'Updated MCP config by adding runtime as another server: {updated_mcp_config}',
        )
        return updated_mcp_config

    async def call_tool_mcp(self, action: MCPAction) -> Observation:
        # Import here to avoid circular imports
        from openhands.mcp.utils import call_tool_mcp as call_tool_mcp_handler
        from openhands.mcp.utils import create_mcp_clients

        # Get the updated MCP config
        updated_mcp_config = self.get_updated_mcp_config()
        self.log(
            'debug',
            f'Creating MCP clients with servers: {updated_mcp_config.sse_servers}',
        )

        # Create clients for this specific operation
        mcp_clients = await create_mcp_clients(updated_mcp_config.sse_servers)

        # Call the tool and return the result
        # No need for try/finally since disconnect() is now just resetting state
        result = await call_tool_mcp_handler(mcp_clients, action)

        # Reset client state (no active connections to worry about)
        for client in mcp_clients:
            await client.disconnect()

        return result

    def close(self) -> None:
        # Make sure we don't close the session multiple times
        # Can happen in evaluation
        if self._runtime_closed:
            return
        self._runtime_closed = True
        self.session.close()
