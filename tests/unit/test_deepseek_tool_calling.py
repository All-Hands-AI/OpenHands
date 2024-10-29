import pytest
from openhands.core.config import LLMConfig
from openhands.core.message import Message, TextContent
from openhands.llm.llm import LLM

def test_deepseek_tool_calling_message_serialization():
    # Create a message with tool calls
    message = Message(
        role="assistant",
        content=[TextContent(text="Let me help you with that.")],
        tool_calls=[{
            "id": "call_123",
            "type": "function",
            "function": {
                "name": "test_function",
                "arguments": '{"arg1": "value1"}'
            }
        }]
    )
    
    # Verify serialization
    serialized = message.model_dump()
    assert "tool_calls" in serialized
    assert isinstance(serialized["content"], str)
    assert serialized["tool_calls"][0]["id"] == "call_123"
    assert serialized["tool_calls"][0]["function"]["name"] == "test_function"

def test_deepseek_model_supports_function_calling():
    config = LLMConfig(model="deepseek-chat")
    llm = LLM(config)
    assert llm.config.supports_function_calling is True
