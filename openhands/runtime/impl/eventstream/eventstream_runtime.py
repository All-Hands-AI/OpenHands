import os
import tempfile
import threading
from pathlib import Path
from typing import Callable
from zipfile import ZipFile

import requests

from openhands.core.config import AppConfig
from openhands.core.exceptions import (
    AgentRuntimeError,
    AgentRuntimeTimeoutError,
)
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
from openhands.runtime.base import Runtime
from openhands.runtime.plugins import PluginRequirement
from openhands.runtime.runtime_manager import RuntimeManager
from openhands.runtime.utils.log_streamer import LogStreamer
from openhands.runtime.utils.request import send_request
from openhands.runtime.utils.runtime_build import build_runtime_image
from openhands.utils.async_utils import call_sync_from_async


class EventStreamRuntime(Runtime):
    """This runtime will subscribe the event stream.
    When receive an event, it will send the event to runtime-client which run inside the docker environment.

    Args:
        config (AppConfig): The application configuration.
        event_stream (EventStream): The event stream to subscribe to.
        sid (str, optional): The session ID. Defaults to 'default'.
        plugins (list[PluginRequirement] | None, optional): List of plugin requirements. Defaults to None.
        env_vars (dict[str, str] | None, optional): Environment variables to set. Defaults to None.
        runtime_manager (RuntimeManager): The runtime manager instance.
    """

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
        runtime_manager: RuntimeManager | None = None,
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
        runtime_manager: RuntimeManager | None = None,
    ):
        self.config = config
        self._host_port = 30000  # initial dummy value
        self._container_port = 30001  # initial dummy value
        self._vscode_url: str | None = None  # initial dummy value
        self._runtime_initialized: bool = False
        self.api_url = f'{self.config.sandbox.local_runtime_url}:{self._container_port}'
        self.session = requests.Session()
        self.status_callback = status_callback

        self.base_container_image = self.config.sandbox.base_container_image
        self.runtime_container_image = self.config.sandbox.runtime_container_image
        self.container_name = 'openhands-runtime-' + sid
        self.container = None
        self.action_semaphore = threading.Semaphore(1)  # Ensure one action at a time

        # Buffer for container logs
        self.log_streamer: LogStreamer | None = None

        self.runtime_manager = runtime_manager

        self.init_base_runtime(
            config,
            event_stream,
            sid,
            plugins,
            env_vars,
            status_callback,
            attach_to_existing,
            headless_mode,
            runtime_manager,
        )

        # Log runtime_extra_deps after base class initialization so self.sid is available
        if self.config.sandbox.runtime_extra_deps:
            self.log(
                'debug',
                f'Installing extra user-provided dependencies in the runtime image: {self.config.sandbox.runtime_extra_deps}',
            )

    async def connect(self):
        if not self.runtime_manager:
            raise RuntimeError('RuntimeManager not initialized')

        self.send_status_message('STATUS$STARTING_RUNTIME')
        try:
            self.container, self._container_port = self.runtime_manager._attach_to_container(self.container_name)
            self._host_port = self._container_port
            self.api_url = f'{self.config.sandbox.local_runtime_url}:{self._container_port}'
            self.log(
                'debug',
                f'attached to container: {self.container_name} {self._container_port} {self.api_url}',
            )
        except Exception as e:
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
                    self.runtime_manager._runtime_builder,
                    platform=self.config.sandbox.platform,
                    extra_deps=self.config.sandbox.runtime_extra_deps,
                    force_rebuild=self.config.sandbox.force_rebuild_runtime,
                    extra_build_args=self.config.sandbox.runtime_extra_build_args,
                )

            self.log(
                'info', f'Starting runtime with image: {self.runtime_container_image}'
            )
            self._host_port = self.runtime_manager._find_available_port()
            self._container_port = self._host_port
            self.api_url = f'{self.config.sandbox.local_runtime_url}:{self._container_port}'

            self.container = self.runtime_manager._initialize_container(
                self.runtime_container_image,
                self.container_name,
                self._container_port,
                self.plugins,
                self.initial_env_vars,
                self.status_callback,
            )
            self.log(
                'info',
                f'Container started: {self.container_name}. VSCode URL: {self.vscode_url}',
            )

        self.log_streamer = LogStreamer(self.container, self.log)

        if not self.attach_to_existing:
            self.log('info', f'Waiting for client to become ready at {self.api_url}...')
            self.send_status_message('STATUS$WAITING_FOR_CLIENT')

        await call_sync_from_async(
            lambda: self.runtime_manager and self.runtime_manager._wait_until_alive(
                self.container_name,
                self._container_port,
                self.log_streamer,
            )
        )

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

    def close(self, rm_all_containers: bool | None = None):
        """Closes the EventStreamRuntime and associated objects

        Parameters:
        - rm_all_containers (bool): Whether to remove all containers with the 'openhands-sandbox-' prefix
        """
        if self.log_streamer:
            self.log_streamer.close()

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
                raise AgentRuntimeTimeoutError(
                    f'Runtime failed to return execute_action before the requested timeout of {action.timeout}s'
                )

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

    def copy_to(
        self, host_src: str, sandbox_dest: str, recursive: bool = False
    ) -> None:
        if not os.path.exists(host_src):
            raise FileNotFoundError(f'Source file {host_src} does not exist')

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
            raise AgentRuntimeTimeoutError('Copy operation timed out')
        except Exception as e:
            raise AgentRuntimeError(f'Copy operation failed: {str(e)}')
        finally:
            if recursive:
                os.unlink(temp_zip_path)
            self.log(
                'debug', f'Copy completed: host:{host_src} -> runtime:{sandbox_dest}'
            )

    def list_files(self, path: str | None = None) -> list[str]:
        """List files in the sandbox.

        If path is None, list files in the sandbox's initial working directory (e.g., /workspace).
        """

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