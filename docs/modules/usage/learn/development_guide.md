# OpenHands Development Guide

This guide will help you understand how to contribute to OpenHands development, from setting up your environment to creating new components.

## Table of Contents
1. [Installation and Setup](#installation-and-setup)
2. [System Architecture](#system-architecture)
3. [Component Initialization Flow](#component-initialization-flow)
4. [Core Concepts](#core-concepts)
5. [Development Guide](#development-guide)
6. [Testing Your Changes](#testing-your-changes)

## Installation and Setup

### Prerequisites
- Linux, Mac OS, or WSL on Windows (Ubuntu >= 22.04)
- Docker
- Python 3.12
- NodeJS >= 20.x
- Poetry >= 1.8

### Installation Steps

1. **Clone the Repository**
```bash
git clone https://github.com/All-Hands-AI/OpenHands.git
cd OpenHands
```

2. **Build the Project**
```bash
make build
```
This command will:
- Check all dependencies
- Install Python dependencies via Poetry
- Install frontend dependencies
- Install pre-commit hooks
- Build the frontend

3. **Configure the Language Model**
```bash
make setup-config
```
Follow the prompts to configure:
- LLM API key
- Model name
- Workspace directory
- Embedding model settings

4. **Start the Backend Service**
```bash
make start-backend
```
This starts the backend server with:
- Host: 0.0.0.0 (accessible from any host)
- Port: 3000 (default)
- Hot reload enabled
- Workspace directory excluded from reload

## System Architecture

OpenHands follows a modular architecture with these key components:

```
openhands/
├── server/         # FastAPI backend server
├── controller/     # Agent control and state management
├── events/         # Event system and tools
├── runtime/        # Runtime environment and execution
├── memory/         # Memory and state persistence
├── llm/           # Language model integration
├── agenthub/      # Agent implementations
└── microagent/    # Micro-agent framework
```

### Key Components

1. **Server Layer** (`server/`)
   - Handles HTTP/WebSocket connections
   - Manages sessions and conversations
   - Routes requests to appropriate handlers

2. **Controller Layer** (`controller/`)
   - Manages agent lifecycle
   - Handles state transitions
   - Processes agent actions

3. **Events System** (`events/`)
   - Defines event types and tools
   - Handles event serialization
   - Manages event streams

4. **Runtime Environment** (`runtime/`)
   - Executes agent actions
   - Provides sandbox environment
   - Manages plugins and extensions

## Component Initialization Flow

When the backend service starts, the following initialization sequence occurs:

1. **Server Initialization**
```python
# openhands/server/listen.py
app = FastAPI()
app.include_router(api_router)
app.add_middleware(...)

# Initialize core services
@app.on_event("startup")
async def startup_event():
    initialize_services()
    setup_routes()
```

2. **Session Management**
```python
# openhands/server/session/manager.py
class SessionManager:
    def create_session(self):
        # Initialize session components
        session = Session()
        session.register_runtime(...)
        session.register_agent(...)
        return session
```

3. **Agent Initialization**
```python
# openhands/controller/agent_controller.py
class AgentController:
    def initialize(self):
        # Setup agent state
        self.state = AgentState()
        # Register event handlers
        self.register_handlers()
        # Initialize memory
        self.memory = Memory()
```

## Core Concepts

### 1. Sessions and Runtime

Sessions manage the lifecycle of agents and their runtime environment:

```python
from openhands.server.session import Session
from openhands.runtime import Runtime

class CustomSession(Session):
    def __init__(self):
        self.runtime = Runtime()
        self.agents = {}
    
    def register_agent(self, agent):
        self.agents[agent.id] = agent
        agent.bind_runtime(self.runtime)
```

### 2. Events and State

The event system manages communication between components:

```python
from openhands.events import Event, EventStream

class CustomAgent:
    def __init__(self):
        self.event_stream = EventStream()
        
    async def handle_event(self, event: Event):
        # Process event
        if event.type == "user_input":
            response = await self.process_input(event.data)
            await self.event_stream.emit("agent_response", response)
```

### 3. Memory and State Management

Memory components handle persistence and state:

```python
from openhands.memory import Memory

class CustomMemory(Memory):
    def __init__(self):
        self.state = {}
        
    async def store(self, key: str, value: any):
        self.state[key] = value
        
    async def retrieve(self, key: str) -> any:
        return self.state.get(key)
```

## Development Guide

### Creating a New Agent

1. Create a new directory under `openhands/agenthub/`:
```bash
mkdir openhands/agenthub/my_agent
```

2. Create the agent class:
```python
# openhands/agenthub/my_agent/agent.py
from openhands.controller.agent import Agent
from openhands.events import Event

class MyAgent(Agent):
    def __init__(self, config):
        super().__init__(config)
        self.name = "my_agent"
    
    async def handle_user_input(self, event: Event):
        # Process user input
        response = await self.process(event.data)
        # Emit response
        await self.emit_event("agent_response", response)
    
    async def process(self, input_data):
        # Implement your agent's logic here
        return {"result": "processed"}
```

3. Register your agent:
```python
# openhands/agenthub/my_agent/__init__.py
from .agent import MyAgent

def create_agent(config):
    return MyAgent(config)
```

### Creating a New Runtime Component

1. Create a new runtime implementation:
```python
# openhands/runtime/impl/my_runtime.py
from openhands.runtime.base import Runtime

class MyRuntime(Runtime):
    def __init__(self, config):
        super().__init__(config)
        self.capabilities = ["my_capability"]
    
    async def execute(self, action):
        if action.type == "my_capability":
            return await self._handle_capability(action)
        return await super().execute(action)
    
    async def _handle_capability(self, action):
        # Implement capability
        return {"status": "success"}
```

2. Register the runtime:
```python
# openhands/runtime/impl/__init__.py
from .my_runtime import MyRuntime

def create_runtime(config):
    return MyRuntime(config)
```

### Creating a New Service

1. Create the service class:
```python
# openhands/server/services/my_service.py
from openhands.server.services.base import Service

class MyService(Service):
    def __init__(self, config):
        self.config = config
        
    async def initialize(self):
        # Setup service
        pass
        
    async def handle_request(self, request):
        # Process request
        return {"status": "success"}
```

2. Register the service:
```python
# openhands/server/services/__init__.py
from .my_service import MyService

def register_services(app):
    service = MyService(app.config)
    app.add_service("my_service", service)
```

## Testing Your Changes

### 1. Unit Tests

Create tests in the `tests/unit` directory:

```python
# tests/unit/test_my_agent.py
import pytest
from openhands.agenthub.my_agent import MyAgent

def test_agent_initialization():
    agent = MyAgent({})
    assert agent.name == "my_agent"

@pytest.mark.asyncio
async def test_agent_processing():
    agent = MyAgent({})
    result = await agent.process({"input": "test"})
    assert result["status"] == "success"
```

### 2. Running Tests

```bash
# Run all unit tests
poetry run pytest ./tests/unit/test_*.py

# Run specific test file
poetry run pytest ./tests/unit/test_my_agent.py

# Run with coverage
poetry run pytest --cov=openhands ./tests/unit/
```

### 3. Integration Testing

For integration tests, use the test client:

```python
# tests/integration/test_my_agent_integration.py
from fastapi.testclient import TestClient
from openhands.server.app import app

client = TestClient(app)

def test_agent_endpoint():
    response = client.post("/api/agent/my_agent", json={"input": "test"})
    assert response.status_code == 200
    assert response.json()["status"] == "success"
```

## Best Practices

1. **Code Organization**
   - Keep related functionality together
   - Use clear, descriptive names
   - Follow Python naming conventions

2. **Error Handling**
   - Use appropriate exception types
   - Provide meaningful error messages
   - Handle edge cases gracefully

3. **Documentation**
   - Document public APIs
   - Include usage examples
   - Explain complex logic

4. **Testing**
   - Write unit tests for new functionality
   - Include integration tests for APIs
   - Test edge cases and error conditions

5. **Performance**
   - Use async/await for I/O operations
   - Implement proper resource cleanup
   - Consider memory usage

Remember to run the linter before submitting changes:
```bash
make lint
```

This will ensure your code follows the project's style guidelines.