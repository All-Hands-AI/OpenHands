import os
import threading
from pathlib import Path
from typing import Callable, Optional

import requests
import tenacity
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_code_engine_sdk.code_engine_v2 import CodeEngineV2

from openhands.core.config import AppConfig
from openhands.core.exceptions import (
    AgentRuntimeNotReadyError,
    AgentRuntimeUnavailableError,
)
from openhands.events import EventStream
from openhands.events.action import (
    BrowseInteractiveAction,
    BrowseURLAction,
    CmdRunAction,
    FileReadAction,
    FileWriteAction,
    IPythonRunCellAction,
)
from openhands.events.action.action import Action
from openhands.events.observation import (
    Observation,
)
from openhands.events.serialization import observation_from_dict
from openhands.runtime.base import Runtime
from openhands.runtime.plugins import PluginRequirement
from openhands.runtime.utils.command import get_remote_startup_command
from openhands.runtime.utils.request import (
    RequestHTTPError,
    send_request,
)
from openhands.utils.async_utils import call_sync_from_async
from openhands.utils.tenacity_stop import stop_if_should_exit


class IBMCodeEngineRuntime(Runtime):
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
        # We need to set session and action_semaphore before the __init__ below, or we get odd errors
        self.session = requests.Session()
        self.action_semaphore = threading.Semaphore(1)

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
        self.runtime_url: str | None = None
        self.container_port: int
        self._runtime_initialized: bool = False

    async def connect(self):
        try:
            await call_sync_from_async(self._create_new_sandbox())
        except Exception:
            self.log('error', 'Runtime failed to start, timed out before ready')
            raise
        await call_sync_from_async(self._initialize_sandbox())
        self._runtime_initialized = True

    def _initialize_sandbox(self):
        return

    def _create_new_sandbox(self):
        # get image
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
        self.runtime_url = self._create_app()

        self.container_port = 8889  # urlparse(self.runtime_url).port
        print(f'Started Job at : {self.runtime_url}')
        self._start_runtime()
        self.send_status_message('STATUS$WAITING_FOR_CLIENT')
        self._wait_until_alive()
        self.send_status_message(' ')

    def _create_app(
        self,
    ):  # TODO - Use settings once integrated instead of self.config ?
        authenticator = IAMAuthenticator(
            apikey=os.environ['CE_API_FID'],
            url=self.config.extended['ibm']['iam_prod_url'],
        )
        service = CodeEngineV2(authenticator=authenticator)
        service.set_service_url(
            f'https://api.{self.config.extended['ibm']['ce_region']}.codeengine.cloud.ibm.com/v2'
        )
        # must be synchronous then ? for 30 min ? so the job is not killed ?
        response = service.create_job_run(
            job_name=self.config.extended['ibm']['ce_job_name'],
            project_id=self.config.extended['ibm']['ce_project_id'],
        )
        return response.get_result()['href']

    def _build_runtime(self):
        self.log('debug', f'Building RemoteRuntime config:\n{self.config}')
        with self._send_request(  # TODO CODE ENGINE CALL
            'POST',
            f'{self.config.sandbox.remote_runtime_api_url}',
            is_retry=False,
            timeout=60,
        ) as response:
            response_json = response.json()
        registry_prefix = response_json['registry_prefix']
        os.environ['OH_RUNTIME_RUNTIME_IMAGE_REPO'] = (
            registry_prefix.rstrip('/') + '/runtime'
        )

        # Build the container image
        # self.container_image = build_runtime_image(
        #     self.config.sandbox.base_container_image,
        #     self.runtime_builder,
        #     platform=self.config.sandbox.platform,
        #     extra_deps=self.config.sandbox.runtime_extra_deps,
        #     force_rebuild=self.config.sandbox.force_rebuild_runtime,
        # )
        # TODO this may not be needed - we are building a pure remote image

        with self._send_request(  # TODO check if image started
            'GET',
            f'{self.config.sandbox.remote_runtime_api_url}/version',
            is_retry=False,
            # params={'image': self.container_image},
            timeout=60,
        ) as response:
            if not response.json()['exists']:
                raise Exception(
                    f'Container image {self.container_image} does not exist'
                )

    def _start_runtime(self):
        # Prepare the request body for the /start endpoint
        codeengine_start_cmd = get_remote_startup_command(
            self.container_port,
            self.config.workspace_mount_path_in_sandbox,
            'openhands' if self.config.run_as_openhands else 'root',
            self.config.sandbox.user_id,
            [],  # self.plugins,
            browsergym_args=[],
            is_root=not self.config.run_as_openhands,  # is_root=True when running as root
        )

        # creates a request to the remote server ?
        start_request = {
            'image': self.container_image,
            'command': codeengine_start_cmd,
            'working_dir': '/openhands/code/',
            'environment': {'DEBUG': 'true'} if self.config.debug else {},
            'session_id': self.sid,
            'resource_factor': self.config.sandbox.remote_runtime_resource_factor,
        }

        # Start the sandbox using the /start endpoint
        # TODO implement a /start endpoint ?
        try:
            with self._send_request(
                'POST',
                f'{self.runtime_url}/version',
                is_retry=False,
                json=start_request,
                timeout=60,
            ) as response:
                self._parse_runtime_response(response)
            self.log(
                'debug',
                f'Runtime started. URL: {self.runtime_url}',
            )
        except requests.HTTPError as e:
            self.log('error', f'Unable to start runtime: {e}')
            raise AgentRuntimeUnavailableError() from e

    def _send_request(self, method, url, is_retry=False, **kwargs):
        is_runtime_request = self.runtime_url and self.runtime_url in url
        try:
            return send_request(self.session, method, url, **kwargs)
        except requests.Timeout:
            self.log('error', 'No response received within the timeout period.')
            raise
        except RequestHTTPError as e:
            if is_runtime_request and e.response.status_code in (404, 502):
                raise Exception(
                    f'{e.response.status_code} error while connecting to {self.runtime_url}'
                ) from e
            elif is_runtime_request and e.response.status_code == 503:
                if not is_retry:
                    self.log('warning', 'Runtime appears to be paused. Resuming...')
                    self._resume_runtime()
                    self._wait_until_alive()
                    return self._send_request(method, url, True, **kwargs)
                else:
                    raise AgentRuntimeUnavailableError(
                        f'{e.response.status_code} error while connecting to {self.runtime_url}'
                    ) from e

            else:
                raise e

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

    def _parse_runtime_response(self, response: requests.Response):
        start_response = response.json()
        self.runtime_id = start_response['runtime_id']
        self.runtime_url = start_response['url']
        if 'session_api_key' in start_response:
            self.session.headers.update(
                {'X-Session-API-Key': start_response['session_api_key']}
            )

    def _resume_runtime(self):
        with self._send_request(
            'POST',
            f'{self.config.sandbox.remote_runtime_api_url}/resume',
            is_retry=False,
            json={'runtime_id': self.runtime_id},
            timeout=60,
        ):
            pass
        self.log('debug', 'Runtime resumed.')

    def _wait_until_alive_impl(self):
        self.log('debug', f'Waiting for runtime to be alive at url: {self.runtime_url}')

    def close(self, timeout: int = 10):
        return

    def run_action(self, action: Action, is_retry: bool = False) -> Observation:
        return observation_from_dict({'hello': 'world'})

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
        return None

    def list_files(self, path: str | None = None) -> list[str]:
        return ['hello', 'world']

    def copy_from(self, path: str) -> Path:
        return Path('hello_worlsd.py')

    @property
    def vscode_url(self) -> str | None:
        return None
