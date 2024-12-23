import logging
import threading
import time
from typing import Callable

import requests
import tenacity
from runloop_api_client import Runloop
from runloop_api_client.types import DevboxView
from runloop_api_client.types.shared_params import LaunchParameters

from openhands.core.config import AppConfig
from openhands.core.exceptions import (
    AgentRuntimeNotReadyError,
    AgentRuntimeUnavailableError,
)
from openhands.core.logger import openhands_logger as logger
from openhands.events import EventStream
from openhands.runtime.impl.eventstream.eventstream_runtime import EventStreamRuntime
from openhands.runtime.plugins import PluginRequirement
from openhands.runtime.utils.command import get_remote_startup_command
from openhands.runtime.utils.log_streamer import LogStreamer
from openhands.runtime.utils.request import send_request
from openhands.utils.tenacity_stop import stop_if_should_exit

CONTAINER_NAME_PREFIX = 'openhands-runtime-'


class RunloopLogStreamer(LogStreamer):
    """Streams Runloop devbox logs to stdout.

    This class provides a way to stream logs from a Runloop devbox directly to stdout
    through the provided logging function.
    """

    def __init__(
        self,
        runloop_api_client: Runloop,
        devbox_id: str,
        logFn: Callable,
    ):
        self.runloop_api_client = runloop_api_client
        self.devbox_id = devbox_id
        self.log = logFn
        self.log_index = 0
        self._stop_event = threading.Event()

        # Start the stdout streaming thread
        self.stdout_thread = threading.Thread(target=self._stream_logs)
        self.stdout_thread.daemon = True
        self.stdout_thread.start()

    def _stream_logs(self):
        """Stream logs from the Runloop devbox."""
        try:
            while True:
                raw_logs = self.runloop_api_client.devboxes.logs.list(
                    self.devbox_id
                ).logs[self.log_index :]
                logs = [
                    log.message
                    for log in raw_logs
                    if log.message and log.cmd_id is None
                ]

                self.log_index += len(raw_logs)
                if self._stop_event.is_set():
                    break
                if logs:
                    for log_line in logs:
                        self.log('debug', f'[inside devbox] {log_line}')

                time.sleep(1)
        except Exception as e:
            self.log('error', f'Error streaming runloop logs: {e}')


