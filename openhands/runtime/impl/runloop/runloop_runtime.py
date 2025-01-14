import logging
from typing import Callable

import tenacity
from runloop_api_client import Runloop
from runloop_api_client.types import DevboxView
from runloop_api_client.types.shared_params import LaunchParameters

from openhands.core.config import AppConfig
from openhands.core.logger import openhands_logger as logger
from openhands.events import EventStream
from openhands.runtime.impl.action_execution.action_execution_client import (
    ActionExecutionClient,
)
from openhands.runtime.plugins import PluginRequirement
from openhands.runtime.utils.command import get_action_execution_server_startup_command
from openhands.utils.tenacity_stop import stop_if_should_exit

CONTAINER_NAME_PREFIX = 'openhands-runtime-'


class RunloopRuntime(ActionExecutionClient):
    """The RunloopRuntime class is an DockerRuntime that utilizes Runloop Devbox as a runtime environment."""

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
        self.container_name = CONTAINER_NAME_PREFIX + sid
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
        # Buffer for container logs
        self._vscode_url: str | None = None

    def _get_action_execution_server_host(self):
        return self.api_url

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
        start_command = get_action_execution_server_startup_command(
            server_port=self._sandbox_port,
            plugins=self.plugins,
            app_config=self.config,
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
            name=self.sid,
            environment_variables={'DEBUG': 'true'} if self.config.debug else {},
            prebuilt='openhands',
            launch_parameters=LaunchParameters(
                available_ports=[self._sandbox_port, self._vscode_port],
                resource_size_request='LARGE',
                launch_commands=[
                    f'mkdir -p {self.config.workspace_mount_path_in_sandbox}'
                ],
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

        self.api_url = tunnel.url
        logger.info(f'Container started. Server url: {self.api_url}')

        # End Runloop connect
        # NOTE: Copied from DockerRuntime
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
        super().check_if_alive()

    def close(self, rm_all_containers: bool | None = True):
        super().close()

        if self.attach_to_existing:
            return

        if self.devbox:
            self.runloop_api_client.devboxes.shutdown(self.devbox.id)

    @property
    def vscode_url(self) -> str | None:
        if self._vscode_url is not None:  # cached value
            return self._vscode_url
        token = super().get_vscode_token()
        if not token:
            return None
        if not self.devbox:
            return None
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
