import os
import tempfile
import threading
from functools import lru_cache
from typing import Callable
from zipfile import ZipFile

import docker
import requests
import tenacity

from openhands.core.config import AppConfig
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
    FatalErrorObservation,
    NullObservation,
    Observation,
    UserRejectObservation,
)
from openhands.events.serialization import event_to_dict, observation_from_dict
from openhands.events.serialization.action import ACTION_TYPE_TO_CLASS
from openhands.runtime.base import Runtime
from openhands.runtime.plugins import PluginRequirement
from openhands.runtime.utils import find_available_tcp_port
from openhands.runtime.utils.request import send_request_with_retry
from openhands.utils.tenacity_stop import stop_if_should_exit


class LogBuffer:
    """Synchronous buffer for Docker container logs.

    This class provides a thread-safe way to collect, store, and retrieve logs
    from a Docker container. It uses a list to store log lines and provides methods
    for appending, retrieving, and clearing logs.
    """

    def __init__(self, container: docker.models.containers.Container):
        self.client_ready = False
        self.init_msg = 'Runtime client initialized.'

        self.buffer: list[str] = []
        self.lock = threading.Lock()
        self._stop_event = threading.Event()
        self.log_generator = container.logs(stream=True, follow=True)
        self.log_stream_thread = threading.Thread(target=self.stream_logs)
        self.log_stream_thread.daemon = True
        self.log_stream_thread.start()

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
                    if self.init_msg in decoded_line:
                        self.client_ready = True
        except Exception as e:
            logger.error(f'Error streaming docker logs: {e}')

    def __del__(self):
        if self.log_stream_thread.is_alive():
            logger.warn(
                "LogBuffer was not properly closed. Use 'log_buffer.close()' for clean shutdown."
            )
            self.close(timeout=5)

    def close(self, timeout: float = 5.0):
        self._stop_event.set()
        self.log_stream_thread.join(timeout)


