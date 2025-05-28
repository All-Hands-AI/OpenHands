# Using OpenHands as a Library

OpenHands can be used as a Python library in your own applications. This guide will show you how to integrate OpenHands into your Python projects, allowing you to build custom applications that leverage OpenHands' powerful agent capabilities.

## Installation

First, install the OpenHands library from PyPI:

```bash
pip install openhands-ai
```

## Basic Usage

Here's a simple example of how to use OpenHands in your Python code:

```python
import asyncio
from openhands.controller.agent import Agent
from openhands.core.config import AppConfig, LLMConfig, AgentConfig
from openhands.events.action import MessageAction
from openhands.llm.llm import LLM
from openhands.core.setup import (
    create_runtime,
    create_memory,
    generate_sid,
)
from openhands.core.main import run_controller

async def run_openhands_agent():
    # 1. Create configuration
    config = AppConfig(
        runtime="local",  # Use local runtime
        file_store="memory",  # Store events in memory
    )
    
    # 2. Configure LLM
    llm_config = LLMConfig(
        model="claude-sonnet-4-20250514",  # Choose your preferred model
        api_key="your_api_key_here",  # Replace with your actual API key
        temperature=0.0,
    )
    config.set_llm_config(llm_config)
    
    # 3. Configure Agent
    agent_config = AgentConfig(
        enable_browsing=False,  # Disable browsing for this example
    )
    config.set_agent_config(agent_config)
    
    # 4. Create Agent
    agent = Agent(
        llm=LLM(config=llm_config),
        config=agent_config,
    )
    
    # 5. Generate a session ID
    sid = generate_sid(config)
    
    # 6. Create Runtime
    runtime = create_runtime(
        config=config,
        sid=sid,
        headless_mode=True,
        agent=agent,
    )
    
    # 7. Connect to the runtime
    await runtime.connect()
    
    # 8. Create Memory
    memory = create_memory(
        runtime=runtime,
        event_stream=runtime.event_stream,
        sid=sid,
    )
    
    # 9. Define the initial task
    initial_user_action = MessageAction(content="Write a Python function that calculates the factorial of a number")
    
    # 10. Run the agent
    final_state = await run_controller(
        config=config,
        initial_user_action=initial_user_action,
        sid=sid,
        runtime=runtime,
        agent=agent,
        memory=memory,
        headless_mode=True,
        exit_on_message=True,  # Exit when the agent asks for user input
    )
    
    # 11. Close the runtime
    await runtime.close()
    
    return final_state

# Run the async function
if __name__ == "__main__":
    final_state = asyncio.run(run_openhands_agent())
    print("Agent execution completed!")
```

## Components Overview

### AppConfig

The `AppConfig` class is the main configuration object for OpenHands. It contains settings for the runtime, agent, LLM, and more.

```python
from openhands.core.config import AppConfig

config = AppConfig(
    runtime="local",  # Options: "local", "docker", "e2b", "modal", etc.
    file_store="memory",  # Options: "memory", "local", etc.
    file_store_path="/path/to/store",  # Only needed for "local" file_store
    max_iterations=100,  # Maximum number of agent iterations
)
```

### LLMConfig

The `LLMConfig` class configures the language model used by the agent.

```python
from openhands.core.config import LLMConfig

llm_config = LLMConfig(
    model="claude-sonnet-4-20250514",  # Model name
    api_key="your_api_key_here",  # API key
    temperature=0.0,  # Temperature for generation
    max_output_tokens=4096,  # Maximum tokens in the response
)
```

### AgentConfig

The `AgentConfig` class configures the agent's behavior and available tools.

```python
from openhands.core.config import AgentConfig

agent_config = AgentConfig(
    enable_browsing=True,  # Enable web browsing
    enable_cmd=True,  # Enable bash commands
    enable_editor=True,  # Enable file editing
    enable_jupyter=True,  # Enable Jupyter notebook
    enable_think=True,  # Enable thinking tool
    enable_finish=True,  # Enable finish tool
)
```

### Agent

The `Agent` class represents the AI agent that will perform tasks.

```python
from openhands.controller.agent import Agent
from openhands.llm.llm import LLM

agent = Agent(
    llm=LLM(config=llm_config),
    config=agent_config,
)
```

### Runtime

The runtime is the environment where the agent executes commands and interacts with the system.

```python
from openhands.core.setup import create_runtime

runtime = create_runtime(
    config=config,
    sid=sid,
    headless_mode=True,
    agent=agent,
)
```

### Memory

The memory component manages the agent's context and conversation history.

```python
from openhands.core.setup import create_memory

memory = create_memory(
    runtime=runtime,
    event_stream=runtime.event_stream,
    sid=sid,
)
```

## Advanced Usage

### Custom Sandbox Configuration

You can customize the sandbox environment by configuring the `SandboxConfig`:

