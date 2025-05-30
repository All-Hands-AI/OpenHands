# Using OpenHands as a library


## Hello World
```python
import asyncio
from openhands.core.config import OpenHandsConfig, LLMConfig, AgentConfig
from openhands.core.setup import run_agent

async def run_openhands_agent():
    final_state = await run_agent(
        config=OpenHandsConfig(
            llm=LLMConfig(
                model="claude-sonnet-4-20250514",
                api_key="your_api_key_here",  # Replace with your actual API key
            ),
        ),
        initial_user_message="Flip a coin",
        context_message="You build simple programs and run them.",
    )

    return final_state

# Run the async function
if __name__ == "__main__":
    final_state = asyncio.run(run_openhands_agent())
    print("Agent execution completed!")
```

## Using the internals

```python
import asyncio
from openhands.controller.agent import Agent
from openhands.core.config import OpenHandsConfig, LLMConfig, AgentConfig
from openhands.events.action import MessageAction
from openhands.llm.llm import LLM
from openhands.core.setup import (
    create_runtime,
    create_memory,
    generate_sid,
)
from openhands.core.main import run_controller

async def run_openhands_agent():
    config = OpenHandsConfig(
        runtime="local",
        file_store="memory",
        llm=LLMConfig(
            model="claude-sonnet-4-20250514",  # Choose your preferred model
            api_key="your_api_key_here",  # Replace with your actual API key
            temperature=0.0,  # Set temperature to 0 for deterministic output
        ),
        agent=AgentConfig(
            enable_browsing=False,
        ),
    )

    oh = OpenHands(config=config)

    conversation = oh.create_conversation(
        conversation_id='hello-world',
    )
    await conversation.runtime.connect()

    def on_event(event: Event) -> None:
        print(f"Event received: {event}")
    conversation.event_stream.subscribe(EventStreamSubscriber.MAIN, on_event)

    initial_user_action = MessageAction(content="Flip a coin")
    conversation.event_stream.add_event(initial_user_action, EventSource.USER)

    while conversation.state.agent_state not in end_states:
        await asyncio.sleep(1)

    await runtime.close()

    return conversation.state

# Run the async function
if __name__ == "__main__":
    final_state = asyncio.run(run_openhands_agent())
    print("Agent execution completed!")
```
