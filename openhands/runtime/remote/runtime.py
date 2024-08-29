import asyncio
import os
import ssl
import tempfile
import uuid
from typing import Any, Optional, Type
from zipfile import ZipFile

import aiohttp
import aiohttp.client_exceptions
import tenacity

from openhands.core.config import AppConfig
from openhands.core.logger import openhands_logger as logger
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
    ErrorObservation,
    NullObservation,
    Observation,
)
from openhands.events.serialization import event_to_dict, observation_from_dict
from openhands.events.serialization.action import ACTION_TYPE_TO_CLASS
from openhands.runtime.builder.remote import RemoteRuntimeBuilder
from openhands.runtime.plugins import PluginRequirement
from openhands.runtime.runtime import Runtime
from openhands.runtime.utils.runtime_build import build_runtime_image

DEFAULT_RETRY_EXCEPTIONS = [
    ssl.SSLCertVerificationError,
    aiohttp.ClientError,
    aiohttp.client_exceptions.ContentTypeError,
    aiohttp.client_exceptions.ClientConnectorCertificateError,
    ssl.SSLCertVerificationError,
    asyncio.TimeoutError,
]


class RemoteRuntime(Runtime):
    """This runtime will connect to a remote od-runtime-client."""

    port: int = 60000  # default port for the remote runtime client

    def __init__(
        self,
        config: AppConfig,
        event_stream: EventStream,
        sid: str = 'default',
        plugins: list[PluginRequirement] | None = None,
    ):
        super().__init__(config, event_stream, sid, plugins)
        if self.config.sandbox.api_hostname == 'localhost':
            self.config.sandbox.api_hostname = 'api.all-hands.dev/v0/runtime'
            logger.warning(
                'Using localhost as the API hostname is not supported in the RemoteRuntime. Please set a proper hostname.\n'
                'Setting it to default value: api.all-hands.dev/v0/runtime'
            )
        self.api_url = f'https://{self.config.sandbox.api_hostname.rstrip("/")}'

        self.session: Optional[aiohttp.ClientSession] = None

        self.action_semaphore = asyncio.Semaphore(1)  # Ensure one action at a time

        if self.config.workspace_base is not None:
            logger.warning(
                'Setting workspace_base is not supported in the remote runtime.'
            )

        if self.config.sandbox.api_key is None:
            raise ValueError(
                'API key is required to use the remote runtime. '
                'Please set the API key in the config (config.toml) or as an environment variable (SANDBOX_API_KEY).'
            )
        self.runtime_builder = RemoteRuntimeBuilder(
            self.api_url, self.config.sandbox.api_key
        )
        self.runtime_id: str | None = None
        self.runtime_url: str | None = None

        self.instance_id = (
            sid + str(uuid.uuid4()) if sid is not None else str(uuid.uuid4())
        )
        if self.config.sandbox.runtime_container_image is not None:
            raise ValueError(
                'Setting runtime_container_image is not supported in the remote runtime.'
            )
        self.container_image: str = self.config.sandbox.base_container_image
        self.container_name = 'od-remote-runtime-' + self.instance_id
        logger.debug(f'RemoteRuntime `{sid}` config:\n{self.config}')

    async def _send_request(
        self,
        method: str,
        url: str,
        retry_exceptions: list[Type[Exception]] | None = None,
        **kwargs: Any,
    ) -> aiohttp.ClientResponse:
        if retry_exceptions is None:
            retry_exceptions = DEFAULT_RETRY_EXCEPTIONS

        session = await self._ensure_session()

        def log_retry(retry_state):
            exception = retry_state.outcome.exception()
            logger.warning(
                f'Retry attempt {retry_state.attempt_number} failed with exception: {exception}'
            )

        @tenacity.retry(
            stop=tenacity.stop_after_attempt(10),
            wait=tenacity.wait_exponential(multiplier=1, min=4, max=60),
            retry=tenacity.retry_if_exception_type(tuple(retry_exceptions)),
            reraise=True,
            after=log_retry,
        )
        async def _send_request_with_retry():
            async with session.request(method, url, **kwargs) as response:
                await response.read()
                return response

        return await _send_request_with_retry()

    async def ainit(self, env_vars: dict[str, str] | None = None):
        # Check if the container image exists
        # Use the /registry_prefix endpoint to get the registry prefix
        response = await self._send_request('GET', f'{self.api_url}/registry_prefix')
        if response.status != 200:
            raise RuntimeError(
                f'Failed to get registry prefix: {await response.text()}'
            )
        response_json = await response.json()
        registry_prefix = response_json['registry_prefix']
        os.environ['OD_RUNTIME_RUNTIME_IMAGE_REPO'] = (
            registry_prefix.rstrip('/') + '/runtime'
        )
        logger.info(
            f'Runtime image repo: {os.environ["OD_RUNTIME_RUNTIME_IMAGE_REPO"]}'
        )

        if self.config.sandbox.runtime_extra_deps:
            logger.info(
                f'Installing extra user-provided dependencies in the runtime image: {self.config.sandbox.runtime_extra_deps}'
            )

        # Build the container image
        self.container_image = build_runtime_image(
            self.container_image,
            self.runtime_builder,
            extra_deps=self.config.sandbox.runtime_extra_deps,
        )

        # Use the /image_exists endpoint to check if the image exists
        response = await self._send_request(
            'GET',
            f'{self.api_url}/image_exists',
            params={'image': self.container_image},
        )
        if response.status != 200 or not (await response.json())['exists']:
            raise RuntimeError(f'Container image {self.container_image} does not exist')

        # Prepare the request body for the /start endpoint
        plugin_arg = ''
        if self.plugins is not None and len(self.plugins) > 0:
            plugin_arg = (
                f'--plugins {" ".join([plugin.name for plugin in self.plugins])} '
            )
        if self.config.sandbox.browsergym_eval_env is not None:
            browsergym_arg = (
                f'--browsergym-eval-env {self.config.sandbox.browsergym_eval_env}'
            )
        else:
            browsergym_arg = ''
        start_request = {
            'image': self.container_image,
            'command': (
                f'/openhands/miniforge3/bin/mamba run --no-capture-output -n base '
                'PYTHONUNBUFFERED=1 poetry run '
                f'python -u -m openhands.runtime.client.client {self.port} '
                f'--working-dir {self.sandbox_workspace_dir} '
                f'{plugin_arg}'
                f'--username {"openhands" if self.config.run_as_openhands else "root"} '
                f'--user-id {self.config.sandbox.user_id} '
                f'{browsergym_arg}'
            ),
            'working_dir': '/openhands/code/',
            'name': self.container_name,
            'environment': {'DEBUG': 'true'} if self.config.debug else {},
        }

        # Start the sandbox using the /start endpoint
        response = await self._send_request(
            'POST', f'{self.api_url}/start', json=start_request
        )
        if response.status != 201:
            raise RuntimeError(f'Failed to start sandbox: {await response.text()}')
        start_response = await response.json()
        self.runtime_id = start_response['runtime_id']
        self.runtime_url = start_response['url']

        logger.info(
            f'Sandbox started. Runtime ID: {self.runtime_id}, URL: {self.runtime_url}'
        )

        # Initialize environment variables
        await super().ainit(env_vars)

        logger.info(
            f'Runtime initialized with plugins: {[plugin.name for plugin in self.plugins]}'
        )
        logger.info(f'Runtime initialized with env vars: {env_vars}')
        assert (
            self.runtime_id is not None
        ), 'Runtime ID is not set. This should never happen.'
        assert (
            self.runtime_url is not None
        ), 'Runtime URL is not set. This should never happen.'

    async def _ensure_session(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={'X-API-Key': self.config.sandbox.api_key}
            )
        return self.session

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(10),
        wait=tenacity.wait_exponential(multiplier=1, min=4, max=60),
        retry=tenacity.retry_if_exception_type(RuntimeError),
        reraise=True,
    )
    async def _wait_until_alive(self):
        logger.info('Waiting for sandbox to be alive...')
        response = await self._send_request('GET', f'{self.runtime_url}/alive')
        if response.status == 200:
            return
        else:
            msg = f'Runtime is not alive (id={self.runtime_id}). Status: {response.status}.'
            logger.warning(msg)
            raise RuntimeError(msg)

    @property
    def sandbox_workspace_dir(self):
        return self.config.workspace_mount_path_in_sandbox

    async def close(self):
        if self.runtime_id:
            try:
                response = await self._send_request(
                    'POST', f'{self.api_url}/stop', json={'runtime_id': self.runtime_id}
                )
                if response.status != 200:
                    logger.error(f'Failed to stop sandbox: {await response.text()}')
                else:
                    logger.info(f'Sandbox stopped. Runtime ID: {self.runtime_id}')
            except Exception as e:
                raise e
            finally:
                if self.session is not None:
                    await self.session.close()
                self.session = None

    async def run_action(self, action: Action) -> Observation:
        if action.timeout is None:
            action.timeout = self.config.sandbox.timeout

        async with self.action_semaphore:
            if not action.runnable:
                return NullObservation('')
            action_type = action.action  # type: ignore[attr-defined]
            if action_type not in ACTION_TYPE_TO_CLASS:
                return ErrorObservation(f'Action {action_type} does not exist.')
            if not hasattr(self, action_type):
                return ErrorObservation(
                    f'Action {action_type} is not supported in the current runtime.'
                )

            await self._wait_until_alive()

            assert action.timeout is not None

            try:
                logger.info('Executing action')
                request_body = {'action': event_to_dict(action)}
                logger.debug(f'Request body: {request_body}')
                response = await self._send_request(
                    'POST',
                    f'{self.runtime_url}/execute_action',
                    json=request_body,
                    timeout=action.timeout,
                    retry_exceptions=list(
                        filter(
                            lambda e: e != asyncio.TimeoutError,
                            DEFAULT_RETRY_EXCEPTIONS,
                        )
                    ),
                )
                if response.status == 200:
                    output = await response.json()
                    obs = observation_from_dict(output)
                    obs._cause = action.id  # type: ignore[attr-defined]
                    return obs
                else:
                    error_message = await response.text()
                    logger.error(f'Error from server: {error_message}')
                    obs = ErrorObservation(f'Action execution failed: {error_message}')
            except asyncio.TimeoutError:
                logger.error('No response received within the timeout period.')
                obs = ErrorObservation('Action execution timed out')
            except Exception as e:
                logger.error(f'Error during action execution: {e}')
                obs = ErrorObservation(f'Action execution failed: {str(e)}')
            return obs

    async def run(self, action: CmdRunAction) -> Observation:
        return await self.run_action(action)

    async def run_ipython(self, action: IPythonRunCellAction) -> Observation:
        return await self.run_action(action)

    async def read(self, action: FileReadAction) -> Observation:
        return await self.run_action(action)

    async def write(self, action: FileWriteAction) -> Observation:
        return await self.run_action(action)

    async def browse(self, action: BrowseURLAction) -> Observation:
        return await self.run_action(action)

    async def browse_interactive(self, action: BrowseInteractiveAction) -> Observation:
        return await self.run_action(action)

    async def copy_to(
        self, host_src: str, sandbox_dest: str, recursive: bool = False
    ) -> None:
        if not os.path.exists(host_src):
            raise FileNotFoundError(f'Source file {host_src} does not exist')

        await self._wait_until_alive()
        try:
            if recursive:
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
                upload_data = {'file': open(host_src, 'rb')}

            params = {'destination': sandbox_dest, 'recursive': str(recursive).lower()}

            response = await self._send_request(
                'POST',
                f'{self.runtime_url}/upload_file',
                data=upload_data,
                params=params,
                retry_exceptions=list(
                    filter(
                        lambda e: e != asyncio.TimeoutError, DEFAULT_RETRY_EXCEPTIONS
                    )
                ),
            )
            if response.status == 200:
                logger.info(
                    f'Copy completed: host:{host_src} -> runtime:{sandbox_dest}. Response: {await response.text()}'
                )
                return
            else:
                error_message = await response.text()
                raise Exception(f'Copy operation failed: {error_message}')
        except asyncio.TimeoutError:
            raise TimeoutError('Copy operation timed out')
        except Exception as e:
            raise RuntimeError(f'Copy operation failed: {str(e)}')
        finally:
            if recursive:
                os.unlink(temp_zip_path)
            logger.info(f'Copy completed: host:{host_src} -> runtime:{sandbox_dest}')

    async def list_files(self, path: str | None = None) -> list[str]:
        await self._wait_until_alive()
        try:
            data = {}
            if path is not None:
                data['path'] = path

            response = await self._send_request(
                'POST',
                f'{self.runtime_url}/list_files',
                json=data,
                retry_exceptions=list(
                    filter(
                        lambda e: e != asyncio.TimeoutError, DEFAULT_RETRY_EXCEPTIONS
                    )
                ),
            )
            if response.status == 200:
                response_json = await response.json()
                assert isinstance(response_json, list)
                return response_json
            else:
                error_message = await response.text()
                raise Exception(f'List files operation failed: {error_message}')
        except asyncio.TimeoutError:
            raise TimeoutError('List files operation timed out')
        except Exception as e:
            raise RuntimeError(f'List files operation failed: {str(e)}')
