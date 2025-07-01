"""This runtime runs the action_execution_server directly on the local machine without Docker."""

import os
import shutil
import subprocess
import sys
import tempfile
import threading
from dataclasses import dataclass
from typing import Callable
from urllib.parse import urlparse

import httpx
import tenacity

import openhands
from openhands.core.config import OpenHandsConfig
from openhands.core.exceptions import AgentRuntimeDisconnectedError
from openhands.core.logger import openhands_logger as logger
from openhands.events import EventStream
from openhands.events.action import (
    Action,
)
from openhands.events.observation import (
    Observation,
)
from openhands.events.serialization import event_to_dict, observation_from_dict
from openhands.integrations.provider import PROVIDER_TOKEN_TYPE
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
from openhands.runtime.runtime_status import RuntimeStatus
from openhands.runtime.utils import find_available_tcp_port
from openhands.runtime.utils.command import get_action_execution_server_startup_command
from openhands.utils.async_utils import call_sync_from_async
from openhands.utils.tenacity_stop import stop_if_should_exit


@dataclass
class ActionExecutionServerInfo:
    """Information about a running server process."""

    process: subprocess.Popen
    execution_server_port: int
    vscode_port: int
    app_ports: list[int]
    log_thread: threading.Thread
    log_thread_exit_event: threading.Event
    temp_workspace: str | None
    workspace_mount_path: str


# Global dictionary to track running server processes by session ID
_RUNNING_SERVERS: dict[str, ActionExecutionServerInfo] = {}


def get_user_info() -> tuple[int, str | None]:
    """Get user ID and username in a cross-platform way."""
    username = os.getenv('USER')
    if sys.platform == 'win32':
        # On Windows, we don't use user IDs the same way
        # Return a default value that won't cause issues
        return 1000, username
    else:
        # On Unix systems, use os.getuid()
        return os.getuid(), username


def check_dependencies(code_repo_path: str, poetry_venvs_path: str) -> None:
    ERROR_MESSAGE = 'Please follow the instructions in https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md to install OpenHands.'
    if not os.path.exists(code_repo_path):
        raise ValueError(
            f'Code repo path {code_repo_path} does not exist. ' + ERROR_MESSAGE
        )
    if not os.path.exists(poetry_venvs_path):
        raise ValueError(
            f'Poetry venvs path {poetry_venvs_path} does not exist. ' + ERROR_MESSAGE
        )
    # Check jupyter is installed
    logger.debug('Checking dependencies: Jupyter')
    output = subprocess.check_output(
        'poetry run jupyter --version',
        shell=True,
        text=True,
        cwd=code_repo_path,
    )
    logger.debug(f'Jupyter output: {output}')
    if 'jupyter' not in output.lower():
        raise ValueError('Jupyter is not properly installed. ' + ERROR_MESSAGE)

    # Check libtmux is installed (skip on Windows)

    if sys.platform != 'win32':
        logger.debug('Checking dependencies: libtmux')
        import libtmux

        server = libtmux.Server()
        try:
            session = server.new_session(session_name='test-session')
        except Exception:
            raise ValueError('tmux is not properly installed or available on the path.')
        pane = session.attached_pane
        pane.send_keys('echo "test"')
        pane_output = '\n'.join(pane.cmd('capture-pane', '-p').stdout)
        session.kill_session()
        if 'test' not in pane_output:
            raise ValueError('libtmux is not properly installed. ' + ERROR_MESSAGE)

    # Skip browser environment check on Windows
    if sys.platform != 'win32':
        logger.debug('Checking dependencies: browser')
        from openhands.runtime.browser.browser_env import BrowserEnv

        browser = BrowserEnv()
        browser.close()
    else:
        logger.warning('Running on Windows - browser environment check skipped.')


