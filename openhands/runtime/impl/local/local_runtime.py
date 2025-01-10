"""
This runtime runs the action_execution_server directly on the local machine without Docker.
"""

import os
import shutil
import subprocess
import tempfile
import threading
from typing import Callable, Optional

import requests
import tenacity

from openhands.core.config import AppConfig
from openhands.core.exceptions import AgentRuntimeDisconnectedError
from openhands.core.logger import openhands_logger as logger
from openhands.events import EventStream
from openhands.events.action import (
    Action,
)
from openhands.events.observation import (
    ErrorObservation,
    Observation,
)
from openhands.events.serialization import event_to_dict, observation_from_dict
from openhands.runtime.impl.action_execution.action_execution_client import (
    ActionExecutionClient,
)
from openhands.runtime.impl.docker.docker_runtime import (
    APP_PORT_RANGE_1,
    APP_PORT_RANGE_2,
    EXECUTION_SERVER_PORT_RANGE,
    VSCODE_PORT_RANGE,
)
from openhands.runtime.plugins import PluginRequirement
from openhands.runtime.utils import find_available_tcp_port
from openhands.runtime.utils.command import get_action_execution_server_startup_command
from openhands.utils.async_utils import call_sync_from_async
from openhands.utils.tenacity_stop import stop_if_should_exit


