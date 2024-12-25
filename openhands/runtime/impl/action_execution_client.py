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
from openhands.events.action import Action, FileEditAction
from openhands.events.observation import ErrorObservation, NullObservation, Observation
from openhands.events.serialization import event_to_dict, observation_from_dict
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

            try:
                with self._send_request(
                    "POST",
                    f"{self.api_url}/run",
                    json={"action": event_to_dict(action)},
                    timeout=action.timeout,
                ) as response:
                    observation_dict = response.json()
                    observation = observation_from_dict(observation_dict)
                    return observation
            except requests.exceptions.Timeout:
                return ErrorObservation(
                    f"Action timed out after {action.timeout} seconds: {action}"
                )
            except requests.exceptions.ConnectionError as e:
                raise AgentRuntimeDisconnectedError(
                    f"Lost connection to runtime client: {e}"
                ) from e
            except Exception as e:
                return ErrorObservation(f"Failed to run action: {e}")

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