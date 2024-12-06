import atexit
import os
import tempfile
import threading
from functools import lru_cache
from pathlib import Path
from typing import Callable
from zipfile import ZipFile

import docker
import requests
import tenacity

from openhands.core.config import AppConfig
from openhands.core.logger import DEBUG
from openhands.core.logger import openhands_logger as logger
from openhands.events import EventStream
from openhands.events.action import (
    ActionConfirmationStatus,
    BrowseInteractiveAction,
    BrowseURLAction,
    CmdRunAction,
    FileEditAction,
    FileReadAction,
    FileWriteAction,
    IPythonRunCellAction,
)
from openhands.events.action.action import Action
from openhands.events.observation import (
    ErrorObservation,
    NullObservation,
    Observation,
    UserRejectObservation,
)
from openhands.events.serialization import event_to_dict, observation_from_dict
from openhands.events.serialization.action import ACTION_TYPE_TO_CLASS
from openhands.runtime.base import (
    Runtime,
    RuntimeDisconnectedError,
    RuntimeNotFoundError,
)
from openhands.runtime.builder import DockerRuntimeBuilder
from openhands.runtime.impl.eventstream.containers import remove_all_containers
from openhands.runtime.plugins import PluginRequirement
from openhands.runtime.utils import find_available_tcp_port
from openhands.runtime.utils.request import send_request
from openhands.runtime.utils.runtime_build import build_runtime_image
from openhands.utils.async_utils import call_sync_from_async
from openhands.utils.tenacity_stop import stop_if_should_exit

CONTAINER_NAME_PREFIX = 'openhands-runtime-'


def remove_all_runtime_containers():
    remove_all_containers(CONTAINER_NAME_PREFIX)


atexit.register(remove_all_runtime_containers)


class LogBuffer:
    """Synchronous buffer for Docker container logs.

    This class provides a thread-safe way to collect, store, and retrieve logs
    from a Docker container. It uses a list to store log lines and provides methods
    for appending, retrieving, and clearing logs.
    """

    def __init__(self, container: docker.models.containers.Container, logFn: Callable):
        self.init_msg = 'Runtime client initialized.'

        self.buffer: list[str] = []
        self.lock = threading.Lock()
        self._stop_event = threading.Event()
        self.log_generator = container.logs(stream=True, follow=True)
        self.log_stream_thread = threading.Thread(target=self.stream_logs)
        self.log_stream_thread.daemon = True
        self.log_stream_thread.start()
        self.log = logFn

    def append(self, log_line: str):
        with self.lock:
            self.buffer.append(log_line)

    def get_and_clear(self) -> list[str]:
        with self.lock:
            logs = list(self.buffer)
            self.buffer.clear()
            return logs

    def stream_logs(self):
        """Stream logs from the Docker container in a separate thread.

        This method runs in its own thread to handle the blocking
        operation of reading log lines from the Docker SDK's synchronous generator.
        """
        try:
            for log_line in self.log_generator:
                if self._stop_event.is_set():
                    break
                if log_line:
                    decoded_line = log_line.decode('utf-8').rstrip()
                    self.append(decoded_line)
        except Exception as e:
            self.log('error', f'Error streaming docker logs: {e}')

    def __del__(self):
        if self.log_stream_thread.is_alive():
            self.log(
                'warn',
                "LogBuffer was not properly closed. Use 'log_buffer.close()' for clean shutdown.",
            )
            self.close(timeout=5)

    def close(self, timeout: float = 5.0):
        self._stop_event.set()
        self.log_stream_thread.join(timeout)
        # Close the log generator to release the file descriptor
        if hasattr(self.log_generator, 'close'):
            self.log_generator.close()