class DockerRuntime(Runtime):
    """This runtime will subscribe the event stream.

    When receive an event, it will send the event to runtime-client which run inside the docker environment.

    Args:
        config (AppConfig): The application configuration.
        event_stream (EventStream): The event stream to subscribe to.
        sid (str, optional): The session ID. Defaults to 'default'.
        plugins (list[PluginRequirement] | None, optional): List of plugin requirements. Defaults to None.
        env_vars (dict[str, str] | None, optional): Environment variables to set. Defaults to None.
    """

    #
    def init_base_runtime(
        self,
        config: AppConfig,
        event_stream: EventStream,
        sid: str = 'default',
        plugins: list[PluginRequirement] | None = None,
        env_vars: dict[str, str] | None = None,
        status_message_callback: Callable | None = None,
        attach_to_existing: bool = False,
    ):
        super().__init__(
            config,
            event_stream,
            sid,
            plugins,
            env_vars,
            status_message_callback,
            attach_to_existing,
        )

    def __init__(
        self,
        config: AppConfig,
        event_stream: EventStream,
        sid: str = 'default',
        plugins: list[PluginRequirement] | None = None,
        env_vars: dict[str, str] | None = None,
        status_message_callback: Callable | None = None,
        attach_to_existing: bool = False,
    ):
        self.config = config

        # TODO: Just define one 'runtime_api_url'?
        self.api_url = (
            config.sandbox.remote_runtime_api_url or config.sandbox.local_runtime_url
        )
        self.session = requests.Session()
        self.status_message_callback = status_message_callback

        self.docker_client: docker.DockerClient = self._init_docker_client(
            config.sandbox.docker_url
        )
        self.container_name = self.config.sandbox.container_name
        self.container = None
        self.action_semaphore = threading.Semaphore(1)

        # Buffer for container logs
        self.log_buffer: LogBuffer | None = None

        self.init_base_runtime(
            config,
            event_stream,
            sid,
            plugins,
            env_vars,
            status_message_callback,
        )

    async def connect(self):
        self.send_status_message('STATUS$STARTING_RUNTIME')

        self._init_container()

        logger.info('Waiting for client to become ready...')
        self.send_status_message('STATUS$WAITING_FOR_CLIENT')
        self._wait_until_alive()

        logger.info(
            f'Container attached: {self.container_name}. Runtime client is ready.'
        )

        self.send_status_message(' ')

    @staticmethod
    @lru_cache(maxsize=1)
    def _init_docker_client(docker_url: str) -> docker.DockerClient:
        try:
            base_url = docker_url or os.environ.get('DOCKER_HOST')
            return docker.DockerClient(base_url)
        except Exception as ex:
            logger.error(
                'Launch docker client failed. Please make sure you have installed docker and started docker desktop/daemon.'
            )
            raise ex

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(5) | stop_if_should_exit(),
        wait=tenacity.wait_exponential(multiplier=1, min=4, max=60),
    )
    def _init_container(self):
        try:
            logger.info('Preparing to start container...')

            self.send_status_message('STATUS$PREPARING_CONTAINER')
            self.container = self.docker_client.containers.get(self.container_name)
            self.log_buffer = LogBuffer(self.container)

            logger.info(f'Container attached. {self.container_name}')

            self.send_status_message('STATUS$CONTAINER_STARTED')
        except Exception as e:
            logger.error(
                f'Error: Instance {self.container_name} FAILED to attach to container!\n'
            )
            logger.exception(e)
            self.close()
            raise e

    def _refresh_logs(self):
        logger.debug('Getting container logs...')

        assert (
            self.log_buffer is not None
        ), 'Log buffer is expected to be initialized when container is started'

        logs = self.log_buffer.get_and_clear()
        if logs:
            formatted_logs = '\n'.join([f'    |{log}' for log in logs])
            logger.info(
                '\n'
                + '-' * 35
                + 'Container logs:'
                + '-' * 35
                + f'\n{formatted_logs}'
                + '\n'
                + '-' * 80
            )

    @tenacity.retry(
        stop=tenacity.stop_after_delay(120) | stop_if_should_exit(),
        wait=tenacity.wait_exponential(multiplier=2, min=1, max=20),
        reraise=(ConnectionRefusedError,),
    )
    def _wait_until_alive(self):
        self._refresh_logs()
        if not (self.log_buffer and self.log_buffer.client_ready):
            raise RuntimeError('Runtime client is not ready.')

        response = send_request_with_retry(
            self.session,
            'GET',
            f'{self.api_url}/alive',
            retry_exceptions=[ConnectionRefusedError],
            timeout=300,  # 5 minutes gives the container time to be alive 🧟‍♂️
        )
        if response.status_code == 200:
            return
        else:
            msg = f'Action execution API is not alive. Response: {response}'
            logger.error(msg)
            raise RuntimeError(msg)

    def close(self):
        """Closes the DockerRuntime and associated objects."""
        if self.log_buffer:
            self.log_buffer.close()

        if self.session:
            self.session.close()

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
                return FatalErrorObservation(f'Action {action_type} does not exist.')
            if not hasattr(self, action_type):
                return FatalErrorObservation(
                    f'Action {action_type} is not supported in the current runtime.'
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
                response = send_request_with_retry(
                    self.session,
                    'POST',
                    f'{self.api_url}/execute_action',
                    json={'action': event_to_dict(action)},
                    timeout=action.timeout,
                )
                if response.status_code == 200:
                    output = response.json()
                    obs = observation_from_dict(output)
                    obs._cause = action.id  # type: ignore[attr-defined]
                else:
                    logger.debug(f'action: {action}')
                    logger.debug(f'response: {response}')
                    error_message = response.text
                    logger.error(f'Error from server: {error_message}')
                    obs = FatalErrorObservation(
                        f'Action execution failed: {error_message}'
                    )
            except requests.Timeout:
                logger.error('No response received within the timeout period.')
                obs = FatalErrorObservation(
                    f'Action execution timed out after {action.timeout} seconds.'
                )
            except Exception as e:
                logger.error(f'Error during action execution: {e}')
                obs = FatalErrorObservation(f'Action execution failed: {str(e)}')
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

            response = send_request_with_retry(
                self.session,
                'POST',
                f'{self.api_url}/upload_file',
                files=upload_data,
                params=params,
                timeout=300,
            )
            if response.status_code == 200:
                return
            else:
                error_message = response.text
                raise Exception(f'Copy operation failed: {error_message}')

        except requests.Timeout:
            raise TimeoutError('Copy operation timed out')
        except Exception as e:
            raise RuntimeError(f'Copy operation failed: {str(e)}')
        finally:
            if recursive:
                os.unlink(temp_zip_path)
            logger.info(f'Copy completed: host:{host_src} -> runtime:{sandbox_dest}')
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

            response = send_request_with_retry(
                self.session,
                'POST',
                f'{self.api_url}/list_files',
                json=data,
                timeout=30,  # 30 seconds because the container should already be alive
            )
            if response.status_code == 200:
                response_json = response.json()
                assert isinstance(response_json, list)
                return response_json
            else:
                error_message = response.text
                raise Exception(f'List files operation failed: {error_message}')
        except requests.Timeout:
            raise TimeoutError('List files operation timed out')
        except Exception as e:
            raise RuntimeError(f'List files operation failed: {str(e)}')

    def copy_from(self, path: str) -> bytes:
        """Zip all files in the sandbox and return as a stream of bytes."""
        self._refresh_logs()
        try:
            params = {'path': path}
            response = send_request_with_retry(
                self.session,
                'GET',
                f'{self.api_url}/download_files',
                params=params,
                stream=True,
                timeout=30,
            )
            if response.status_code == 200:
                data = response.content
                return data
            else:
                error_message = response.text
                raise Exception(f'Copy operation failed: {error_message}')
        except requests.Timeout:
            raise TimeoutError('Copy operation timed out')
        except Exception as e:
            raise RuntimeError(f'Copy operation failed: {str(e)}')

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

    def send_status_message(self, message: str):
        """Sends a status message if the callback function was provided."""
        if self.status_message_callback:
            self.status_message_callback(message)