class RunloopRuntime(EventStreamRuntime):
    """The RunloopRuntime class is an EventStreamRuntime that utilizes Runloop Devbox as a runtime environment."""

    _sandbox_port: int = 4444
    _vscode_port: int = 4445

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
        assert config.runloop_api_key is not None, 'Runloop API key is required'
        self.devbox: DevboxView | None = None
        self.config = config
        self.runloop_api_client = Runloop(
            bearer_token=config.runloop_api_key,
        )
        self.session = requests.Session()
        self.container_name = CONTAINER_NAME_PREFIX + sid
        self.action_semaphore = threading.Semaphore(1)  # Ensure one action at a time
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
        # Buffer for container logs
        self.log_streamer: LogStreamer | None = None
        self._vscode_url: str | None = None

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(120),
        wait=tenacity.wait_fixed(1),
    )
    def _wait_for_devbox(self, devbox: DevboxView) -> DevboxView:
        """Pull devbox status until it is running"""
        if devbox == 'running':
            return devbox

        devbox = self.runloop_api_client.devboxes.retrieve(id=devbox.id)
        if devbox.status != 'running':
            raise ConnectionRefusedError('Devbox is not running')

        # Devbox is connected and running
        logging.debug(f'devbox.id={devbox.id} is running')
        return devbox

    def _create_new_devbox(self) -> DevboxView:
        # Note: Runloop connect
        sandbox_workspace_dir = self.config.workspace_mount_path_in_sandbox
        plugin_args = []
        if self.plugins is not None and len(self.plugins) > 0:
            plugin_args.append('--plugins')
            plugin_args.extend([plugin.name for plugin in self.plugins])

        browsergym_args = []
        if self.config.sandbox.browsergym_eval_env is not None:
            browsergym_args = [
                '-browsergym-eval-env',
                self.config.sandbox.browsergym_eval_env,
            ]

        # Copied from EventstreamRuntime
        start_command = get_remote_startup_command(
            self._sandbox_port,
            sandbox_workspace_dir,
            'openhands' if self.config.run_as_openhands else 'root',
            self.config.sandbox.user_id,
            plugin_args,
            browsergym_args,
            is_root=not self.config.run_as_openhands,  # is_root=True when running as root
        )

        # Add some additional commands based on our image
        # NB: start off as root, action_execution_server will ultimately choose user but expects all context
        # (ie browser) to be installed as root
        start_command = (
            'export MAMBA_ROOT_PREFIX=/openhands/micromamba && '
            'cd /openhands/code && '
            + '/openhands/micromamba/bin/micromamba run -n openhands poetry config virtualenvs.path /openhands/poetry && '
            + ' '.join(start_command)
        )
        entrypoint = f"sudo bash -c '{start_command}'"

        devbox = self.runloop_api_client.devboxes.create(
            entrypoint=entrypoint,
            setup_commands=[f'mkdir -p {self.config.workspace_mount_path_in_sandbox}'],
            name=self.sid,
            environment_variables={'DEBUG': 'true'} if self.config.debug else {},
            prebuilt='openhands',
            launch_parameters=LaunchParameters(
                available_ports=[self._sandbox_port, self._vscode_port],
                resource_size_request='LARGE',
            ),
            metadata={'container-name': self.container_name},
        )
        return self._wait_for_devbox(devbox)

    async def connect(self):
        self.send_status_message('STATUS$STARTING_RUNTIME')

        if self.attach_to_existing:
            active_devboxes = self.runloop_api_client.devboxes.list(
                status='running'
            ).devboxes
            self.devbox = next(
                (devbox for devbox in active_devboxes if devbox.name == self.sid), None
            )

        if self.devbox is None:
            self.devbox = self._create_new_devbox()

        # Create tunnel - this will return a stable url, so is safe to call if we are attaching to existing
        tunnel = self.runloop_api_client.devboxes.create_tunnel(
            id=self.devbox.id,
            port=self._sandbox_port,
        )

        # Hook up logs
        self.log_streamer = RunloopLogStreamer(
            self.runloop_api_client, self.devbox.id, logger.info
        )
        self.api_url = tunnel.url
        logger.info(f'Container started. Server url: {self.api_url}')

        # End Runloop connect
        # NOTE: Copied from EventStreamRuntime
        logger.info('Waiting for client to become ready...')
        self.send_status_message('STATUS$WAITING_FOR_CLIENT')
        self._wait_until_alive()

        if not self.attach_to_existing:
            self.setup_initial_env()

        logger.info(
            f'Container initialized with plugins: {[plugin.name for plugin in self.plugins]}'
        )
        self.send_status_message(' ')

    @tenacity.retry(
        stop=tenacity.stop_after_delay(120) | stop_if_should_exit(),
        wait=tenacity.wait_fixed(1),
        reraise=(ConnectionRefusedError,),
    )
    def _wait_until_alive(self):
        if not self.log_streamer:
            raise AgentRuntimeNotReadyError('Runtime client is not ready.')
        response = send_request(
            self.session,
            'GET',
            f'{self.api_url}/alive',
            timeout=5,
        )
        if response.status_code == 200:
            return
        else:
            msg = f'Action execution API is not alive. Response: {response}'
            logger.error(msg)
            raise AgentRuntimeUnavailableError(msg)

    def close(self, rm_all_containers: bool | None = True):
        if self.log_streamer:
            self.log_streamer.close()

        if self.session:
            self.session.close()

        if self.attach_to_existing:
            return

        if self.devbox:
            self.runloop_api_client.devboxes.shutdown(self.devbox.id)

    @property
    def vscode_url(self) -> str | None:
        if self.vscode_enabled and self.devbox and self.devbox.status == 'running':
            if self._vscode_url is not None:
                return self._vscode_url

            try:
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
                    token = response_json['token']

                self._vscode_url = (
                    self.runloop_api_client.devboxes.create_tunnel(
                        id=self.devbox.id,
                        port=self._vscode_port,
                    ).url
                    + f'/?tkn={token}&folder={self.config.workspace_mount_path_in_sandbox}'
                )

                self.log(
                    'debug',
                    f'VSCode URL: {self._vscode_url}',
                )

                return self._vscode_url
            except Exception as e:
                self.log(
                    'error',
                    f'Failed to create vscode tunnel {e}',
                )
                return None
        else:
            return None
