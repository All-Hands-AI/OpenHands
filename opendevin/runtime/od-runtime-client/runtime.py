from typing import Any
import asyncio
import json
import os
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
    CmdOutputObservation,
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
        # self._init_event_stream()
        self._init_websocket()
    
    def _init_event_stream(self):
        self.event_stream.subscribe(EventStreamSubscriber.RUNTIME, self.on_event)

    def _init_websocket(self):
        self.websocket = None
        self.loop = asyncio.get_event_loop()
        self.loop.run_until_complete(self._init_websocket_connect())
    
    async def _init_websocket_connect(self):
        self.websocket = await websockets.connect(self.uri)
    
    def close(self):
        pass
    
    async def on_event(self, event: Event) -> None:
        if isinstance(event, Action):
            observation = await self.run_action(event)
            observation._cause = event.id  # type: ignore[attr-defined]
            source = event.source if event.source else EventSource.AGENT
            await self.event_stream.add_event(observation, source)
    
    async def run_action(self, action: Action) -> Observation:
        """
        Run an action and return the resulting observation.
        If the action is not runnable in any runtime, a NullObservation is returned.
        If the action is not supported by the current runtime, an ErrorObservation is returned.
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
        observation = await self.execute(action)
        observation._parent = action.id  # type: ignore[attr-defined]
        return observation
    
    async def execute(
        self, action: Action, stream: bool = False, timeout: int | None = None
    ) -> Observation:
        # Send action into websocket and get the result
        if self.websocket is None:
            raise Exception("WebSocket is not connected.")
        await self.websocket.send(json.dumps(event_to_dict(action)))
        output = await self.websocket.recv()
        print(output)
        return observation_from_dict(json.loads(output))
        
    async def run_ipython(self, action: IPythonRunCellAction) -> Observation:
        raise NotImplementedError

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
        return await browse(action, self.browser)

    async def browse_interactive(self, action: BrowseInteractiveAction) -> Observation:
        return await browse(action, self.browser)

    async def recall(self, action: AgentRecallAction) -> Observation:
        return NullObservation('')
    
    ############################################################################ 
    # Function that should impelement in od-runtime-client
    ############################################################################
    async def run(self, action: CmdRunAction) -> Observation:
        raise NotImplementedError
    

if __name__ == "__main__":
    event_stream = EventStream("1")
    runtime = EventStreamRuntime(event_stream)
    asyncio.run(runtime.execute(CmdRunAction('ls -l')))


    