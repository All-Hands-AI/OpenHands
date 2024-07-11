import asyncio
import json
import uuid

import docker
import websockets

from opendevin.core.config import config
from opendevin.events import EventSource, EventStream, EventStreamSubscriber
from opendevin.events.action import (
    AgentRecallAction,
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
from opendevin.runtime.plugins import PluginRequirement
from opendevin.runtime.runtime import Runtime
from opendevin.runtime.server.browse import browse
from opendevin.runtime.server.files import read_file, write_file


class EventStreamRuntime(Runtime):
    # This runtime will subscribe the event stream
    # When receive an event, it will send the event to od-runtime-client which run inside the docker environment

    # websocket uri
    uri = 'ws://localhost:8080'
    container_name_prefix = 'opendevin-sandbox-'
    docker_client: docker.DockerClient

    def __init__(
        self,
        event_stream: EventStream,
        sid: str = 'default',
        container_image: str | None = None,
    ):
        # We don't need sandbox in this runtime, because it's equal to a websocket sandbox
        self._init_event_stream(event_stream)
        self._init_websocket()
        self._init_docker(sid, container_image)

    def _init_docker(self, sid, container_image):
        self.container_image = container_image
        # (
        #     config.sandbox_container_image
        #     if container_image is None
        #     else container_image
        # )
        self.instance_id = (
            sid + str(uuid.uuid4()) if sid is not None else str(uuid.uuid4())
        )
        self.container_name = self.container_name_prefix + self.instance_id
        try:
            self.docker_client = docker.from_env()
            self._init_sandbox()
        except Exception as ex:
            print(
                'Launch docker client failed. Please make sure you have installed docker and started the docker daemon.'
            )
            raise ex

    def _init_event_stream(self, event_stream: EventStream):
        self.event_stream = event_stream
        self.event_stream.subscribe(EventStreamSubscriber.RUNTIME, self.on_event)

    def _init_websocket(self):
        self.websocket = None
        # TODO: need to initialization globally only once
        # self.loop = asyncio.new_event_loop()
        # asyncio.set_event_loop(self.loop)
        # self.loop.run_until_complete(self._init_websocket_connect())

    async def _init_websocket_connect(self):
        self.websocket = await websockets.connect(self.uri)

    def _init_sandbox(self):
        try:
            # start the container
            mount_dir = config.workspace_mount_path
            self.container = self.docker_client.containers.run(
                self.container_image,
                command='tail -f /dev/null',
                # TODO: test the port mapping in mac and linux
                # network_mode='host',
                working_dir=self.sandbox_workspace_dir,
                name=self.container_name,
                detach=True,
                ports={'8080/tcp': 8080},
                volumes={mount_dir: {'bind': self.sandbox_workspace_dir, 'mode': 'rw'}},
            )
            print('Container started')
        except Exception as e:
            print('Failed to start container')
            raise e

    @property
    def sandbox_workspace_dir(self):
        return config.workspace_mount_path_in_sandbox

    def close(self):
        containers = self.docker_client.containers.list(all=True)
        for container in containers:
            try:
                if container.name.startswith(self.container_name_prefix):
                    container.remove(force=True)
            except docker.errors.NotFound:
                pass
        self.docker_client.close()

    async def on_event(self, event: Event) -> None:
        print('EventStreamRuntime: on_event triggered')
        if isinstance(event, Action):
            observation = await self.run_action(event)
            print('EventStreamRuntime: observation', observation)
            # observation._cause = event.id  # type: ignore[attr-defined]
            source = event.source if event.source else EventSource.AGENT
            await self.event_stream.add_event(observation, source)

    async def run_action(self, action: Action) -> Observation:
        """
        Run an action and return the resulting observation.
        If the action is not runnable in any runtime, a NullObservation is returned.
        If the action is not supported by the current runtime, an ErrorObservation is returned.
        We will filter some action and execute in runtime. Pass others into od-runtime-client
        """
        if not action.runnable:
            return NullObservation('')
        action_type = action.action  # type: ignore[attr-defined]
        if action_type not in ACTION_TYPE_TO_CLASS:
            return ErrorObservation(f'Action {action_type} does not exist.')
        if not hasattr(self, action_type):
            return ErrorObservation(
                f'Action {action_type} is not supported in the current runtime.'
            )
        observation = await getattr(self, action_type)(action)
        # TODO: fix ID problem, see comments https://github.com/OpenDevin/OpenDevin/pull/2603#discussion_r1668994137
        observation._parent = action.id  # type: ignore[attr-defined]
        return observation

    async def run(self, action: CmdRunAction) -> Observation:
        return await self._run_command(action)

    async def _run_command(
        self, action: Action, _stream: bool = False, timeout: int | None = None
    ) -> Observation:
        # Send action into websocket and get the result
        # TODO: need to initialization globally only once
        self.websocket = await websockets.connect(self.uri)
        if self.websocket is None:
            raise Exception('WebSocket is not connected.')
        try:
            await self.websocket.send(json.dumps(event_to_dict(action)))
            output = await asyncio.wait_for(self.websocket.recv(), timeout=timeout)
            output = json.loads(output)
            print('Received output: ', output)
        except asyncio.TimeoutError:
            print('No response received within the timeout period.')
        await self.websocket.close()
        return observation_from_dict(output)

    async def run_ipython(self, action: IPythonRunCellAction) -> Observation:
        return await self._run_command(action)

    ############################################################################
    # Keep the same with other runtimes
    ############################################################################

    async def get_working_directory(self) -> str:
        # TODO: should we get this from od-runtime-client
        return config.workspace_base

    async def read(self, action: FileReadAction) -> Observation:
        working_dir = self.get_working_directory()
        return await read_file(action.path, working_dir, action.start, action.end)

    async def write(self, action: FileWriteAction) -> Observation:
        working_dir = self.get_working_directory()
        return await write_file(
            action.path, working_dir, action.content, action.start, action.end
        )

    async def browse(self, action: BrowseURLAction) -> Observation:
        return await browse(action, self.browser)

    async def browse_interactive(self, action: BrowseInteractiveAction) -> Observation:
        return await browse(action, self.browser)

    async def recall(self, action: AgentRecallAction) -> Observation:
        return NullObservation('')

    ############################################################################
    # Initialization work inside sandbox image
    ############################################################################

    # init_runtime_tools direcctly do as what Runtime do

    # Do in the od_runtime_client
    # Overwrite the init_sandbox_plugins
    async def init_sandbox_plugins(self, plugins: list[PluginRequirement]) -> None:
        pass


def test_run_command():
    sid = 'test'
    cli_session = 'main' + ('_' + sid if sid else '')
    event_stream = EventStream(cli_session)
    runtime = EventStreamRuntime(event_stream)
    asyncio.run(runtime._run_command(CmdRunAction('ls -l')))


async def test_event_stream():
    sid = 'test'
    cli_session = 'main' + ('_' + sid if sid else '')
    event_stream = EventStream(cli_session)
    runtime = EventStreamRuntime(event_stream)
    # Test run command
    action_cmd = CmdRunAction(command='ls -l')
    print(await runtime.run_action(action_cmd))

    # Test run ipython
    test_code = "print('Hello, `World`!\n')"
    action_opython = IPythonRunCellAction(code=test_code)
    print(await runtime.run_action(action_opython))

    # Test read file
    action_read = FileReadAction(path='hello.sh')
    print(await runtime.run_action(action_read))

    # Test write file
    action_write = FileWriteAction(content='echo "Hello, World!"', path='hello.sh')
    print(await runtime.run_action(action_write))

    # Test browse
    action_browse = BrowseURLAction(url='https://google.com')
    print(await runtime.run_action(action_browse))

    # Test recall
    action_recall = AgentRecallAction(query='who am I?')
    print(await runtime.run_action(action_recall))


def test_docker_launch():
    sid = 'test'
    cli_session = 'main' + ('_' + sid if sid else '')
    event_stream = EventStream(cli_session)
    runtime = EventStreamRuntime(event_stream, sid, 'ghcr.io/opendevin/sandbox:main')
    runtime.close()


if __name__ == '__main__':
    asyncio.run(test_event_stream())
