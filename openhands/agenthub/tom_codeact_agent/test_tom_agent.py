#!/usr/bin/env python3
"""
Test script for TomCodeActAgent and sleeptime processing
Usage: python test_tom_agent.py "Your custom instruction here"
"""

import asyncio
import sys
import tempfile
import os
import shutil
from pathlib import Path
from typing import List

# Add the project root to the Python path
project_root = Path(__file__).parents[3]
sys.path.insert(0, str(project_root))

# Import the tom agent to register it
import openhands.agenthub.tom_codeact_agent

from openhands.core.config import OpenHandsConfig, AgentConfig, LLMConfig, load_from_toml
from openhands.core.setup import create_agent, create_runtime
from openhands.events.action import MessageAction
from openhands.events import EventSource
from openhands.runtime.impl.local import LocalRuntime
from openhands.controller.state.state import State
from openhands.llm.metrics import Metrics
# Removed sleeptime import since it's now integrated into TomCodeActAgent

async def test_tom_agent(instruction: str, workspace_dir: str = None):
    """Test TomCodeActAgent with a custom instruction."""
    print("\n=== Testing TomCodeActAgent ===")

    # Create a workspace in .cache folder if none provided
    if workspace_dir is None:
        cache_dir = project_root / ".cache" / "tom_agent_test"
        cache_dir.mkdir(parents=True, exist_ok=True)
        workspace_dir = str(cache_dir)
        print(f"Using cache workspace: {workspace_dir}")

    # Configure the agent with browser disabled and Tom settings
    config = OpenHandsConfig(
        default_agent="TomCodeActAgent",
        workspace_base=workspace_dir,
        runtime="local",
        max_iterations=10,  # Keep it short for testing
        disable_color=True,  # Disable colors for cleaner output
        enable_browser=False,  # Disable browser to avoid browser setup issues
    )

    # Configure Tom settings via agent config
    config.sandbox.browsergym_eval_env = None

    # Load LLM configuration from config.toml
    config_path = project_root / "config.toml"
    if config_path.exists():
        load_from_toml(config, str(config_path))
        print(f"Loaded LLM config from {config_path}")
    else:
        print("Warning: config.toml not found, using default LLM config")

    runtime = None
    try:
        # Create the agent
        agent = create_agent(config)
        print(f"Created agent: {agent.__class__.__name__}")

        # Create local runtime
        runtime = create_runtime(config, sid="test_session")
        await runtime.connect()
        print("Runtime connected")

        # Create initial user message
        user_message = MessageAction(content=instruction)

        # Add the message to the event stream
        runtime.event_stream.add_event(user_message, EventSource.USER)

        print(f"\n🤖 Starting TomCodeAct Agent with instruction:")
        print(f"📝 {instruction}")
        print(f"📁 Workspace: {workspace_dir}")
        print("-" * 60)

        # Simple interaction loop
        max_steps = 5  # Reduced for testing
        for step in range(max_steps):
            print(f"\n--- Step {step + 1} ---")

            # Create a proper state object with event history
            all_events = list(runtime.event_stream.get_events())  # Convert to list
            # Filter out NullObservation to avoid conversation memory errors
            from openhands.events.observation.empty import NullObservation
            events = [event for event in all_events if not isinstance(event, NullObservation)]
            print(f"Filtered out {len(all_events) - len(events)} null observations from {len(all_events)} total events")
            state = State(
                budget_flag=False,
                metrics=Metrics(),
                history=events  # Add the event history so agent can find initial message
            )

            # Let the agent process and take an action
            try:
                action = agent.step(state)
            except Exception as e:
                print(f"⚠️ Agent step failed: {e}")
                break

            if action is None:
                print("Agent returned no action")
                break

            print(f"Agent action: {action.__class__.__name__}")
            if hasattr(action, 'content'):
                print(f"Content: {action.content[:200]}...")
            # Add the action to the event stream
            runtime.event_stream.add_event(action, EventSource.AGENT)

            # Execute the action in the runtime
            observation = runtime.run_action(action)

            if observation:
                print(f"Observation: {observation.__class__.__name__}")
                if hasattr(observation, 'content'):
                    content = str(observation.content)
                    print(f"Result: {content[:200]}...")

                # Add observation to event stream
                runtime.event_stream.add_event(observation, EventSource.ENVIRONMENT)

            # Handle MessageActions by asking for user input
            if action.__class__.__name__ == "MessageAction":
                print(f"\n🤖 Agent: {action.content}")
                user_input = input("\n👤 Your response: ").strip()
                if user_input:
                    # Create a new user message and add it to the event stream
                    new_user_message = MessageAction(content=user_input)
                    runtime.event_stream.add_event(new_user_message, EventSource.USER)
                    print(f"✅ Added your response to conversation")

            # Check if agent is finished
            if action.__class__.__name__ == "AgentFinishAction":
                print("\n✅ Agent finished!")
                if hasattr(action, 'outputs'):
                    print(f"Final output: {action.outputs}")
                break
        else:
            print(f"\n⏰ Reached maximum steps ({max_steps})")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Cleanup
        if runtime:
            await runtime.close()
        print(f"\n📂 Results saved in: {workspace_dir}")


def main():
    """Main function to run the tests."""
    # Then run agent test if arguments provided
    if len(sys.argv) > 1:
        instruction = " ".join(sys.argv[1:])
        # You can optionally specify a workspace directory
        workspace_dir = None
        if os.path.isdir(sys.argv[-1]):
            workspace_dir = sys.argv[-1]
            instruction = " ".join(sys.argv[1:-1])
        asyncio.run(test_tom_agent(instruction, workspace_dir))
    else:
        print("\nSkipping agent test (no instruction provided)")
        print("To test agent, run: python test_tom_agent.py \"Your instruction here\"")


if __name__ == "__main__":
    main()
