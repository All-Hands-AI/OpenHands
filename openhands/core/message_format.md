# OpenHands Message Format and litellm Integration

## Overview

OpenHands uses its own `Message` class (`openhands/core/message.py`) which provides rich content support while maintaining compatibility with litellm's message handling system.

## Class Structure

Our `Message` class (`openhands/core/message.py`):
```python
class Message(BaseModel):
    role: Literal['user', 'system', 'assistant', 'tool']
    content: list[TextContent | ImageContent] = Field(default_factory=list)
    cache_enabled: bool = False
    vision_enabled: bool = False
    condensable: bool = True
    function_calling_enabled: bool = False
    tool_calls: list[ChatCompletionMessageToolCall] | None = None
    tool_call_id: str | None = None
    name: str | None = None
    event_id: int = -1
```

litellm's `Message` class (`litellm/types/utils.py`):
```python
class Message(OpenAIObject):
    content: Optional[str]
    role: Literal["assistant", "user", "system", "tool", "function"]
    tool_calls: Optional[List[ChatCompletionMessageToolCall]]
    function_call: Optional[FunctionCall]
    audio: Optional[ChatCompletionAudioResponse] = None
```

## How It Works

1. **Message Creation**: Our `Message` class is a Pydantic model that supports rich content (text and images) through its `content` field.

2. **Serialization**: The class uses Pydantic's `@model_serializer` to convert messages into dictionaries that litellm can understand:
   ```python
   @model_serializer
   def serialize_model(self) -> dict:
       if self.cache_enabled or self.vision_enabled or self.function_calling_enabled:
           return self._list_serializer()
       return self._string_serializer()
   ```

3. **litellm Integration**: When we pass our messages to `litellm.completion()`, litellm doesn't care about the message class type - it works with the dictionary representation. This works because:
   - litellm's transformation code (e.g., `litellm/llms/anthropic/chat/transformation.py`) processes messages based on their structure, not their type
   - Our serialization produces dictionaries that match litellm's expected format
   - litellm handles rich content by looking at the message structure, supporting both simple string content and lists of content items

4. **Provider-Specific Handling**: litellm then transforms these messages into provider-specific formats (e.g., Anthropic, OpenAI) through its transformation layers, which know how to handle both simple and rich content structures.

## Key Points

- We don't need to inherit from litellm's `Message` class because litellm works with dictionary representations, not class types
- Our rich content model is more sophisticated than litellm's basic string content, but litellm handles it correctly through its transformation layers
- The compatibility is maintained through proper serialization rather than inheritance