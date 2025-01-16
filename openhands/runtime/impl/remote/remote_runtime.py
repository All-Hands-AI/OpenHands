import os
from typing import Callable, Optional
from urllib.parse import urlparse

import requests
import tenacity

from openhands.core.config import AppConfig
from openhands.core.exceptions import (
    AgentRuntimeDisconnectedError,
    AgentRuntimeError,
    AgentRuntimeNotFoundError,
    AgentRuntimeNotReadyError,
    AgentRuntimeUnavailableError,
)
from openhands.events import EventStream
from openhands.runtime.builder.remote import RemoteRuntimeBuilder
from openhands.runtime.impl.action_execution.action_execution_client import (
    ActionExecutionClient,
)
from openhands.runtime.plugins import PluginRequirement
from openhands.runtime.utils.command import get_action_execution_server_startup_command
from openhands.runtime.utils.request import send_request
from openhands.runtime.utils.runtime_build import build_runtime_image
from openhands.utils.async_utils import call_sync_from_async
from openhands.utils.tenacity_stop import stop_if_should_exit


class RemoteRuntime(ActionExecutionClient):
    """This runtime will connect to a remote oh-runtime-client."""

    port: int = 60000  # default port for the remote runtime client

    def __init__(
        self,
        config: AppConfig,
        event_stream: EventStream,
        sid: str = 'default',
        plugins: list[PluginRequirement] | None = None,
        env_vars: dict[str, str] | None = None,
        status_callback: Optional[Callable] = None,
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
        if self.config.sandbox.api_key is None:
            raise ValueError(
                'API key is required to use the remote runtime. '
                'Please set the API key in the config (config.toml) or as an environment variable (SANDBOX_API_KEY).'
            )
        self.session.headers.update({'X-API-Key': self.config.sandbox.api_key})

        if self.config.workspace_base is not None:
            self.log(
                'debug',
                'Setting workspace_base is not supported in the remote runtime.',
            )

        self.runtime_builder = RemoteRuntimeBuilder(
            self.config.sandbox.remote_runtime_api_url,
            self.config.sandbox.api_key,
            self.session,
        )
        self.runtime_id: str | None = None
        self.runtime_url: str | None = None
        self.available_hosts: dict[str, int] = {}
        self._runtime_initialized: bool = False

    def _get_action_execution_server_host(self):
        return self.runtime_url

    async def connect(self):
        try:
            await call_sync_from_async(self._start_or_attach_to_runtime)
        except AgentRuntimeNotReadyError:
            self.log('error', 'Runtime failed to start, timed out before ready')
            raise
        await call_sync_from_async(self.setup_initial_env)
        self._runtime_initialized = True

    def _start_or_attach_to_runtime(self):
        existing_runtime = self._check_existing_runtime()
        if existing_runtime:
            self.log('debug', f'Using existing runtime with ID: {self.runtime_id}')
        elif self.attach_to_existing:
            raise AgentRuntimeNotFoundError(
                f'Could not find existing runtime for SID: {self.sid}'
            )
        else:
            self.send_status_message('STATUS$STARTING_CONTAINER')
            if self.config.sandbox.runtime_container_image is None:
                self.log(
                    'info',
                    f'Building remote runtime with base image: {self.config.sandbox.base_container_image}',
                )
                self._build_runtime()
            else:
                self.log(
                    'info',
                    f'Starting remote runtime with image: {self.config.sandbox.runtime_container_image}',
                )
                self.container_image = self.config.sandbox.runtime_container_image
            self._start_runtime()
        assert (
            self.runtime_id is not None
        ), 'Runtime ID is not set. This should never happen.'
        assert (
            self.runtime_url is not None
        ), 'Runtime URL is not set. This should never happen.'
        self.send_status_message('STATUS$WAITING_FOR_CLIENT')
        if not self.attach_to_existing:
            self.log('info', 'Waiting for runtime to be alive...')
        self._wait_until_alive()
        if not self.attach_to_existing:
            self.log('info', 'Runtime is ready.')
        self.send_status_message(' ')

    def _check_existing_runtime(self) -> bool:
        try:
            with self._send_runtime_api_request(
                'GET',
                f'{self.config.sandbox.remote_runtime_api_url}/sessions/{self.sid}',
            ) as response:
                data = response.json()
                status = data.get('status')
                if status == 'running' or status == 'paused':
                    self._parse_runtime_response(response)
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                return False
            self.log('debug', f'Error while looking for remote runtime: {e}')
            raise

        if status == 'running':
            return True
        elif status == 'stopped':
            self.log('debug', 'Found existing remote runtime, but it is stopped')
            return False
        elif status == 'paused':
            self.log('debug', 'Found existing remote runtime, but it is paused')
            self._resume_runtime()
            return True
        else:
            self.log('error', f'Invalid response from runtime API: {data}')
            return False

    def _build_runtime(self):
        self.log('debug', f'Building RemoteRuntime config:\n{self.config}')
        with self._send_runtime_api_request(
            'GET',
            f'{self.config.sandbox.remote_runtime_api_url}/registry_prefix',
        ) as response:
            response_json = response.json()
        registry_prefix = response_json['registry_prefix']
        os.environ['OH_RUNTIME_RUNTIME_IMAGE_REPO'] = (
            registry_prefix.rstrip('/') + '/runtime'
        )
        self.log(
            'debug',
            f'Runtime image repo: {os.environ["OH_RUNTIME_RUNTIME_IMAGE_REPO"]}',
        )

        if self.config.sandbox.runtime_extra_deps:
            self.log(
                'debug',
                f'Installing extra user-provided dependencies in the runtime image: {self.config.sandbox.runtime_extra_deps}',
            )

        # Build the container image
        self.container_image = build_runtime_image(
            self.config.sandbox.base_container_image,
            self.runtime_builder,
            platform=self.config.sandbox.platform,
            extra_deps=self.config.sandbox.runtime_extra_deps,
            force_rebuild=self.config.sandbox.force_rebuild_runtime,
        )

        with self._send_runtime_api_request(
            'GET',
            f'{self.config.sandbox.remote_runtime_api_url}/image_exists',
            params={'image': self.container_image},
        ) as response:
            if not response.json()['exists']:
                raise AgentRuntimeError(
                    f'Container image {self.container_image} does not exist'
                )

    def _start_runtime(self):
        # Prepare the request body for the /start endpoint
        command = get_action_execution_server_startup_command(
            server_port=self.port,
            plugins=self.plugins,
            app_config=self.config,
        )
        start_request = {
            'image': self.container_image,
            'command': command,
            'working_dir': '/openhands/code/',
            'environment': {'DEBUG': 'true'}
            if self.config.debug or os.environ.get('DEBUG', 'false').lower() == 'true'
            else {},
            'session_id': self.sid,
            'resource_factor': self.config.sandbox.remote_runtime_resource_factor,
        }

        # Start the sandbox using the /start endpoint
        try:
            with self._send_runtime_api_request(
                'POST',
                f'{self.config.sandbox.remote_runtime_api_url}/start',
                json=start_request,
            ) as response:
                self._parse_runtime_response(response)
            self.log(
                'debug',
                f'Runtime started. URL: {self.runtime_url}',
            )
        except requests.HTTPError as e:
            self.log('error', f'Unable to start runtime: {e}')
            raise AgentRuntimeUnavailableError() from e

    def _resume_runtime(self):
        """
        1. Show status update that runtime is being started.
        2. Send the runtime API a /resume request
        3. Poll for the runtime to be ready
        4. Update env vars
        """
        self.send_status_message('STATUS$STARTING_RUNTIME')
        with self._send_runtime_api_request(
            'POST',
            f'{self.config.sandbox.remote_runtime_api_url}/resume',
            json={'runtime_id': self.runtime_id},
        ):
            pass
        self._wait_until_alive()
        self.setup_initial_env()
        self.log('debug', 'Runtime resumed.')

    def _parse_runtime_response(self, response: requests.Response):
        start_response = response.json()
        self.runtime_id = start_response['runtime_id']
        self.runtime_url = start_response['url']
        self.available_hosts = start_response.get('work_hosts', {})

        if 'session_api_key' in start_response:
            self.session.headers.update(
                {'X-Session-API-Key': start_response['session_api_key']}
            )

    @property
    def vscode_url(self) -> str | None:
        token = super().get_vscode_token()
        if not token:
            return None
        _parsed_url = urlparse(self.runtime_url)
        assert isinstance(_parsed_url.scheme, str) and isinstance(
            _parsed_url.netloc, str
        )
        vscode_url = f'{_parsed_url.scheme}://vscode-{_parsed_url.netloc}/?tkn={token}&folder={self.config.workspace_mount_path_in_sandbox}'
        self.log(
            'debug',
            f'VSCode URL: {vscode_url}',
        )
        return vscode_url

    @property
    def web_hosts(self) -> dict[str, int]:
        return self.available_hosts

    def _wait_until_alive(self):
        retry_decorator = tenacity.retry(
            stop=tenacity.stop_after_delay(
                self.config.sandbox.remote_runtime_init_timeout
            )
            | stop_if_should_exit(),
            reraise=True,
            retry=tenacity.retry_if_exception_type(AgentRuntimeNotReadyError),
            wait=tenacity.wait_fixed(2),
        )
        return retry_decorator(self._wait_until_alive_impl)()

    def _wait_until_alive_impl(self):
        self.log('debug', f'Waiting for runtime to be alive at url: {self.runtime_url}')
        with self._send_runtime_api_request(
            'GET',
            f'{self.config.sandbox.remote_runtime_api_url}/sessions/{self.sid}',
        ) as runtime_info_response:
            runtime_data = runtime_info_response.json()
        assert 'runtime_id' in runtime_data
        assert runtime_data['runtime_id'] == self.runtime_id
        assert 'pod_status' in runtime_data
        pod_status = runtime_data['pod_status'].lower()
        self.log('debug', f'Pod status: {pod_status}')

        # FIXME: We should fix it at the backend of /start endpoint, make sure
        # the pod is created before returning the response.
        # Retry a period of time to give the cluster time to start the pod
        if pod_status == 'ready':
            try:
                self.check_if_alive()
            except requests.HTTPError as e:
                self.log(
                    'warning', f"Runtime /alive failed, but pod says it's ready: {e}"
                )
                raise AgentRuntimeNotReadyError(
                    f'Runtime /alive failed to respond with 200: {e}'
                )
            return
        elif (
            pod_status == 'not found'
            or pod_status == 'pending'
            or pod_status == 'running'
        ):  # nb: Running is not yet Ready
            raise AgentRuntimeNotReadyError(
                f'Runtime (ID={self.runtime_id}) is not yet ready. Status: {pod_status}'
            )
        elif pod_status in ('failed', 'unknown', 'crashloopbackoff'):
            # clean up the runtime
            self.close()
            if pod_status == 'crashloopbackoff':
                raise AgentRuntimeUnavailableError(
                    'Runtime crashed and is being restarted, potentially due to memory usage. Please try again.'
                )
            else:
                raise AgentRuntimeUnavailableError(
                    f'Runtime is unavailable (status: {pod_status}). Please try again.'
                )
        else:
            # Maybe this should be a hard failure, but passing through in case the API changes
            self.log('warning', f'Unknown pod status: {pod_status}')

        self.log(
            'debug',
            f'Waiting for runtime pod to be active. Current status: {pod_status}',
        )
        raise AgentRuntimeNotReadyError()

    def close(self):
        if self.config.sandbox.keep_runtime_alive or self.attach_to_existing:
            super().close()
            return
        try:
            with self._send_runtime_api_request(
                'POST',
                f'{self.config.sandbox.remote_runtime_api_url}/stop',
                json={'runtime_id': self.runtime_id},
            ):
                self.log('debug', 'Runtime stopped.')
        except Exception as e:
            raise e
        finally:
            super().close()

    def _send_runtime_api_request(self, method, url, **kwargs):
        return send_request(self.session, method, url, **kwargs)

    def _send_action_server_request(self, method, url, **kwargs):
        try:
            return super()._send_action_server_request(method, url, **kwargs)
        except requests.Timeout:
            self.log(
                'error',
                f'No response received within the timeout period for url: {url}',
            )
            raise

        except requests.HTTPError as e:
            if e.response.status_code in (404, 502):
                if e.response.status_code == 404:
                    raise AgentRuntimeDisconnectedError(
                        'Runtime is not responding. This may be temporary, please try again.'
                    ) from e
                else:  # 502
                    raise AgentRuntimeDisconnectedError(
                        'Runtime is temporarily unavailable. This may be due to a restart or network issue, please try again.'
                    ) from e
            elif e.response.status_code == 503:
                self.log('warning', 'Runtime appears to be paused. Resuming...')
                self._resume_runtime()
                return super()._send_action_server_request(method, url, **kwargs)
            else:
                raise e