```python
from openhands.core.config import SandboxConfig

sandbox_config = SandboxConfig(
    selected_repo="username/repo",  # GitHub repository to clone
    base_image="ubuntu:22.04",  # Base Docker image
)
config.sandbox = sandbox_config
```

### Security Configuration

Configure security settings using the `SecurityConfig`:

```python
from openhands.core.config import SecurityConfig

security_config = SecurityConfig(
    confirmation_mode=False,  # Whether to require confirmation for actions
    security_analyzer="default",  # Security analyzer to use
)
config.security = security_config
```

### Custom Agent Response Handling

You can provide a custom function to handle agent responses:

```python
def custom_response_handler(state):
    # Process the agent's state and generate a response
    return "Continue with your current approach"

final_state = await run_controller(
    config=config,
    initial_user_action=initial_user_action,
    fake_user_response_fn=custom_response_handler,
)
```

## Building a Complete Application

Here's an example of a more complete application that uses OpenHands to assist with code generation:

```python
import asyncio
import os
from openhands.controller.agent import Agent
from openhands.core.config import AppConfig, LLMConfig, AgentConfig, SandboxConfig
from openhands.events.action import MessageAction
from openhands.llm.llm import LLM
from openhands.core.setup import create_runtime, create_memory, generate_sid
from openhands.core.main import run_controller
from openhands.events import EventStreamSubscriber
from openhands.events.observation import AgentStateChangedObservation
from openhands.core.schema import AgentState

class CodeAssistant:
    def __init__(self, api_key, model="claude-sonnet-4-20250514"):
        self.api_key = api_key
        self.model = model
        self.config = None
        self.agent = None
        self.runtime = None
        self.memory = None
        self.sid = None
        self.event_stream = None
        
    async def initialize(self):
        # Create configuration
        self.config = AppConfig(
            runtime="docker",
            file_store="memory",
        )
        
        # Configure LLM
        llm_config = LLMConfig(
            model=self.model,
            api_key=self.api_key,
            temperature=0.0,
        )
        self.config.set_llm_config(llm_config)
        
        # Configure Agent
        agent_config = AgentConfig(
            enable_browsing=True,
            enable_cmd=True,
            enable_editor=True,
            enable_jupyter=True,
        )
        self.config.set_agent_config(agent_config)
        
        # Configure Sandbox
        sandbox_config = SandboxConfig(
            base_image="ubuntu:22.04",
        )
        self.config.sandbox = sandbox_config
        
        # Create Agent
        self.agent = Agent(
            llm=LLM(config=llm_config),
            config=agent_config,
        )
        
        # Generate a session ID
        self.sid = generate_sid(self.config)
        
        # Create Runtime
        self.runtime = create_runtime(
            config=self.config,
            sid=self.sid,
            headless_mode=True,
            agent=self.agent,
        )
        
        # Connect to the runtime
        await self.runtime.connect()
        
        # Create Memory
        self.memory = create_memory(
            runtime=self.runtime,
            event_stream=self.runtime.event_stream,
            sid=self.sid,
        )
        
        self.event_stream = self.runtime.event_stream
        
    async def run_task(self, task_description, callback=None):
        # Define the initial task
        initial_user_action = MessageAction(content=task_description)
        
        # Set up event callback if provided
        if callback:
            def on_event(event):
                if isinstance(event, AgentStateChangedObservation):
                    callback(event)
            
            self.event_stream.subscribe(
                EventStreamSubscriber.MAIN, 
                on_event, 
                self.sid
            )
        
        # Run the agent
        final_state = await run_controller(
            config=self.config,
            initial_user_action=initial_user_action,
            sid=self.sid,
            runtime=self.runtime,
            agent=self.agent,
            memory=self.memory,
            headless_mode=True,
            exit_on_message=True,
        )
        
        return final_state
    
    async def close(self):
        if self.runtime:
            await self.runtime.close()

# Example usage
async def main():
    # Initialize the code assistant
    assistant = CodeAssistant(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    await assistant.initialize()
    
    # Define a callback to process events
    def event_callback(event):
        if isinstance(event, AgentStateChangedObservation):
            print(f"Agent state changed to: {event.agent_state}")
    
    # Run a task
    task = """
    Create a simple Flask API with the following endpoints:
    1. GET /users - Returns a list of users
    2. GET /users/{id} - Returns a specific user
    3. POST /users - Creates a new user
    
    Use SQLite as the database and implement proper error handling.
    """
    
    final_state = await assistant.run_task(task, callback=event_callback)
    
    # Close the assistant
    await assistant.close()
    
    print("Task completed!")

if __name__ == "__main__":
    asyncio.run(main())
```

## Conclusion

Using OpenHands as a library gives you the flexibility to integrate AI agents into your own applications. You can customize the agent's behavior, runtime environment, and how it interacts with your application.

For more advanced usage, refer to the OpenHands source code and API documentation. The library is highly customizable and can be adapted to a wide range of use cases.