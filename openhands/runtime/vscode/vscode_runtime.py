import asyncio
import uuid

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
    BrowserOutputObservation,
    CmdOutputObservation,
    ErrorObservation,
    FileEditObservation,
    FileReadObservation,
    FileWriteObservation,
    MCPObservation,
    Observation,
)
from openhands.events.stream import EventStream
from openhands.runtime.base import Runtime

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
        sio_server: socketio.AsyncServer,  # The main backend Socket.IO server
        socket_connection_id: str,  # The Socket.IO SID of the VS Code extension client
        logical_sid: str = 'default_logical_sid',  # Logical identifier for this runtime/conversation
    ):
        super().__init__(config=config, event_stream=event_stream)
        self.sio_server = sio_server
        self.socket_connection_id = socket_connection_id
        self.logical_sid = logical_sid  # Renamed from self.sid for clarity
        self._running_actions: dict[str, asyncio.Future[Observation]] = {}
        logger.info(
            f'VsCodeRuntime initialized for logical_sid: {self.logical_sid}, '
            f'socket_connection_id: {self.socket_connection_id}'
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

        oh_event_payload = {
            'event_id': event_id,
            'action': action.__class__.__name__,
            'args': action.__dict__,
            'message': getattr(
                action, 'message', f'Delegating {type(action).__name__} to VSCode'
            ),
            'source': 'agent',
        }

        if hasattr(action, 'thought') and action.thought:
            # Ensure args is a dict before adding thought
            if not isinstance(oh_event_payload.get('args'), dict):
                oh_event_payload['args'] = {}
            # Type assertion since we just ensured it's a dict
            args_dict = oh_event_payload['args']
            assert isinstance(args_dict, dict)
            args_dict['thought'] = action.thought

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
            obs_type = observation_event.get('observation')
            obs_content = observation_event.get('content', '')
            obs_extras = observation_event.get('extras', {})

            observation: Observation
            if obs_type == 'run':
                observation = CmdOutputObservation(
                    command_id=-1,
                    command=obs_extras.get('command', ''),
                    exit_code=obs_extras.get('exit_code', -1),
                    content=obs_content,
                )
            elif obs_type == 'read':
                observation = FileReadObservation(
                    path=obs_extras.get('path', ''), content=obs_content
                )
            elif obs_type == 'write':
                observation = FileWriteObservation(
                    path=obs_extras.get('path', ''), content=obs_content
                )
            elif obs_type == 'edit':
                observation = FileEditObservation(
                    path=obs_extras.get('path', ''), content=obs_content
                )
            elif obs_type == 'browse':
                observation = BrowserOutputObservation(
                    url=obs_extras.get('url', ''),
                    trigger_by_action=obs_extras.get('trigger_by_action', ''),
                    content=obs_content,
                    screenshot=obs_extras.get('screenshot', ''),
                )
            elif obs_type == 'ipython':
                # Import here to avoid circular imports
                from openhands.events.observation import IPythonRunCellObservation

                observation = IPythonRunCellObservation(
                    content=obs_content,
                    code=obs_extras.get('code', ''),
                )
            elif obs_type == 'mcp':
                observation = MCPObservation(
                    content=obs_content,
                    name=obs_extras.get('name', ''),
                    arguments=obs_extras.get('arguments', {}),
                )
            else:
                logger.warning(
                    f"Received unknown observation type '{obs_type}' from VSCode for cause {cause_event_id}"
                )
                observation = ErrorObservation(
                    content=f"Unknown observation type '{obs_type}' received from VSCode. Content: {obs_content}"
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

    async def close(self):
        logger.info('Closing VsCodeRuntime. Outstanding actions will be cancelled.')
        for event_id, future in self._running_actions.items():
            if not future.done():
                future.cancel()
                logger.info(f'Cancelled pending action: {event_id}')
        self._running_actions.clear()
        logger.info('VsCodeRuntime closed.')
