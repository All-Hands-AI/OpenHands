import asyncio
import os
import tempfile
import uuid
from typing import Optional
from zipfile import ZipFile

import aiohttp
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


class RemoteRuntime(Runtime):
    """This runtime will connect to a remote od-runtime-client."""

    port: int = 60000  # default port for the remote runtime client

    def __init__(
        self,
        config: AppConfig,
        event_stream: EventStream,
        sid: str = 'default',
        plugins: list[PluginRequirement] | None = None,
        container_image: str | None = None,
    ):
        super().__init__(config, event_stream, sid, plugins)
        self.api_url = f'https://{self.config.sandbox.api_hostname.rstrip("/")}'
        self.session: Optional[aiohttp.ClientSession] = None

        self.action_semaphore = asyncio.Semaphore(1)  # Ensure one action at a time

        assert (
            self.config.sandbox.api_key is not None
        ), 'API key is required to use the remote runtime.'
        self.runtime_builder = RemoteRuntimeBuilder(
            self.api_url, self.config.sandbox.api_key
        )
        self.runtime_id: str | None = None
        self.sandbox_url: str | None = None

        self.instance_id = (
            sid + str(uuid.uuid4()) if sid is not None else str(uuid.uuid4())
        )
        self.container_image = (
            self.config.sandbox.container_image
            if container_image is None
            else container_image
        )
        self.container_name = 'od-remote-runtime-' + self.instance_id
        logger.debug(f'RemoteRuntime `{sid}` config:\n{self.config}')

    async def ainit(self, env_vars: dict[str, str] | None = None):
        # Check if the container image exists
        # Use the /registry_prefix endpoint to get the registry prefix
        session = await self._ensure_session()
        async with session.get(f'{self.api_url}/registry_prefix') as response:
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
        session = await self._ensure_session()
        async with session.get(
            f'{self.api_url}/image_exists', params={'image': self.container_image}
        ) as response:
            if response.status != 200 or not (await response.json())['exists']:
                raise RuntimeError(
                    f'Container image {self.container_image} does not exist'
                )

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
        session = await self._ensure_session()
        async with session.post(
            f'{self.api_url}/start', json=start_request
        ) as response:
            if response.status != 201:
                raise RuntimeError(f'Failed to start sandbox: {await response.text()}')
            start_response = await response.json()
            self.runtime_id = start_response['runtime_id']
            self.sandbox_url = start_response['url']

        logger.info(
            f'Sandbox started. Runtime ID: {self.runtime_id}, URL: {self.sandbox_url}'
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
            self.sandbox_url is not None
        ), 'Sandbox URL is not set. This should never happen.'

    async def _ensure_session(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={'X-API-Key': self.config.sandbox.api_key}
            )
        return self.session

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(10),
        wait=tenacity.wait_exponential(multiplier=2, min=10, max=60),
    )
    async def _wait_until_alive(self):
        logger.info('Waiting for sandbox to be alive...')
        session = await self._ensure_session()
        async with session.get(
            f'{self.api_url}/runtime/{self.runtime_id}/{self.port}/alive'
        ) as response:
            if response.status == 200:
                return
            else:
                msg = f'Sandbox is not alive. Status: {response.status}. Response: {await response.json()}'
                logger.error(msg)
                raise RuntimeError(msg)

    @property
    def sandbox_workspace_dir(self):
        return self.config.workspace_mount_path_in_sandbox

    async def close(self):
        async def _retry_stop_runtime():
            session = await self._ensure_session()
            async with session.post(
                f'{self.api_url}/stop', json={'runtime_id': self.runtime_id}
            ) as response:
                if response.status != 200:
                    logger.error(f'Failed to stop sandbox: {await response.text()}')
                else:
                    logger.info(f'Sandbox stopped. Runtime ID: {self.runtime_id}')

        if self.runtime_id:
            await tenacity.retry(
                _retry_stop_runtime,
                stop=tenacity.stop_after_attempt(10),
                wait=tenacity.wait_exponential(multiplier=2, min=10, max=60),
            )()

        if self.session is not None and not self.session.closed:
            await self.session.close()
            self.session = None  # Set session to None after closing

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

            session = await self._ensure_session()
            await self._wait_until_alive()

            assert action.timeout is not None

            try:
                logger.info('Executing action')
                request_body = {'action': event_to_dict(action)}
                logger.debug(f'Request body: {request_body}')
                async with session.post(
                    f'{self.api_url}/runtime/{self.runtime_id}/{self.port}/execute_action',
                    json=request_body,
                    timeout=action.timeout,
                ) as response:
                    if response.status == 200:
                        output = await response.json()
                        obs = observation_from_dict(output)
                        obs._cause = action.id  # type: ignore[attr-defined]
                        return obs
                    else:
                        error_message = await response.text()
                        logger.error(f'Error from server: {error_message}')
                        obs = ErrorObservation(
                            f'Action execution failed: {error_message}'
                        )
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

        session = await self._ensure_session()
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

            async with session.post(
                f'{self.api_url}/runtime/{self.runtime_id}/{self.port}/upload_file',
                data=upload_data,
                params=params,
            ) as response:
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
        session = await self._ensure_session()
        await self._wait_until_alive()
        try:
            data = {}
            if path is not None:
                data['path'] = path

            async with session.post(
                f'{self.api_url}/runtime/{self.runtime_id}/{self.port}/list_files',
                json=data,
            ) as response:
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
