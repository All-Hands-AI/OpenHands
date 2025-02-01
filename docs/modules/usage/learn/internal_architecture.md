# OpenHands Internal Architecture Guide

This guide provides a deep dive into OpenHands' internal architecture, explaining how different components work together and how to extend them.

## Table of Contents
1. [Server Architecture](#server-architecture)
2. [Agent System](#agent-system)
3. [Event System](#event-system)
4. [Runtime and Execution](#runtime-and-execution)
5. [Implementation Examples](#implementation-examples)

## Server Architecture

### FastAPI Application Structure

The OpenHands server is built on FastAPI and organized into several routers:

```python
# Server initialization (openhands/server/app.py)
app = FastAPI(
    title='OpenHands',
    description='OpenHands: Code Less, Make More',
    version=__version__,
    lifespan=_lifespan,
)

# Router registration
app.include_router(public_api_router)
app.include_router(files_api_router)
app.include_router(security_api_router)
app.include_router(feedback_api_router)
app.include_router(conversation_api_router)
app.include_router(manage_conversation_api_router)
app.include_router(settings_router)
app.include_router(github_api_router)
app.include_router(trajectory_router)
```

### Key Routes and Their Functions

1. **Conversation API** (`conversation_api_router`)
   - Handles real-time communication with agents
   - Manages conversation state and history
   - Processes user inputs and agent responses

2. **Files API** (`files_api_router`)
   - Manages file operations
   - Handles file uploads and downloads
   - Processes file-related requests

3. **Security API** (`security_api_router`)
   - Implements security measures
   - Handles authentication and authorization
   - Manages security settings

## Agent System

### Agent Base Class

The Agent system is built around an abstract base class that defines the core functionality:

```python
# openhands/controller/agent.py
class Agent(ABC):
    _registry: dict[str, Type['Agent']] = {}
    sandbox_plugins: list[PluginRequirement] = []

    def __init__(self, llm: LLM, config: 'AgentConfig'):
        self.llm = llm
        self.config = config
        self._complete = False
        self.prompt_manager = None

    @abstractmethod
    def step(self, state: 'State') -> 'Action':
        """Execute one step of the agent's logic"""
        pass

    def reset(self) -> None:
        """Reset agent state"""
        self._complete = False
        if self.llm:
            self.llm.reset()
```

### Agent Registration System

Agents are registered using a class-based registry system:

```python
@classmethod
def register(cls, name: str, agent_cls: Type['Agent']):
    """Register a new agent type"""
    if name in cls._registry:
        raise AgentAlreadyRegisteredError(name)
    cls._registry[name] = agent_cls

@classmethod
def get_cls(cls, name: str) -> Type['Agent']:
    """Get a registered agent class"""
    if name not in cls._registry:
        raise AgentNotRegisteredError(name)
    return cls._registry[name]
```

## Event System

### Event Base Class

Events are the primary communication mechanism between components:

```python
# openhands/events/event.py
@dataclass
class Event:
    INVALID_ID = -1

    @property
    def message(self) -> str | None:
        return getattr(self, '_message', '')

    @property
    def source(self) -> EventSource | None:
        return getattr(self, '_source', None)

    def set_hard_timeout(self, value: int | None, blocking: bool = True):
        self._timeout = value
        if value is not None and value > 600:
            logger.warning('Timeout greater than 600 seconds may not be supported')
```

### Event Sources

Events can come from different sources:

```python
class EventSource(str, Enum):
    AGENT = 'agent'
    USER = 'user'
    ENVIRONMENT = 'environment'
```

## Implementation Examples

### 1. Creating a Custom Agent

Here's a complete example of creating a custom agent:

```python
from openhands.controller.agent import Agent
from openhands.events import Event, EventSource
from openhands.events.action import Action

class CustomTaskAgent(Agent):
    def __init__(self, llm, config):
        super().__init__(llm, config)
        self.task_state = {}
    
    def step(self, state: 'State') -> 'Action':
        # Process current state
        current_input = state.get_latest_input()
        
        # Use LLM for processing
        llm_response = await self.llm.generate(
            prompt=self.prompt_manager.get_prompt("task_processing"),
            context={"input": current_input}
        )
        
        # Create and return action
        return Action(
            type="task_response",
            data={"response": llm_response},
            source=EventSource.AGENT
        )
    
    def reset(self) -> None:
        super().reset()
        self.task_state = {}

# Register the agent
Agent.register("custom_task", CustomTaskAgent)
```

### 2. Implementing a Custom Event Handler

Example of implementing an event handler:

```python
from openhands.events import Event, EventStream
from typing import AsyncGenerator

class CustomEventHandler:
    def __init__(self):
        self.event_stream = EventStream()
    
    async def handle_events(self) -> AsyncGenerator[Event, None]:
        async for event in self.event_stream:
            # Process event
            if event.source == EventSource.USER:
                # Handle user event
                processed_event = await self._process_user_event(event)
                yield processed_event
            elif event.source == EventSource.AGENT:
                # Handle agent event
                processed_event = await self._process_agent_event(event)
                yield processed_event
    
    async def _process_user_event(self, event: Event) -> Event:
        # Process user event
        return Event(
            message="Processed user event",
            source=EventSource.ENVIRONMENT
        )
    
    async def _process_agent_event(self, event: Event) -> Event:
        # Process agent event
        return Event(
            message="Processed agent event",
            source=EventSource.ENVIRONMENT
        )
```

### 3. Custom Runtime Implementation

Example of implementing a custom runtime:

```python
from openhands.runtime.base import Runtime
from openhands.events.action import Action
from typing import Any, Dict

class CustomRuntime(Runtime):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.capabilities = ["custom_action"]
        self._initialize_runtime()
    
    def _initialize_runtime(self):
        # Initialize runtime-specific resources
        self.resources = {}
    
    async def execute(self, action: Action) -> Dict[str, Any]:
        if action.type in self.capabilities:
            return await self._handle_custom_action(action)
        return await super().execute(action)
    
    async def _handle_custom_action(self, action: Action) -> Dict[str, Any]:
        # Implement custom action handling
        try:
            result = await self._process_action(action.data)
            return {
                "status": "success",
                "result": result
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _process_action(self, data: Dict[str, Any]) -> Any:
        # Implement action processing logic
        return {"processed": data}
    
    async def cleanup(self):
        # Clean up resources
        self.resources.clear()
```

## Best Practices for Implementation

1. **Event Handling**
   - Always specify event source
   - Implement proper timeout handling
   - Use appropriate event types

2. **Agent Implementation**
   - Keep agents focused on specific tasks
   - Implement proper state management
   - Handle errors gracefully

3. **Runtime Development**
   - Define clear capabilities
   - Implement proper resource cleanup
   - Handle concurrent executions

4. **Error Handling**
   - Use custom exceptions
   - Provide detailed error messages
   - Implement proper error recovery

## Debugging Tips

1. **Event Debugging**
```python
from openhands.core.logger import openhands_logger

class DebugEventHandler:
    def __init__(self):
        self.logger = openhands_logger

    async def handle_event(self, event: Event):
        self.logger.debug(f"Event received: {event}")
        self.logger.debug(f"Event source: {event.source}")
        self.logger.debug(f"Event message: {event.message}")
```

2. **Agent Debugging**
```python
class DebugAgent(Agent):
    def step(self, state: 'State') -> 'Action':
        self.logger.debug(f"Current state: {state}")
        action = super().step(state)
        self.logger.debug(f"Generated action: {action}")
        return action
```

3. **Runtime Debugging**
```python
class DebugRuntime(Runtime):
    async def execute(self, action: Action):
        self.logger.debug(f"Executing action: {action}")
        result = await super().execute(action)
        self.logger.debug(f"Action result: {result}")
        return result
```

Remember to use the built-in logging system for debugging and monitoring your implementations.