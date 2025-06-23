from typing import Callable

import httpx
import tenacity
from daytona import (
    CreateSandboxFromSnapshotParams,
    Daytona,
    DaytonaConfig,
    Sandbox,
    SessionExecuteRequest,
)

from openhands.core.config.openhands_config import OpenHandsConfig
from openhands.events.stream import EventStream
from openhands.integrations.provider import PROVIDER_TOKEN_TYPE
from openhands.runtime.impl.action_execution.action_execution_client import (
    ActionExecutionClient,
)
from openhands.runtime.plugins.requirement import PluginRequirement
from openhands.runtime.runtime_status import RuntimeStatus
from openhands.runtime.utils.command import get_action_execution_server_startup_command
from openhands.runtime.utils.request import RequestHTTPError
from openhands.utils.async_utils import call_sync_from_async
from openhands.utils.tenacity_stop import stop_if_should_exit

OPENHANDS_SID_LABEL = 'OpenHands_SID'


class DaytonaRuntime(ActionExecutionClient):
    """The DaytonaRuntime class is a DockerRuntime that utilizes Daytona Sandboxes as runtime environments."""

    _sandbox_port: int = 4444
    _vscode_port: int = 4445

    def __init__(
        self,
        config: OpenHandsConfig,
        event_stream: EventStream,
        sid: str = 'default',
        plugins: list[PluginRequirement] | None = None,
        env_vars: dict[str, str] | None = None,
        status_callback: Callable | None = None,
        attach_to_existing: bool = False,
        headless_mode: bool = True,
        user_id: str | None = None,
        git_provider_tokens: PROVIDER_TOKEN_TYPE | None = None,
    ):
        assert config.daytona_api_key, 'Daytona API key is required'

        self.config = config
        self.sid = sid
        self.sandbox: Sandbox | None = None
        self._vscode_url: str | None = None

        daytona_config = DaytonaConfig(
            api_key=config.daytona_api_key.get_secret_value(),
            server_url=config.daytona_api_url,
            target=config.daytona_target,
        )
        self.daytona = Daytona(daytona_config)

        # workspace_base cannot be used because we can't bind mount into a workspace.
        if self.config.workspace_base is not None:
            self.log(
                'warning',
                'Workspace mounting is not supported in the Daytona runtime.',
            )

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

    def _get_sandbox(self) -> Sandbox | None:
        try:
            sandboxes = self.daytona.list({OPENHANDS_SID_LABEL: self.sid})
            if len(sandboxes) == 0:
                return None
            assert len(sandboxes) == 1, 'Multiple sandboxes found for SID'

            sandbox = sandboxes[0]

            self.log('info', f'Attached to existing sandbox with id: {self.sid}')
        except Exception:
            self.log(
                'warning',
                f'Failed to attach to existing sandbox with id: {self.sid}',
            )
            sandbox = None

        return sandbox

    def _get_creation_env_vars(self) -> dict[str, str]:
        env_vars: dict[str, str] = {
            'port': str(self._sandbox_port),
            'PYTHONUNBUFFERED': '1',
            'VSCODE_PORT': str(self._vscode_port),
        }

        if self.config.debug:
            env_vars['DEBUG'] = 'true'

        return env_vars

    def _create_sandbox(self) -> Sandbox:
        sandbox_params = CreateSandboxFromSnapshotParams(
            language='python',
            snapshot=self.config.sandbox.runtime_container_image,
            public=True,
            env_vars=self._get_creation_env_vars(),
            labels={OPENHANDS_SID_LABEL: self.sid},
        )
        return self.daytona.create(sandbox_params)

    def _construct_api_url(self, port: int) -> str:
        assert self.sandbox is not None, 'Sandbox is not initialized'
        assert self.sandbox.runner_domain is not None, 'Runner domain is not available'

        return f'https://{port}-{self.sandbox.id}.{self.sandbox.runner_domain}'

    @property
    def action_execution_server_url(self) -> str:
        return self.api_url

    def _start_action_execution_server(self) -> None:
        assert self.sandbox is not None, 'Sandbox is not initialized'

        start_command: list[str] = get_action_execution_server_startup_command(
            server_port=self._sandbox_port,
            plugins=self.plugins,
            app_config=self.config,
            override_user_id=1000,
            override_username='openhands',
        )
        start_command_str: str = (
            f'mkdir -p {self.config.workspace_mount_path_in_sandbox} && cd /openhands/code && '
            + ' '.join(start_command)
        )

        self.log(
            'debug',
            f'Starting action execution server with command: {start_command_str}',
        )

        exec_session_id = 'action-execution-server'
        self.sandbox.process.create_session(exec_session_id)

        exec_command = self.sandbox.process.execute_session_command(
            exec_session_id,
            SessionExecuteRequest(command=start_command_str, var_async=True),
        )

        self.log('debug', f'exec_command_id: {exec_command.cmd_id}')

    @tenacity.retry(
        stop=tenacity.stop_after_delay(120) | stop_if_should_exit(),
        wait=tenacity.wait_fixed(1),
        reraise=(ConnectionRefusedError,),
    )
    def _wait_until_alive(self):
        super().check_if_alive()

    async def connect(self):
        self.set_runtime_status(RuntimeStatus.STARTING_RUNTIME)
        should_start_action_execution_server = False

        if self.attach_to_existing:
            self.sandbox = await call_sync_from_async(self._get_sandbox)
        else:
            should_start_action_execution_server = True

        if self.sandbox is None:
            self.set_runtime_status(RuntimeStatus.BUILDING_RUNTIME)
            self.sandbox = await call_sync_from_async(self._create_sandbox)
            self.log('info', f'Created a new sandbox with id: {self.sid}')

        self.api_url = self._construct_api_url(self._sandbox_port)

        state = self.sandbox.state

        if state == 'stopping':
            self.log('info', 'Waiting for the Daytona sandbox to stop...')
            await call_sync_from_async(self.sandbox.wait_for_sandbox_stop)
            state = 'stopped'

        if state == 'stopped':
            self.log('info', 'Starting the Daytona sandbox...')
            await call_sync_from_async(self.sandbox.start)
            should_start_action_execution_server = True

        if should_start_action_execution_server:
            await call_sync_from_async(self._start_action_execution_server)
            self.log(
                'info',
                f'Container started. Action execution server url: {self.api_url}',
            )

        self.log('info', 'Waiting for client to become ready...')
        self.set_runtime_status(RuntimeStatus.STARTING_RUNTIME)
        await call_sync_from_async(self._wait_until_alive)

        if should_start_action_execution_server:
            await call_sync_from_async(self.setup_initial_env)

        self.log(
            'info',
            f'Container initialized with plugins: {[plugin.name for plugin in self.plugins]}',
        )

        if should_start_action_execution_server:
            self.set_runtime_status(RuntimeStatus.READY)
        self._runtime_initialized = True

    @tenacity.retry(
        retry=tenacity.retry_if_exception(
            lambda e: (
                isinstance(e, httpx.HTTPError) or isinstance(e, RequestHTTPError)
            )
            and hasattr(e, 'response')
            and e.response.status_code == 502
        ),
        stop=tenacity.stop_after_delay(120) | stop_if_should_exit(),
        wait=tenacity.wait_fixed(1),
        reraise=True,
    )
    def _send_action_server_request(self, method, url, **kwargs):
        return super()._send_action_server_request(method, url, **kwargs)

    def close(self):
        super().close()

        if self.attach_to_existing:
            return

        if self.sandbox:
            self.sandbox.delete()

    @property
    def vscode_url(self) -> str | None:
        if self._vscode_url is not None:  # cached value
            return self._vscode_url
        token = super().get_vscode_token()
        if not token:
            self.log(
                'warning', 'Failed to get VSCode token while trying to get VSCode URL'
            )
            return None
        if not self.sandbox:
            self.log(
                'warning', 'Sandbox is not initialized while trying to get VSCode URL'
            )
            return None
        self._vscode_url = (
            self._construct_api_url(self._vscode_port)
            + f'/?tkn={token}&folder={self.config.workspace_mount_path_in_sandbox}'
        )

        self.log(
            'debug',
            f'VSCode URL: {self._vscode_url}',
        )

        return self._vscode_url

    @property
    def additional_agent_instructions(self) -> str:
        return f'When showing endpoints to access applications for any port, e.g. port 3000, instead of localhost:3000, use this format: {self._construct_api_url(3000)}.'
