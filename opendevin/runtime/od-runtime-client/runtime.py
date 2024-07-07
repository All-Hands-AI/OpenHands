from typing import Any
import asyncio
import json
import websockets
from opendevin.events.serialization.action import ACTION_TYPE_TO_CLASS
from opendevin.events.action.action import Action
from opendevin.events.event import Event
from opendevin.events.observation import Observation
from opendevin.events.stream import EventStream
from opendevin.events.serialization import event_to_dict, observation_from_dict
from opendevin.runtime.runtime import Runtime
from opendevin.runtime.server.browse import browse
from opendevin.runtime.server.files import read_file, write_file
from opendevin.core.config import config
from opendevin.events.observation import (
    ErrorObservation,
    NullObservation,
    Observation,
)
from opendevin.events.action import (
    AgentRecallAction,
    BrowseInteractiveAction,
    BrowseURLAction,
    CmdRunAction,
    FileReadAction,
    FileWriteAction,
    IPythonRunCellAction,
)
import asyncio
from opendevin.events import EventSource, EventStream, EventStreamSubscriber

class EventStreamRuntime(Runtime):
    # This runtime will subscribe the event stream
    # When receive an event, it will send the event to od-runtime-client which run inside the docker environment
    
    # websocket uri
    uri = 'ws://localhost:8080'

    def __init__(self, event_stream: EventStream, sid: str = 'default'):
        # We don't need sandbox in this runtime, because it's equal to a websocket sandbox
        self.event_stream = event_stream
        self._init_event_stream()
        self._init_websocket()
    
    def _init_event_stream(self):
        self.event_stream.subscribe(EventStreamSubscriber.RUNTIME, self.on_event)

    def _init_websocket(self):
        self.websocket = None
        # self.loop = asyncio.new_event_loop()
        # asyncio.set_event_loop(self.loop)
        # self.loop.run_until_complete(self._init_websocket_connect())
    
    async def _init_websocket_connect(self):
        self.websocket = await websockets.connect(self.uri)
    
    def close(self):
        pass
    
    async def on_event(self, event: Event) -> None:
        print("EventStreamRuntime: on_event triggered")
        if isinstance(event, Action):
            observation = await self.run_action(event)
            print("EventStreamRuntime: observation", observation)
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
        # TODO: fix ID problem
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
            raise Exception("WebSocket is not connected.")
        try:
            await self.websocket.send(json.dumps(event_to_dict(action)))
            output = await asyncio.wait_for(self.websocket.recv(), timeout=timeout)
            output = json.loads(output)
            print("Received output: ", output)
        except asyncio.TimeoutError:
            print("No response received within the timeout period.")
        await self.websocket.close()
        return observation_from_dict(output)
        
    async def run_ipython(self, action: IPythonRunCellAction) -> Observation:
        return await self.run(action)

    ############################################################################ 
    # Keep the same with other runtimes
    ############################################################################ 

    def get_working_directory(self):
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
        return await browse(action, self.browse)

    async def browse_interactive(self, action: BrowseInteractiveAction) -> Observation:
        return await browse(action, self.browse)

    async def recall(self, action: AgentRecallAction) -> Observation:
        return NullObservation('')
    
def test_run_command():
    sid = "test"
    cli_session = 'main' + ('_' + sid if sid else '')
    event_stream = EventStream(cli_session)
    runtime = EventStreamRuntime(event_stream)
    asyncio.run(runtime._run_command(CmdRunAction('ls -l')))

async def test_event_stream():
    sid = "test"
    cli_session = 'main' + ('_' + sid if sid else '')
    event_stream = EventStream(cli_session)
    runtime = EventStreamRuntime(event_stream)
    # Test run command
    action = CmdRunAction(command='ls -l')
    print(await runtime.run_action(action))

    # Test run ipython
    test_code = "print('Hello, `World`!\n')"
    action = IPythonRunCellAction(code=test_code)
    print(await runtime.run_action(action))

    # Test read file
    action = FileReadAction(path='hello.sh')
    print(await runtime.run_action(action))

    # Test write file
    action = FileWriteAction(content='echo "Hello, World!"', path='hello.sh')
    print(await runtime.run_action(action))

    # Test browse
    action = BrowseURLAction(url='https://google.com')
    print(await runtime.run_action(action))

    # Test recall
    action = AgentRecallAction(query='who am I?')
    print(await runtime.run_action(action))
    

if __name__ == "__main__":
    asyncio.run(test_event_stream())


    