class EventStreamRuntime(Runtime):
    """This runtime will subscribe the event stream.
    When receive an event, it will send the event to runtime-client which run inside the docker environment.

    Args:
        config (AppConfig): The application configuration.
        event_stream (EventStream): The event stream to subscribe to.
        sid (str, optional): The session ID. Defaults to 'default'.
        plugins (list[PluginRequirement] | None, optional): List of plugin requirements. Defaults to None.
        env_vars (dict[str, str] | None, optional): Environment variables to set. Defaults to None.
    """

    # Need to provide this method to allow inheritors to init the Runtime
    # without initting the EventStreamRuntime.
    def init_base_runtime(
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
        self._host_port = 30000  # initial dummy value
        self._container_port = 30001  # initial dummy value
        self._vscode_url: str | None = None  # initial dummy value
        self._runtime_initialized: bool = False
        self.api_url = f'{self.config.sandbox.local_runtime_url}:{self._container_port}'
        self.session = requests.Session()
        self.status_callback = status_callback

        self.docker_client: docker.DockerClient = self._init_docker_client()
        self.base_container_image = self.config.sandbox.base_container_image
        self.runtime_container_image = self.config.sandbox.runtime_container_image
        self.container_name = CONTAINER_NAME_PREFIX + sid
        self.container = None
        self.action_semaphore = threading.Semaphore(1)  # Ensure one action at a time

        self.runtime_builder = DockerRuntimeBuilder(self.docker_client)

        # Buffer for container logs
        self.log_buffer: LogBuffer | None = None

        self.init_base_runtime(
            config,
            event_stream,
            sid,
            plugins,
            env_vars,
            status_callback,
            attach_to_existing,
            headless_mode,
        )

        # Log runtime_extra_deps after base class initialization so self.sid is available
        if self.config.sandbox.runtime_extra_deps:
            self.log(
                'debug',
                f'Installing extra user-provided dependencies in the runtime image: {self.config.sandbox.runtime_extra_deps}',
            )

    async def connect(self):
        self.send_status_message('STATUS$STARTING_RUNTIME')
        try:
            await call_sync_from_async(self._attach_to_container)
        except docker.errors.NotFound as e:
            if self.attach_to_existing:
                self.log(
                    'error',
                    f'Container {self.container_name} not found.',
                )
                raise e
            if self.runtime_container_image is None:
                if self.base_container_image is None:
                    raise ValueError(
                        'Neither runtime container image nor base container image is set'
                    )
                self.send_status_message('STATUS$STARTING_CONTAINER')
                self.runtime_container_image = build_runtime_image(
                    self.base_container_image,
                    self.runtime_builder,
                    platform=self.config.sandbox.platform,
                    extra_deps=self.config.sandbox.runtime_extra_deps,
                    force_rebuild=self.config.sandbox.force_rebuild_runtime,
                )

            self.log(
                'info', f'Starting runtime with image: {self.runtime_container_image}'
            )
            await call_sync_from_async(self._init_container)
            self.log(
                'info',
                f'Container started: {self.container_name}. VSCode URL: {self.vscode_url}',
            )

        self.log_buffer = LogBuffer(self.container, self.log)

        if not self.attach_to_existing:
            self.log('info', f'Waiting for client to become ready at {self.api_url}...')
            self.send_status_message('STATUS$WAITING_FOR_CLIENT')

        await call_sync_from_async(self._wait_until_alive)

        if not self.attach_to_existing:
            self.log('info', 'Runtime is ready.')

        if not self.attach_to_existing:
            await call_sync_from_async(self.setup_initial_env)

        self.log(
            'debug',
            f'Container initialized with plugins: {[plugin.name for plugin in self.plugins]}. VSCode URL: {self.vscode_url}',
        )
        if not self.attach_to_existing:
            self.send_status_message(' ')
        self._runtime_initialized = True

    @staticmethod
    @lru_cache(maxsize=1)
    def _init_docker_client() -> docker.DockerClient:
        try:
            return docker.from_env()
        except Exception as ex:
            logger.error(
                'Launch docker client failed. Please make sure you have installed docker and started docker desktop/daemon.',
            )
            raise ex

    def _init_container(self):
        self.log('debug', 'Preparing to start container...')
        self.send_status_message('STATUS$PREPARING_CONTAINER')
        plugin_arg = ''
        if self.plugins is not None and len(self.plugins) > 0:
            plugin_arg = (
                f'--plugins {" ".join([plugin.name for plugin in self.plugins])} '
            )
        self._host_port = self._find_available_port()
        self._container_port = (
            self._host_port
        )  # in future this might differ from host port
        self.api_url = f'{self.config.sandbox.local_runtime_url}:{self._container_port}'

        use_host_network = self.config.sandbox.use_host_network
        network_mode: str | None = 'host' if use_host_network else None

        port_mapping: dict[str, list[dict[str, str]]] | None = (
            None
            if use_host_network
            else {f'{self._container_port}/tcp': [{'HostPort': str(self._host_port)}]}
        )

        if use_host_network:
            self.log(
                'warn',
                'Using host network mode. If you are using MacOS, please make sure you have the latest version of Docker Desktop and enabled host network feature: https://docs.docker.com/network/drivers/host/#docker-desktop',
            )

        # Combine environment variables
        environment = {
            'port': str(self._container_port),
            'PYTHONUNBUFFERED': 1,
        }
        if self.config.debug or DEBUG:
            environment['DEBUG'] = 'true'

        if self.vscode_enabled:
            # vscode is on port +1 from container port
            if isinstance(port_mapping, dict):
                port_mapping[f'{self._container_port + 1}/tcp'] = [
                    {'HostPort': str(self._host_port + 1)}
                ]

        self.log('debug', f'Workspace Base: {self.config.workspace_base}')
        if (
            self.config.workspace_mount_path is not None
            and self.config.workspace_mount_path_in_sandbox is not None
        ):
            # e.g. result would be: {"/home/user/openhands/workspace": {'bind': "/workspace", 'mode': 'rw'}}
            volumes = {
                self.config.workspace_mount_path: {
                    'bind': self.config.workspace_mount_path_in_sandbox,
                    'mode': 'rw',
                }
            }
            logger.debug(f'Mount dir: {self.config.workspace_mount_path}')
        else:
            logger.debug(
                'Mount dir is not set, will not mount the workspace directory to the container'
            )
            volumes = None
        self.log(
            'debug',
            f'Sandbox workspace: {self.config.workspace_mount_path_in_sandbox}',
        )

        if self.config.sandbox.browsergym_eval_env is not None:
            browsergym_arg = (
                f'--browsergym-eval-env {self.config.sandbox.browsergym_eval_env}'
            )
        else:
            browsergym_arg = ''

        try:
            self.container = self.docker_client.containers.run(
                self.runtime_container_image,
                command=(
                    f'/openhands/micromamba/bin/micromamba run -n openhands '
                    f'poetry run '
                    f'python -u -m openhands.runtime.action_execution_server {self._container_port} '
                    f'--working-dir "{self.config.workspace_mount_path_in_sandbox}" '
                    f'{plugin_arg}'
                    f'--username {"openhands" if self.config.run_as_openhands else "root"} '
                    f'--user-id {self.config.sandbox.user_id} '
                    f'{browsergym_arg}'
                ),
                network_mode=network_mode,
                ports=port_mapping,
                working_dir='/openhands/code/',  # do not change this!
                name=self.container_name,
                detach=True,
                environment=environment,
                volumes=volumes,
            )
            self.log('debug', f'Container started. Server url: {self.api_url}')
            self.send_status_message('STATUS$CONTAINER_STARTED')
        except docker.errors.APIError as e:
            if '409' in str(e):
                self.log(
                    'warning',
                    f'Container {self.container_name} already exists. Removing...',
                )
                remove_all_containers(self.container_name)
                return self._init_container()

            else:
                self.log(
                    'error',
                    f'Error: Instance {self.container_name} FAILED to start container!\n',
                )
        except Exception as e:
            self.log(
                'error',
                f'Error: Instance {self.container_name} FAILED to start container!\n',
            )
            self.log('error', str(e))
            self.close()
            raise e

    def _attach_to_container(self):
        self._container_port = 0
        self.container = self.docker_client.containers.get(self.container_name)
        for port in self.container.attrs['NetworkSettings']['Ports']:  # type: ignore
            self._container_port = int(port.split('/')[0])
            break
        self._host_port = self._container_port
        self.api_url = f'{self.config.sandbox.local_runtime_url}:{self._container_port}'
        self.log(
            'debug',
            f'attached to container: {self.container_name} {self._container_port} {self.api_url}',
        )

    def _refresh_logs(self):
        self.log('debug', 'Getting container logs...')

        assert (
            self.log_buffer is not None
        ), 'Log buffer is expected to be initialized when container is started'

        logs = self.log_buffer.get_and_clear()
        if logs:
            formatted_logs = '\n'.join([f'    |{log}' for log in logs])
            self.log(
                'debug',
                '\n'
                + '-' * 35
                + 'Container logs:'
                + '-' * 35
                + f'\n{formatted_logs}'
                + '\n'
                + '-' * 80,
            )

    @tenacity.retry(
        stop=tenacity.stop_after_delay(120) | stop_if_should_exit(),
        retry=tenacity.retry_if_exception_type(
            (ConnectionError, requests.exceptions.ConnectionError)
        ),
        reraise=True,
        wait=tenacity.wait_fixed(2),
    )
    def _wait_until_alive(self):
        try:
            container = self.docker_client.containers.get(self.container_name)
            if container.status == 'exited':
                raise RuntimeDisconnectedError(
                    f'Container {self.container_name} has exited.'
                )
        except docker.errors.NotFound:
            raise RuntimeNotFoundError(f'Container {self.container_name} not found.')

        self._refresh_logs()
        if not self.log_buffer:
            raise RuntimeError('Runtime client is not ready.')

        with send_request(
            self.session,
            'GET',
            f'{self.api_url}/alive',
            timeout=5,
        ):
            pass

    def close(self, rm_all_containers: bool | None = None):
        """Closes the EventStreamRuntime and associated objects

        Parameters:
        - rm_all_containers (bool): Whether to remove all containers with the 'openhands-sandbox-' prefix
        """
        if self.log_buffer:
            self.log_buffer.close()

        if self.session:
            self.session.close()

        if rm_all_containers is None:
            rm_all_containers = self.config.sandbox.rm_all_containers

        if self.config.sandbox.keep_runtime_alive or self.attach_to_existing:
            return
        close_prefix = (
            CONTAINER_NAME_PREFIX if rm_all_containers else self.container_name
        )
        remove_all_containers(close_prefix)

    def run_action(self, action: Action) -> Observation:
        if isinstance(action, FileEditAction):
            return self.edit(action)

        # set timeout to default if not set
        if action.timeout is None:
            action.timeout = self.config.sandbox.timeout

        with self.action_semaphore:
            if not action.runnable:
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

            self._refresh_logs()

            assert action.timeout is not None

            try:
                with send_request(
                    self.session,
                    'POST',
                    f'{self.api_url}/execute_action',
                    json={'action': event_to_dict(action)},
                    # wait a few more seconds to get the timeout error from client side
                    timeout=action.timeout + 5,
                ) as response:
                    output = response.json()
                    obs = observation_from_dict(output)
                    obs._cause = action.id  # type: ignore[attr-defined]
            except requests.Timeout:
                raise RuntimeError(
                    f'Runtime failed to return execute_action before the requested timeout of {action.timeout}s'
                )
            self._refresh_logs()
            return obs

    def run(self, action: CmdRunAction) -> Observation:
        return self.run_action(action)

    def run_ipython(self, action: IPythonRunCellAction) -> Observation:
        return self.run_action(action)

    def read(self, action: FileReadAction) -> Observation:
        return self.run_action(action)

    def write(self, action: FileWriteAction) -> Observation:
        return self.run_action(action)

    def browse(self, action: BrowseURLAction) -> Observation:
        return self.run_action(action)

    def browse_interactive(self, action: BrowseInteractiveAction) -> Observation:
        return self.run_action(action)

    # ====================================================================
    # Implement these methods (for file operations) in the subclass
    # ====================================================================

    def copy_to(
        self, host_src: str, sandbox_dest: str, recursive: bool = False
    ) -> None:
        if not os.path.exists(host_src):
            raise FileNotFoundError(f'Source file {host_src} does not exist')

        self._refresh_logs()
        try:
            if recursive:
                # For recursive copy, create a zip file
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
                # For single file copy
                upload_data = {'file': open(host_src, 'rb')}

            params = {'destination': sandbox_dest, 'recursive': str(recursive).lower()}

            with send_request(
                self.session,
                'POST',
                f'{self.api_url}/upload_file',
                files=upload_data,
                params=params,
                timeout=300,
            ):
                pass

        except requests.Timeout:
            raise TimeoutError('Copy operation timed out')
        except Exception as e:
            raise RuntimeError(f'Copy operation failed: {str(e)}')
        finally:
            if recursive:
                os.unlink(temp_zip_path)
            self.log(
                'debug', f'Copy completed: host:{host_src} -> runtime:{sandbox_dest}'
            )
            self._refresh_logs()

    def list_files(self, path: str | None = None) -> list[str]:
        """List files in the sandbox.

        If path is None, list files in the sandbox's initial working directory (e.g., /workspace).
        """
        self._refresh_logs()
        try:
            data = {}
            if path is not None:
                data['path'] = path

            with send_request(
                self.session,
                'POST',
                f'{self.api_url}/list_files',
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
        self._refresh_logs()
        try:
            params = {'path': path}
            with send_request(
                self.session,
                'GET',
                f'{self.api_url}/download_files',
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

    def _is_port_in_use_docker(self, port):
        containers = self.docker_client.containers.list()
        for container in containers:
            container_ports = container.ports
            if str(port) in str(container_ports):
                return True
        return False

    def _find_available_port(self, max_attempts=5):
        port = 39999
        for _ in range(max_attempts):
            port = find_available_tcp_port(30000, 39999)
            if not self._is_port_in_use_docker(port):
                return port
        # If no port is found after max_attempts, return the last tried port
        return port

    @property
    def vscode_url(self) -> str | None:
        if self.vscode_enabled and self._runtime_initialized:
            if (
                hasattr(self, '_vscode_url') and self._vscode_url is not None
            ):  # cached value
                return self._vscode_url

            with send_request(
                self.session,
                'GET',
                f'{self.api_url}/vscode/connection_token',
                timeout=10,
            ) as response:
                response_json = response.json()
                assert isinstance(response_json, dict)
                if response_json['token'] is None:
                    return None
                self._vscode_url = f'http://localhost:{self._host_port + 1}/?tkn={response_json["token"]}&folder={self.config.workspace_mount_path_in_sandbox}'
                self.log(
                    'debug',
                    f'VSCode URL: {self._vscode_url}',
                )
                return self._vscode_url
        else:
            return None
