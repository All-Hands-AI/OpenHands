"""Base class for runtimes that interact with the action execution server."""

import threading
from typing import Any

import requests
import tenacity

from openhands.core.config import AppConfig
from openhands.core.exceptions import (
    AgentRuntimeDisconnectedError,
    AgentRuntimeError,
    AgentRuntimeNotFoundError,
    AgentRuntimeNotReadyError,
    AgentRuntimeTimeoutError,
)
from openhands.events import EventStream
from openhands.events.action import Action, ActionConfirmationStatus, FileEditAction
from openhands.events.observation import (
    ErrorObservation,
    NullObservation,
    Observation,
    UserRejectObservation,
)
from openhands.events.serialization import event_to_dict, observation_from_dict
from openhands.events.serialization.action import ACTION_TYPE_TO_CLASS
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
        sid: str = "default",
        plugins: list[PluginRequirement] | None = None,
        env_vars: dict[str, str] | None = None,
        status_callback: Any | None = None,
        attach_to_existing: bool = False,
        headless_mode: bool = True,
    ):
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
        self.session = requests.Session()
        self.action_semaphore = threading.Semaphore(1)  # Ensure one action at a time
        self._runtime_initialized: bool = False
        self.api_url: str | None = None

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
        if not self._runtime_initialized and not url.endswith("/alive"):
            raise AgentRuntimeNotReadyError("Runtime client is not ready.")

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

    def run_action(self, action: Action) -> Observation:
        """Run an action by sending it to the action execution server.
        
        Args:
            action: Action to execute
        
        Returns:
            Observation from executing the action
        """
        if isinstance(action, FileEditAction):
            return self.edit(action)

        # set timeout to default if not set
        if action.timeout is None:
            action.timeout = self.config.sandbox.timeout

        with self.action_semaphore:
            if not action.runnable:
                return NullObservation("")
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
                request_body = {'action': event_to_dict(action)}
                self.log('debug', f'Request body: {request_body}')
                url = f"{self.runtime_url}/execute_action" if hasattr(self, "runtime_url") else f"{self.api_url}/execute_action"
                with self._send_request(
                    'POST',
                    url,
                    json=request_body,
                    # wait a few more seconds to get the timeout error from client side
                    timeout=action.timeout + 5,
                ) as response:
                    output = response.json()
                    obs = observation_from_dict(output)
                    obs._cause = action.id  # type: ignore[attr-defined]
                    return obs
            except requests.Timeout:
                raise AgentRuntimeTimeoutError(
                    f'Runtime failed to return execute_action before the requested timeout of {action.timeout}s'
                )

    def _wait_until_alive(self):
        """Wait until the action execution server is alive and ready.
        
        Raises:
            AgentRuntimeNotReadyError: If the server does not become ready in time
            AgentRuntimeDisconnectedError: If the connection is lost
        """
        retry_decorator = tenacity.retry(
            stop=tenacity.stop_after_delay(120) | stop_if_should_exit(),
            retry=tenacity.retry_if_exception_type(
                (ConnectionError, requests.exceptions.ConnectionError)
            ),
            reraise=True,
            wait=tenacity.wait_fixed(2),
        )

        try:
            with retry_decorator(send_request)(
                self.session,
                "GET",
                f"{self.api_url}/alive",
                timeout=5,
            ):
                pass
        except requests.exceptions.ConnectionError as e:
            raise AgentRuntimeDisconnectedError(
                f"Lost connection to runtime client: {e}"
            ) from e