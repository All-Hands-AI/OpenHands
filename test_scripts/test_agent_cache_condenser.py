#!/usr/bin/env python3
"""Test script for the LLMAgentCacheCondenser."""

import sys
from typing import List, cast

from openhands.agenthub.codeact_agent.codeact_agent import CodeActAgent
from openhands.controller.state.state import State
from openhands.core.config import AgentConfig, LLMConfig
from openhands.core.config.condenser_config import LLMAgentCacheCondenserConfig
from openhands.events.action.message import MessageAction
from openhands.events.event import Event
from openhands.events.observation.agent import AgentThinkObservation
from openhands.llm.llm import LLM
from openhands.memory.condenser.impl.llm_agent_cache_condenser import LLMAgentCacheCondenser


def create_test_conversation(num_messages: int = 20) -> List[Event]:
    """Create a test conversation with a specified number of messages."""
    events = []
    
    # Add initial user message
    events.append(MessageAction(content="Hello, I need help with a task."))
    
    # Add alternating agent and user messages
    for i in range(num_messages):
        if i % 2 == 0:
            # Agent message
            events.append(AgentThinkObservation(content=f"I'll help you with that. This is message {i}."))
        else:
            # User message
            events.append(MessageAction(content=f"Thanks, here's more information. This is message {i}."))
    
    return events


def test_agent_cache_condenser():
    """Test the LLMAgentCacheCondenser with a simulated conversation."""
    # Create an agent with the LLMAgentCacheCondenser
    config = AgentConfig()
    config.condenser = LLMAgentCacheCondenserConfig(
        type="agentcache",
        trigger_word="CONDENSE!",
        max_size=10
    )
    
    llm_config = LLMConfig(
        model="anthropic/claude-3-7-sonnet-20250219",
        api_key="YOUR_API_KEY_HERE",
        caching_prompt=True
    )
    
    agent = CodeActAgent(llm=LLM(llm_config), config=config)
    
    # Create a conversation
    events = create_test_conversation(num_messages=20)
    
    # Add a message with the trigger word
    events.append(AgentThinkObservation(content="Let me think about this. CONDENSE!"))
    
    state = State(history=cast(List[Event], events))
    
    # Get the condensed history
    condensed = agent.condenser.condensed_history(state)
    
    # Print results
    print(f"Original history length: {len(state.history)}")
    if hasattr(condensed, "action"):
        print(f"Condensation triggered: {condensed.action}")
        print(f"Summary: {condensed.action.summary}")
    else:
        print(f"Condensed history length: {len(condensed)}")
        print("No condensation triggered")


if __name__ == "__main__":
    test_agent_cache_condenser()