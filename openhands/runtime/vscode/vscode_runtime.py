import asyncio
import uuid
from pathlib import Path
from typing import Callable

import socketio  # Added for type hinting

from openhands.core.config import OpenHandsConfig
from openhands.core.logger import openhands_logger as logger
from openhands.events.action import (
    Action,
    BrowseInteractiveAction,
    BrowseURLAction,
    CmdRunAction,
    FileEditAction,
    FileReadAction,
    FileWriteAction,
    IPythonRunCellAction,
    MCPAction,
)
from openhands.events.observation import (
    ErrorObservation,
    Observation,
)
from openhands.events.serialization import event_from_dict, event_to_dict
from openhands.events.stream import EventStream
from openhands.runtime.base import Runtime
from openhands.runtime.plugins import PluginRequirement

# GLOBAL_SOCKET_IO_CLIENT = None # Removed


class VsCodeRuntime(Runtime):
    """
    A runtime that delegates action execution to a VS Code extension.
    This class sends actions to the VS Code extension via the main Socket.IO server
    and receives observations in return.
    """

    def __init__(
        self,
        config: OpenHandsConfig,
        event_stream: EventStream,
        sid: str = 'default',
        plugins: list[PluginRequirement] | None = None,
        env_vars: dict[str, str] | None = None,
        status_callback: Callable[[str, str, str], None] | None = None,
        attach_to_existing: bool = False,
        headless_mode: bool = False,
        user_id: str | None = None,
        # VSCode-specific parameters (optional for testing)
        sio_server: socketio.AsyncServer | None = None,
        socket_connection_id: str | None = None,
    ):
        super().__init__(config=config, event_stream=event_stream)
        self.sid = sid
        self.plugins = plugins or []
        self.env_vars = env_vars or {}
        self.status_callback = status_callback
        self.attach_to_existing = attach_to_existing
        self.headless_mode = headless_mode
        self.user_id = user_id

        # VSCode-specific attributes
        self.sio_server = sio_server
        self.socket_connection_id = socket_connection_id
        self._running_actions: dict[str, asyncio.Future[Observation]] = {}

        logger.info(
            f'VsCodeRuntime initialized with sid={sid}, socket_connection_id={socket_connection_id}'
        )

    async def _send_action_to_vscode(self, action: Action) -> Observation:
        if self.sio_server is None or self.socket_connection_id is None:
            logger.error(
                'sio_server or socket_connection_id is not configured. Cannot send action to VS Code.'
            )
            return ErrorObservation(
                content='VsCodeRuntime is not properly configured with a connection. Cannot operate.'
            )

        event_id = str(uuid.uuid4())

        # Use proper serialization to create event payload for VSCode
        oh_event_payload = event_to_dict(action)
        oh_event_payload['event_id'] = event_id
        oh_event_payload['message'] = getattr(
            action, 'message', f'Delegating {type(action).__name__} to VSCode'
        )

        future: asyncio.Future[Observation] = asyncio.get_event_loop().create_future()
        self._running_actions[event_id] = future

        logger.info(
            f'Sending action to VSCode (event_id: {event_id}, socket_id: {self.socket_connection_id}): {type(action)}'
        )
        logger.debug(f'Action details: {oh_event_payload}')

        try:
            if not hasattr(self.sio_server, 'emit'):
                logger.error("Provided sio_server does not have an 'emit' method.")
                # Clean up future before returning
                self._running_actions.pop(event_id, None)
                future.cancel()  # Ensure future is not left pending
                return ErrorObservation(
                    content='sio_server is misconfigured for VsCodeRuntime.'
                )

            await self.sio_server.emit(
                'oh_event', oh_event_payload, to=self.socket_connection_id
            )
            logger.debug(
                f'Action emitted to socket_connection_id: {self.socket_connection_id}'
            )

        except Exception as e:
            logger.error(
                f'Error emitting action to VSCode (socket_id: {self.socket_connection_id}): {e}'
            )
            # Clean up future before returning
            self._running_actions.pop(event_id, None)
            if not future.done():  # Check if future is already resolved/cancelled
                future.set_exception(
                    e
                )  # Propagate exception to the future if not already done
            return ErrorObservation(
                content=f'Failed to send action to VS Code extension: {e}'
            )

        try:
            observation = await asyncio.wait_for(
                future, timeout=self.config.sandbox.timeout
            )
            logger.info(
                f'Received observation for event_id {event_id} from socket_id: {self.socket_connection_id}'
            )
            return observation
        except asyncio.TimeoutError:
            logger.error(
                f'Timeout waiting for observation for event_id {event_id} from socket_id: {self.socket_connection_id}'
            )
            # The future is automatically cancelled by wait_for on timeout.
            # We just need to ensure it's removed from _running_actions, which finally does.
            return ErrorObservation(
                content=f'Timeout waiting for VS Code extension response for action: {type(action)}'
            )
        except asyncio.CancelledError:
            logger.info(f'Action {event_id} was cancelled while awaiting observation.')
            return ErrorObservation(content=f'Action {type(action)} was cancelled.')
        finally:
            self._running_actions.pop(event_id, None)

    def handle_observation_from_vscode(self, observation_event: dict):
        cause_event_id = observation_event.get('cause')
        if not cause_event_id:
            logger.error(
                f"Received observation event from VSCode without a 'cause' ID: {observation_event}"
            )
            return

        if cause_event_id in self._running_actions:
            future = self._running_actions[cause_event_id]

            try:
                # Use proper deserialization to convert observation event back to Observation object
                observation = event_from_dict(observation_event)
                assert isinstance(observation, Observation)
            except Exception as e:
                logger.error(
                    f'Failed to deserialize observation from VSCode for cause {cause_event_id}: {e}'
                )
                observation = ErrorObservation(
                    content=f'Failed to deserialize observation from VSCode: {e}. Raw event: {observation_event}'
                )

            if not future.done():
                future.set_result(observation)
            else:
                logger.warning(
                    f'Future for event_id {cause_event_id} was already done.'
                )
        else:
            logger.warning(
                f'Received observation for unknown event_id or already handled: {cause_event_id}'
            )

    def _run_async_action(self, action) -> Observation:
        """Helper to run async action in sync context."""
        try:
            # Try to get the current event loop
            asyncio.get_running_loop()
            # If we're already in an async context, we need to use a different approach
            # Create a new task and run it
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run, self._send_action_to_vscode(action)
                )
                return future.result()
        except RuntimeError:
            # No event loop running, safe to use asyncio.run
            return asyncio.run(self._send_action_to_vscode(action))

    def run(self, action: CmdRunAction) -> Observation:
        """Execute a shell command via VSCode."""
        return self._run_async_action(action)

    def read(self, action: FileReadAction) -> Observation:
        """Read a file via VSCode."""
        return self._run_async_action(action)

    def write(self, action: FileWriteAction) -> Observation:
        """Write to a file via VSCode."""
        return self._run_async_action(action)

    def edit(self, action: FileEditAction) -> Observation:
        """Edit a file via VSCode."""
        return self._run_async_action(action)

    def browse(self, action: BrowseURLAction) -> Observation:
        """Browse a URL via VSCode."""
        return self._run_async_action(action)

    def browse_interactive(self, action: BrowseInteractiveAction) -> Observation:
        """Browse interactively via VSCode."""
        return self._run_async_action(action)

    def run_ipython(self, action: IPythonRunCellAction) -> Observation:
        """Execute Python code via VSCode."""
        return self._run_async_action(action)

    async def call_tool_mcp(self, action: MCPAction) -> Observation:
        """Call MCP tool via VSCode."""
        return await self._send_action_to_vscode(action)

    async def connect(self):
        """Connect to VSCode extension via Socket.IO.

        This method is called during runtime initialization.
        The actual Socket.IO connection should be established by the VSCode extension.
        """
        logger.info('VSCode Runtime ready for connection from VSCode extension')
        # The Socket.IO server is started in __init__, so we're ready for connections

    def copy_from(self, path: str) -> Path:
        """Copy files from the VSCode workspace to the host.

        For VSCode runtime, file operations are handled through the extension,
        so files are already accessible on the host. Return the path as-is.
        """
        logger.debug(f'VSCode Runtime: copy_from {path} (no-op)')
        return Path(path)

    def copy_to(self, host_src: str, sandbox_dest: str, recursive: bool = False):
        """Copy files from the host to the VSCode workspace.

        For VSCode runtime, file operations are handled through the extension,
        so this is a no-op as files are already accessible on the host.
        """
        logger.debug(
            f'VSCode Runtime: copy_to {host_src} -> {sandbox_dest} (no-op, recursive={recursive})'
        )

    def get_mcp_config(self, extra_stdio_servers: list | None = None):
        """Get MCP configuration for this runtime.

        Returns the MCP configuration from the runtime config.
        """
        return self.config.mcp

    def list_files(self, path: str | None = None) -> list[str]:
        """List files in the given path.

        For VSCode runtime, we delegate file listing to the extension.
        This is a synchronous wrapper around the async file listing operation.
        """
        # For now, return empty list as file operations should go through VSCode extension
        logger.debug(f'VSCode Runtime: list_files {path} (delegated to extension)')
        return []

    async def close(self):
        logger.info('Closing VsCodeRuntime. Outstanding actions will be cancelled.')
        for event_id, future in self._running_actions.items():
            if not future.done():
                future.cancel()
                logger.info(f'Cancelled pending action: {event_id}')
        self._running_actions.clear()
        logger.info('VsCodeRuntime closed.')
