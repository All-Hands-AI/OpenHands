import asyncio
import uuid
from typing import Optional

import aiohttp
import docker
import tenacity

from opendevin.core.config import SandboxConfig, config
from opendevin.core.logger import opendevin_logger as logger
from opendevin.events import EventSource, EventStream
from opendevin.events.action import (
    BrowseInteractiveAction,
    BrowseURLAction,
    CmdRunAction,
    FileReadAction,
    FileWriteAction,
    IPythonRunCellAction,
)
from opendevin.events.action.action import Action
from opendevin.events.event import Event
from opendevin.events.observation import (
    ErrorObservation,
    NullObservation,
    Observation,
)
from opendevin.events.serialization import event_to_dict, observation_from_dict
from opendevin.events.serialization.action import ACTION_TYPE_TO_CLASS
from opendevin.runtime.plugins import (
    AgentSkillsRequirement,
    JupyterRequirement,
    PluginRequirement,
)
from opendevin.runtime.runtime import Runtime
from opendevin.runtime.utils import find_available_tcp_port
from opendevin.runtime.utils.runtime_build import build_runtime_image


class EventStreamRuntime(Runtime):
    """This runtime will subscribe the event stream.
    When receive an event, it will send the event to od-runtime-client which run inside the docker environment.
    """

    container_name_prefix = 'opendevin-sandbox-'

    def __init__(
        self,
        sandbox_config: SandboxConfig,
        event_stream: EventStream,
        sid: str = 'default',
        container_image: str | None = None,
        plugins: list[PluginRequirement] | None = None,
    ):
        super().__init__(
            sandbox_config, event_stream, sid
        )  # will initialize the event stream
        self._port = find_available_tcp_port()
        self.api_url = f'http://localhost:{self._port}'
        self.session: Optional[aiohttp.ClientSession] = None

        self.instance_id = (
            sid + str(uuid.uuid4()) if sid is not None else str(uuid.uuid4())
        )
        # TODO: We can switch to aiodocker when `get_od_sandbox_image` is updated to use aiodocker
        self.docker_client: docker.DockerClient = self._init_docker_client()
        self.container_image = (
            config.sandbox.container_image
            if container_image is None
            else container_image
        )
        self.container_name = self.container_name_prefix + self.instance_id

        self.plugins = plugins if plugins is not None else []
        self.container = None
        self.action_semaphore = asyncio.Semaphore(1)  # Ensure one action at a time

    async def ainit(self, env_vars: dict[str, str] | None = None):
        self.container_image = build_runtime_image(
            self.container_image,
            self.docker_client,
            # NOTE: You can need set DEBUG=true to update the source code
            # inside the container. This is useful when you want to test/debug the
            # latest code in the runtime docker container.
            update_source_code=config.debug,
        )
        self.container = await self._init_container(
            self.sandbox_workspace_dir,
            mount_dir=config.workspace_mount_path,
            plugins=self.plugins,
        )
        # Initialize the env vars
        await super().ainit(env_vars)

    @staticmethod
    def _init_docker_client() -> docker.DockerClient:
        try:
            return docker.from_env()
        except Exception as ex:
            logger.error(
                'Launch docker client failed. Please make sure you have installed docker and started the docker daemon.'
            )
            raise ex

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(5),
        wait=tenacity.wait_exponential(multiplier=1, min=4, max=60),
    )
    async def _init_container(
        self,
        sandbox_workspace_dir: str,
        mount_dir: str = config.workspace_mount_path,
        plugins: list[PluginRequirement] | None = None,
    ):
        try:
            logger.info(
                f'Starting container with image: {self.container_image} and name: {self.container_name}'
            )
            if plugins is None:
                plugins = []
            plugin_names = ' '.join([plugin.name for plugin in plugins])

            network_mode: str | None = None
            port_mapping: dict[str, int] | None = None
            if self.sandbox_config.use_host_network:
                network_mode = 'host'
                logger.warn(
                    'Using host network mode. If you are using MacOS, please make sure you have the latest version of Docker Desktop and enabled host network feature: https://docs.docker.com/network/drivers/host/#docker-desktop'
                )
            else:
                port_mapping = {f'{self._port}/tcp': self._port}

            container = self.docker_client.containers.run(
                self.container_image,
                command=(
                    f'/opendevin/miniforge3/bin/mamba run --no-capture-output -n base '
                    'PYTHONUNBUFFERED=1 poetry run '
                    f'python -u -m opendevin.runtime.client.client {self._port} '
                    f'--working-dir {sandbox_workspace_dir} '
                    f'--plugins {plugin_names}'
                ),
                network_mode=network_mode,
                ports=port_mapping,
                working_dir='/opendevin/code/',
                name=self.container_name,
                detach=True,
                environment={'DEBUG': 'true'} if config.debug else None,
                volumes={mount_dir: {'bind': sandbox_workspace_dir, 'mode': 'rw'}},
            )
            logger.info(f'Container started. Server url: {self.api_url}')
            return container
        except Exception as e:
            logger.error('Failed to start container')
            logger.exception(e)
            await self.close(close_client=False)
            raise e

    async def _ensure_session(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(10),
        wait=tenacity.wait_exponential(multiplier=2, min=4, max=600),
    )
    async def _wait_until_alive(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(f'{self.api_url}/alive') as response:
                if response.status == 200:
                    return
                else:
                    logger.error(
                        f'Action execution API is not alive. Response: {response}'
                    )
                    raise RuntimeError(
                        f'Action execution API is not alive. Response: {response}'
                    )

    @property
    def sandbox_workspace_dir(self):
        return config.workspace_mount_path_in_sandbox

    async def close(self, close_client: bool = True):
        if self.session is not None and not self.session.closed:
            await self.session.close()

        containers = self.docker_client.containers.list(all=True)
        for container in containers:
            try:
                if container.name.startswith(self.container_name_prefix):
                    logs = container.logs(tail=1000).decode('utf-8')
                    logger.debug(
                        f'==== Container logs ====\n{logs}\n==== End of container logs ===='
                    )
                    container.remove(force=True)
            except docker.errors.NotFound:
                pass
        if close_client:
            self.docker_client.close()

    async def on_event(self, event: Event) -> None:
        logger.info(f'EventStreamRuntime: on_event triggered: {event}')
        if isinstance(event, Action):
            logger.info(event, extra={'msg_type': 'ACTION'})
            observation = await self.run_action(event)
            # observation._cause = event.id  # type: ignore[attr-defined]
            logger.info(observation, extra={'msg_type': 'OBSERVATION'})
            source = event.source if event.source else EventSource.AGENT
            await self.event_stream.add_event(observation, source)

    async def run_action(self, action: Action, timeout: int = 600) -> Observation:
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
            try:
                async with session.post(
                    f'{self.api_url}/execute_action',
                    json={'action': event_to_dict(action)},
                    timeout=timeout,
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
                            f'Command execution failed: {error_message}'
                        )
            except asyncio.TimeoutError:
                logger.error('No response received within the timeout period.')
                obs = ErrorObservation('Command execution timed out')
            except Exception as e:
                logger.error(f'Error during command execution: {e}')
                obs = ErrorObservation(f'Command execution failed: {str(e)}')
            obs._parent = action.id  # type: ignore[attr-defined]
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

    ############################################################################
    # Keep the same with other runtimes
    ############################################################################

    def get_working_directory(self):
        raise NotImplementedError(
            'This method is not implemented in the runtime client.'
        )

    ############################################################################
    # Initialization work inside sandbox image
    ############################################################################

    # init_runtime_tools direcctly do as what Runtime do

    # Do in the od_runtime_client
    # Overwrite the init_sandbox_plugins
    def init_sandbox_plugins(self, plugins: list[PluginRequirement]) -> None:
        pass


async def test_run_command():
    sid = 'test'
    cli_session = 'main' + ('_' + sid if sid else '')
    event_stream = EventStream(cli_session)
    runtime = EventStreamRuntime(
        sandbox_config=config.sandbox, event_stream=event_stream, sid=sid
    )
    await runtime.ainit()
    await runtime.run_action(CmdRunAction('ls -l'))


async def test_event_stream():
    sid = 'test'
    cli_session = 'main' + ('_' + sid if sid else '')
    event_stream = EventStream(cli_session)
    runtime = EventStreamRuntime(
        sandbox_config=config.sandbox,
        event_stream=event_stream,
        sid=sid,
        container_image='ubuntu:22.04',
        plugins=[JupyterRequirement(), AgentSkillsRequirement()],
    )
    await runtime.ainit()

    # Test run command
    action_cmd = CmdRunAction(command='ls -l')
    logger.info(action_cmd, extra={'msg_type': 'ACTION'})
    logger.info(await runtime.run_action(action_cmd), extra={'msg_type': 'OBSERVATION'})

    # Test run ipython
    test_code = "print('Hello, `World`!\\n')"
    action_ipython = IPythonRunCellAction(code=test_code)
    logger.info(action_ipython, extra={'msg_type': 'ACTION'})
    logger.info(
        await runtime.run_action(action_ipython), extra={'msg_type': 'OBSERVATION'}
    )

    # Test read file (file should not exist)
    action_read = FileReadAction(path='hello.sh')
    logger.info(action_read, extra={'msg_type': 'ACTION'})
    logger.info(
        await runtime.run_action(action_read), extra={'msg_type': 'OBSERVATION'}
    )

    # Test write file
    action_write = FileWriteAction(content='echo "Hello, World!"', path='hello.sh')
    logger.info(action_write, extra={'msg_type': 'ACTION'})
    logger.info(
        await runtime.run_action(action_write), extra={'msg_type': 'OBSERVATION'}
    )

    # Test read file (file should exist)
    action_read = FileReadAction(path='hello.sh')
    logger.info(action_read, extra={'msg_type': 'ACTION'})
    logger.info(
        await runtime.run_action(action_read), extra={'msg_type': 'OBSERVATION'}
    )

    # Test browse
    action_browse = BrowseURLAction(url='https://google.com')
    logger.info(action_browse, extra={'msg_type': 'ACTION'})
    logger.info(
        await runtime.run_action(action_browse), extra={'msg_type': 'OBSERVATION'}
    )

    await runtime.close()


if __name__ == '__main__':
    asyncio.run(test_event_stream())