class LocalRuntime(ActionExecutionClient):
    """This runtime will run the action_execution_server directly on the local machine.
    When receiving an event, it will send the event to the server via HTTP.

    Args:
        config (OpenHandsConfig): The application configuration.
        event_stream (EventStream): The event stream to subscribe to.
        sid (str, optional): The session ID. Defaults to 'default'.
        plugins (list[PluginRequirement] | None, optional): list of plugin requirements. Defaults to None.
        env_vars (dict[str, str] | None, optional): Environment variables to set. Defaults to None.
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
        headless_mode: bool = True,
        user_id: str | None = None,
        git_provider_tokens: PROVIDER_TOKEN_TYPE | None = None,
    ) -> None:
        self.is_windows = sys.platform == 'win32'
        if self.is_windows:
            logger.warning(
                'Running on Windows - some features that require tmux will be limited. '
                'For full functionality, please consider using WSL or Docker runtime.'
            )

        self.config = config
        self._user_id, self._username = get_user_info()

        logger.warning(
            'Initializing LocalRuntime. WARNING: NO SANDBOX IS USED. '
            'This is an experimental feature, please report issues to https://github.com/All-Hands-AI/OpenHands/issues. '
            '`run_as_openhands` will be ignored since the current user will be used to launch the server. '
            'We highly recommend using a sandbox (eg. DockerRuntime) unless you '
            'are running in a controlled environment.\n'
            f'User ID: {self._user_id}. '
            f'Username: {self._username}.'
        )

        # Initialize these values to be set in connect()
        self._temp_workspace: str | None = None
        self._execution_server_port = -1
        self._vscode_port = -1
        self._app_ports: list[int] = []

        self.api_url = (
            f'{self.config.sandbox.local_runtime_url}:{self._execution_server_port}'
        )
        self.status_callback = status_callback
        self.server_process: subprocess.Popen[str] | None = None
        self.action_semaphore = threading.Semaphore(1)  # Ensure one action at a time
        self._log_thread_exit_event = threading.Event()  # Add exit event

        # Update env vars
        if self.config.sandbox.runtime_startup_env_vars:
            os.environ.update(self.config.sandbox.runtime_startup_env_vars)

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
            user_id,
            git_provider_tokens,
        )

        # If there is an API key in the environment we use this in requests to the runtime
        session_api_key = os.getenv('SESSION_API_KEY')
        if session_api_key:
            self.session.headers['X-Session-API-Key'] = session_api_key

    @property
    def action_execution_server_url(self) -> str:
        return self.api_url

    async def connect(self) -> None:
        """Start the action_execution_server on the local machine or connect to an existing one."""
        self.set_runtime_status(RuntimeStatus.STARTING_RUNTIME)

        # Check if there's already a server running for this session ID
        if self.sid in _RUNNING_SERVERS:
            self.log('info', f'Connecting to existing server for session {self.sid}')
            server_info = _RUNNING_SERVERS[self.sid]
            self.server_process = server_info.process
            self._execution_server_port = server_info.execution_server_port
            self._log_thread = server_info.log_thread
            self._log_thread_exit_event = server_info.log_thread_exit_event
            self._vscode_port = server_info.vscode_port
            self._app_ports = server_info.app_ports
            self._temp_workspace = server_info.temp_workspace
            self.config.workspace_mount_path_in_sandbox = (
                server_info.workspace_mount_path
            )
            self.api_url = (
                f'{self.config.sandbox.local_runtime_url}:{self._execution_server_port}'
            )
        elif self.attach_to_existing:
            # If we're supposed to attach to an existing server but none exists, raise an error
            self.log('error', f'No existing server found for session {self.sid}')
            raise AgentRuntimeDisconnectedError(
                f'No existing server found for session {self.sid}'
            )
        else:
            # Set up workspace directory
            if self.config.workspace_base is not None:
                logger.warning(
                    f'Workspace base path is set to {self.config.workspace_base}. '
                    'It will be used as the path for the agent to run in. '
                    'Be careful, the agent can EDIT files in this directory!'
                )
                self.config.workspace_mount_path_in_sandbox = self.config.workspace_base
                self._temp_workspace = None
            else:
                # A temporary directory is created for the agent to run in
                logger.warning(
                    'Workspace base path is NOT set. Agent will run in a temporary directory.'
                )
                self._temp_workspace = tempfile.mkdtemp(
                    prefix=f'openhands_workspace_{self.sid}',
                )
                self.config.workspace_mount_path_in_sandbox = self._temp_workspace

            logger.info(
                f'Using workspace directory: {self.config.workspace_mount_path_in_sandbox}'
            )

            # Start a new server
            self._execution_server_port = self._find_available_port(
                EXECUTION_SERVER_PORT_RANGE
            )
            self._vscode_port = int(
                os.getenv('VSCODE_PORT')
                or str(self._find_available_port(VSCODE_PORT_RANGE))
            )
            self._app_ports = [
                int(
                    os.getenv('APP_PORT_1')
                    or str(self._find_available_port(APP_PORT_RANGE_1))
                ),
                int(
                    os.getenv('APP_PORT_2')
                    or str(self._find_available_port(APP_PORT_RANGE_2))
                ),
            ]
            self.api_url = (
                f'{self.config.sandbox.local_runtime_url}:{self._execution_server_port}'
            )

            # Start the server process
            cmd = get_action_execution_server_startup_command(
                server_port=self._execution_server_port,
                plugins=self.plugins,
                app_config=self.config,
                python_prefix=['poetry', 'run'],
                override_user_id=self._user_id,
                override_username=self._username,
            )

            self.log('debug', f'Starting server with command: {cmd}')
            env = os.environ.copy()
            # Get the code repo path
            code_repo_path = os.path.dirname(os.path.dirname(openhands.__file__))
            env['PYTHONPATH'] = os.pathsep.join(
                [code_repo_path, env.get('PYTHONPATH', '')]
            )
            env['OPENHANDS_REPO_PATH'] = code_repo_path
            env['LOCAL_RUNTIME_MODE'] = '1'
            env['VSCODE_PORT'] = str(self._vscode_port)

            # Derive environment paths using sys.executable
            interpreter_path = sys.executable
            python_bin_path = os.path.dirname(interpreter_path)
            env_root_path = os.path.dirname(python_bin_path)

            # Prepend the interpreter's bin directory to PATH for subprocesses
            env['PATH'] = f'{python_bin_path}{os.pathsep}{env.get("PATH", "")}'
            logger.debug(f'Updated PATH for subprocesses: {env["PATH"]}')

            # Check dependencies using the derived env_root_path if not skipped
            if os.getenv('SKIP_DEPENDENCY_CHECK', '') != '1':
                check_dependencies(code_repo_path, env_root_path)

            self.server_process = subprocess.Popen(  # noqa: S603
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1,
                env=env,
                cwd=code_repo_path,  # Explicitly set the working directory
            )

            # Start a thread to read and log server output
            def log_output() -> None:
                if not self.server_process or not self.server_process.stdout:
                    self.log(
                        'error', 'Server process or stdout not available for logging.'
                    )
                    return

                try:
                    # Read lines while the process is running and stdout is available
                    while self.server_process.poll() is None:
                        if self._log_thread_exit_event.is_set():  # Check exit event
                            self.log('info', 'Log thread received exit signal.')
                            break  # Exit loop if signaled
                        line = self.server_process.stdout.readline()
                        if not line:
                            # Process might have exited between poll() and readline()
                            break
                        self.log('info', f'Server: {line.strip()}')

                    # Capture any remaining output after the process exits OR if signaled
                    if (
                        not self._log_thread_exit_event.is_set()
                    ):  # Check again before reading remaining
                        self.log(
                            'info', 'Server process exited, reading remaining output.'
                        )
                        for line in self.server_process.stdout:
                            if (
                                self._log_thread_exit_event.is_set()
                            ):  # Check inside loop too
                                self.log(
                                    'info',
                                    'Log thread received exit signal while reading remaining output.',
                                )
                                break
                            self.log('info', f'Server (remaining): {line.strip()}')

                except Exception as e:
                    # Log the error, but don't prevent the thread from potentially exiting
                    self.log('error', f'Error reading server output: {e}')
                finally:
                    self.log(
                        'info', 'Log output thread finished.'
                    )  # Add log for thread exit

            self._log_thread = threading.Thread(target=log_output, daemon=True)
            self._log_thread.start()

            # Store the server process in the global dictionary
            _RUNNING_SERVERS[self.sid] = ActionExecutionServerInfo(
                process=self.server_process,
                execution_server_port=self._execution_server_port,
                vscode_port=self._vscode_port,
                app_ports=self._app_ports,
                log_thread=self._log_thread,
                log_thread_exit_event=self._log_thread_exit_event,
                temp_workspace=self._temp_workspace,
                workspace_mount_path=self.config.workspace_mount_path_in_sandbox,
            )

        self.log('info', f'Waiting for server to become ready at {self.api_url}...')
        self.set_runtime_status(RuntimeStatus.STARTING_RUNTIME)

        await call_sync_from_async(self._wait_until_alive)

        if not self.attach_to_existing:
            await call_sync_from_async(self.setup_initial_env)

        self.log(
            'debug',
            f'Server initialized with plugins: {[plugin.name for plugin in self.plugins]}',
        )
        if not self.attach_to_existing:
            self.set_runtime_status(RuntimeStatus.READY)
        self._runtime_initialized = True

    def _find_available_port(
        self, port_range: tuple[int, int], max_attempts: int = 5
    ) -> int:
        port = port_range[1]
        for _ in range(max_attempts):
            port = find_available_tcp_port(port_range[0], port_range[1])
            return port
        return port

    @tenacity.retry(
        wait=tenacity.wait_fixed(2),
        stop=tenacity.stop_after_delay(120) | stop_if_should_exit(),
        before_sleep=lambda retry_state: logger.debug(
            f'Waiting for server to be ready... (attempt {retry_state.attempt_number})'
        ),
    )
    def _wait_until_alive(self) -> bool:
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
        if not self.runtime_initialized:
            raise AgentRuntimeDisconnectedError('Runtime not initialized')

        # Check if our server process is still valid
        if self.server_process is None:
            # Check if there's a server in the global dictionary
            if self.sid in _RUNNING_SERVERS:
                self.server_process = _RUNNING_SERVERS[self.sid].process
            else:
                raise AgentRuntimeDisconnectedError('Server process not found')

        # Check if the server process is still running
        if self.server_process.poll() is not None:
            # If the process died, remove it from the global dictionary
            if self.sid in _RUNNING_SERVERS:
                del _RUNNING_SERVERS[self.sid]
            raise AgentRuntimeDisconnectedError('Server process died')

        with self.action_semaphore:
            try:
                response = await call_sync_from_async(
                    lambda: self.session.post(
                        f'{self.api_url}/execute_action',
                        json={'action': event_to_dict(action)},
                    )
                )
                return observation_from_dict(response.json())
            except httpx.NetworkError:
                raise AgentRuntimeDisconnectedError('Server connection lost')

    def close(self) -> None:
        """Stop the server process if not in attach_to_existing mode."""
        # If we're in attach_to_existing mode, don't close the server
        if self.attach_to_existing:
            self.log(
                'info',
                f'Not closing server for session {self.sid} (attach_to_existing=True)',
            )
            # Just clean up our reference to the process, but leave it running
            self.server_process = None
            # Don't clean up temp workspace when attach_to_existing=True
            super().close()
            return

        # Signal the log thread to exit
        self._log_thread_exit_event.set()

        # Remove from global dictionary
        if self.sid in _RUNNING_SERVERS:
            del _RUNNING_SERVERS[self.sid]

        if self.server_process:
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.server_process.kill()
            self.server_process = None
            self._log_thread.join(timeout=5)  # Add timeout to join

        # Clean up temp workspace if it exists and we created it
        if self._temp_workspace and not self.attach_to_existing:
            shutil.rmtree(self._temp_workspace)
            self._temp_workspace = None

        super().close()

    @classmethod
    async def delete(cls, conversation_id: str) -> None:
        """Delete the runtime for a conversation."""
        if conversation_id in _RUNNING_SERVERS:
            logger.info(f'Deleting LocalRuntime for conversation {conversation_id}')
            server_info = _RUNNING_SERVERS[conversation_id]

            # Signal the log thread to exit
            server_info.log_thread_exit_event.set()

            # Terminate the server process
            if server_info.process:
                server_info.process.terminate()
                try:
                    server_info.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    server_info.process.kill()

            # Wait for the log thread to finish
            server_info.log_thread.join(timeout=5)

            # Remove from global dictionary
            del _RUNNING_SERVERS[conversation_id]
            logger.info(f'LocalRuntime for conversation {conversation_id} deleted')

    @property
    def runtime_url(self) -> str:
        runtime_url = os.getenv('RUNTIME_URL')
        if runtime_url:
            return runtime_url

        # TODO: This could be removed if we had a straightforward variable containing the RUNTIME_URL in the K8 env.
        runtime_url_pattern = os.getenv('RUNTIME_URL_PATTERN')
        hostname = os.getenv('HOSTNAME')
        if runtime_url_pattern and hostname:
            runtime_id = hostname.split('-')[1]
            runtime_url = runtime_url_pattern.format(runtime_id=runtime_id)
            return runtime_url

        # Fallback to localhost
        return self.config.sandbox.local_runtime_url

    @property
    def vscode_url(self) -> str | None:
        token = super().get_vscode_token()
        if not token:
            return None
        runtime_url = self.runtime_url
        if 'localhost' in runtime_url:
            vscode_url = f'{self.runtime_url}:{self._vscode_port}'
        else:
            # Similar to remote runtime...
            parsed_url = urlparse(runtime_url)
            vscode_url = f'{parsed_url.scheme}://vscode-{parsed_url.netloc}'
        return f'{vscode_url}/?tkn={token}&folder={self.config.workspace_mount_path_in_sandbox}'

    @property
    def web_hosts(self) -> dict[str, int]:
        hosts: dict[str, int] = {}
        for port in self._app_ports:
            hosts[f'{self.runtime_url}:{port}'] = port
        return hosts