class LocalRuntime(ActionExecutionClient):
    """This runtime will run the action_execution_server directly on the local machine.
    When receiving an event, it will send the event to the server via HTTP.

    Args:
        config (AppConfig): The application configuration.
        event_stream (EventStream): The event stream to subscribe to.
        sid (str, optional): The session ID. Defaults to 'default'.
        plugins (list[PluginRequirement] | None, optional): List of plugin requirements. Defaults to None.
        env_vars (dict[str, str] | None, optional): Environment variables to set. Defaults to None.
    """

    def __init__(
        self,
        config: AppConfig,
        event_stream: EventStream,
        sid: str = 'default',
        plugins: list[PluginRequirement] | None = None,
        env_vars: dict[str, str] | None = None,
        status_callback: Callable | None = None,
        attach_to_existing: bool = False,
        headless_mode: bool = True,
    ):
        self.config = config
        self._user_id = os.getuid()
        self._username = os.getenv('USER')

        # A temporary directory is created for the agent to run in
        # This is used for the local runtime only
        self._temp_workspace = tempfile.mkdtemp(
            prefix=f'openhands_workspace_{sid}',
        )
        self.config.workspace_mount_path_in_sandbox = self._temp_workspace

        logger.warning(
            'Initializing LocalRuntime. WARNING: NO SANDBOX IS USED. '
            '`run_as_openhands` will be ignored since the current user will be used to launch the server. '
            'We highly recommend using a sandbox (eg. DockerRuntime) unless you '
            'are running in a controlled environment.\n'
            f'Temp workspace: {self._temp_workspace}. '
            f'User ID: {self._user_id}. '
            f'Username: {self._username}.'
        )

        if self.config.workspace_base is not None:
            logger.warning(
                f'Workspace base path is set to {self.config.workspace_base}. It will be used as the path for the agent to run in.'
            )
            self.config.workspace_mount_path_in_sandbox = self.config.workspace_base
        else:
            logger.warning(
                'Workspace base path is NOT set. Agent will run in a temporary directory.'
            )
            self._temp_workspace = tempfile.mkdtemp()
            self.config.workspace_mount_path_in_sandbox = self._temp_workspace

        self._host_port = -1
        self._vscode_port = -1
        self._app_ports: list[int] = []

        self.api_url = f'{self.config.sandbox.local_runtime_url}:{self._host_port}'
        self.session = requests.Session()
        self.status_callback = status_callback
        self.server_process: Optional[subprocess.Popen[str]] = None
        self.action_semaphore = threading.Semaphore(1)  # Ensure one action at a time

        # Initialize the action_execution_server
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

    def _get_action_execution_server_host(self):
        return self.api_url

    async def connect(self):
        """Start the action_execution_server on the local machine."""
        self.send_status_message('STATUS$STARTING_RUNTIME')

        self._host_port = self._find_available_port(EXECUTION_SERVER_PORT_RANGE)
        self._vscode_port = self._find_available_port(VSCODE_PORT_RANGE)
        self._app_ports = [
            self._find_available_port(APP_PORT_RANGE_1),
            self._find_available_port(APP_PORT_RANGE_2),
        ]
        self.api_url = f'{self.config.sandbox.local_runtime_url}:{self._host_port}'

        # Start the server process
        cmd = get_action_execution_server_startup_command(
            server_port=self._host_port,
            plugins=self.plugins,
            app_config=self.config,
            python_prefix=[],
            override_user_id=self._user_id,
            override_username=self._username,
        )

        self.log('debug', f'Starting server with command: {cmd}')
        self.server_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1,
        )

        # Start a thread to read and log server output
        def log_output():
            if self.server_process and self.server_process.stdout:
                while True:
                    line = self.server_process.stdout.readline()
                    if not line:
                        break
                    self.log('debug', f'Server: {line.strip()}')

        log_thread = threading.Thread(target=log_output, daemon=True)
        log_thread.start()

        self.log('info', f'Waiting for server to become ready at {self.api_url}...')
        self.send_status_message('STATUS$WAITING_FOR_CLIENT')

        await call_sync_from_async(self._wait_until_alive)

        if not self.attach_to_existing:
            await call_sync_from_async(self.setup_initial_env)

        self.log(
            'debug',
            f'Server initialized with plugins: {[plugin.name for plugin in self.plugins]}',
        )
        if not self.attach_to_existing:
            self.send_status_message(' ')
        self._runtime_initialized = True

    def _find_available_port(self, port_range, max_attempts=5):
        port = port_range[1]
        for _ in range(max_attempts):
            port = find_available_tcp_port(port_range[0], port_range[1])
            return port
        return port

    @tenacity.retry(
        wait=tenacity.wait_exponential(multiplier=0.1, min=0.1, max=1),
        stop=stop_if_should_exit(),
        before_sleep=lambda retry_state: logger.debug(
            f'Waiting for server to be ready... (attempt {retry_state.attempt_number})'
        ),
    )
    def _wait_until_alive(self):
        """Wait until the server is ready to accept requests."""
        if self.server_process and self.server_process.poll() is not None:
            raise RuntimeError('Server process died')

        try:
            response = self.session.get(f'{self.api_url}/alive')
            response.raise_for_status()
            return True
        except Exception as e:
            self.log('debug', f'Server not ready yet: {e}')
            raise

    async def execute_action(self, action: Action) -> Observation:
        """Execute an action by sending it to the server."""
        if not self._runtime_initialized:
            return ErrorObservation('Runtime not initialized')

        if self.server_process is None or self.server_process.poll() is not None:
            return ErrorObservation('Server process died')

        with self.action_semaphore:
            try:
                response = await call_sync_from_async(
                    lambda: self.session.post(
                        f'{self.api_url}/execute_action',
                        json={'action': event_to_dict(action)},
                    )
                )
                return observation_from_dict(response.json())
            except requests.exceptions.ConnectionError:
                raise AgentRuntimeDisconnectedError('Server connection lost')
            except requests.exceptions.RequestException as e:
                return ErrorObservation(f'Failed to execute action: {e}')

    def close(self):
        """Stop the server process."""
        if self.server_process:
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.server_process.kill()
            self.server_process = None

        if self._temp_workspace:
            shutil.rmtree(self._temp_workspace)

        super().close()

        # Cleanup the temp workspace
        if self._temp_workspace:
            shutil.rmtree(self._temp_workspace)

    @property
    def vscode_url(self) -> str | None:
        token = super().get_vscode_token()
        if not token:
            return None
        vscode_url = f'http://localhost:{self._vscode_port}/?tkn={token}&folder={self.config.workspace_mount_path_in_sandbox}'
        return vscode_url

    @property
    def web_hosts(self):
        hosts: dict[str, int] = {}
        for port in self._app_ports:
            hosts[f'http://localhost:{port}'] = port
        return hosts
