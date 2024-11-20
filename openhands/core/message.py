from enum import Enum
from typing import Literal
import uuid
import json

from litellm import ChatCompletionMessageToolCall
from pydantic import BaseModel, Field, model_serializer


class ContentType(Enum):
    TEXT = 'text'
    IMAGE_URL = 'image_url'
    TOOL_CALL = 'tool_call'
    TOOL_RESPONSE = 'tool_response'


class Content(BaseModel):
    type: str
    cache_prompt: bool = False

    @model_serializer
    def serialize_model(self):
        raise NotImplementedError('Subclasses should implement this method.')


class TextContent(Content):
    type: str = ContentType.TEXT.value
    text: str

    @model_serializer
    def serialize_model(self):
        data: dict[str, str | dict[str, str]] = {
            'type': self.type,
            'text': self.text,
        }
        if self.cache_prompt:
            data['cache_control'] = {'type': 'ephemeral'}
        return data


class ImageContent(Content):
    type: str = ContentType.IMAGE_URL.value
    image_urls: list[str]

    @model_serializer
    def serialize_model(self):
        images: list[dict[str, str | dict[str, str]]] = []
        for url in self.image_urls:
            images.append({'type': self.type, 'image_url': {'url': url}})
        if self.cache_prompt and images:
            images[-1]['cache_control'] = {'type': 'ephemeral'}
        return images


class ToolCallContent(Content):
    """Represents a tool call from the LLM to be executed"""
    type: str = ContentType.TOOL_CALL.value
    function_name: str
    function_arguments: str  # JSON string to match OpenAI's format
    tool_call_id: str = Field(default_factory=lambda: f"{uuid.uuid4()}")

    @model_serializer
    def serialize_model(self):
        # For native function calling format
        return {
            'type': self.type,
            'tool_calls': [{
                'id': self.tool_call_id,
                'type': 'function',
                'function': {
                    'name': self.function_name,
                    'arguments': self.function_arguments
                }
            }]
        }

    def to_string_format(self) -> str:
        """Convert to the XML-like format for non-native function calling"""
        ret = f"<function={self.function_name}>\n"
        try:
            args = json.loads(self.function_arguments)
            for param_name, param_value in args.items():
                is_multiline = isinstance(param_value, str) and '\n' in param_value
                ret += f'<parameter={param_name}>'
                if is_multiline:
                    ret += '\n'
                ret += f'{param_value}'
                if is_multiline:
                    ret += '\n'
                ret += '</parameter>\n'
        except json.JSONDecodeError as e:
            raise FunctionCallConversionError(
                f"Failed to parse arguments as JSON. Arguments: {self.function_arguments}"
            ) from e
        ret += '</function>'
        return ret


class ToolResponseContent(Content):
    """Represents a tool response back to the LLM"""
    type: str = ContentType.TOOL_RESPONSE.value
    tool_call_id: str
    name: str  # name of the tool that was called
    content: str  # The actual response content

    @model_serializer
    def serialize_model(self):
        # Tool responses are always serialized at the message level
        # with tool_call_id and name
        return {
            'type': self.type,
            'content': self.content,
        }

    def to_string_format(self) -> str:
        """Convert to the format for non-native function calling"""
        return f"EXECUTION RESULT of [{self.name}]:\n{self.content}"


class Message(BaseModel):
    role: Literal['user', 'system', 'assistant', 'tool']
    content: list[TextContent | ImageContent | ToolCallContent | ToolResponseContent] = Field(default_factory=list)
    cache_enabled: bool = False
    vision_enabled: bool = False
    function_calling_enabled: bool = False
    
    # Tool call fields at message level, as per API spec
    tool_calls: list[ChatCompletionMessageToolCall] | None = None
    tool_call_id: str | None = None
    name: str | None = None

    @property
    def contains_image(self) -> bool:
        return any(isinstance(content, ImageContent) for content in self.content)

    @model_serializer
    def serialize_model(self) -> dict:
        if self.function_calling_enabled:
            return self._native_serializer()
        return self._string_serializer()

    def _string_serializer(self) -> dict:
        """For non-native function calling, everything becomes text in content"""
        content_parts = []
        
        for item in self.content:
            if isinstance(item, TextContent):
                content_parts.append(item.text)
            elif isinstance(item, ToolCallContent):
                content_parts.append(item.to_string_format())
            elif isinstance(item, ToolResponseContent):
                content_parts.append(item.to_string_format())
            # Skip ImageContent in string format
        
        return {
            'role': self.role,
            'content': '\n'.join(content_parts)
        }

    def _native_serializer(self) -> dict:
        """For native function calling, use message-level fields for tools"""
        message_dict: dict = {'role': self.role}

        # Handle tool calls
        tool_call_content = next((c for c in self.content if isinstance(c, ToolCallContent)), None)
        if tool_call_content:
            message_dict['content'] = None  # Tool calls have null content
            message_dict['tool_calls'] = [{
                'id': tool_call_content.tool_call_id,
                'type': 'function',
                'function': {
                    'name': tool_call_content.function_name,
                    'arguments': tool_call_content.function_arguments
                }
            }]
            return message_dict

        # Handle tool responses
        tool_response_content = next((c for c in self.content if isinstance(c, ToolResponseContent)), None)
        if tool_response_content:
            message_dict['content'] = tool_response_content.content
            message_dict['tool_call_id'] = tool_response_content.tool_call_id
            message_dict['name'] = tool_response_content.name
            return message_dict

        # Handle regular content
        content = []
        for item in self.content:
            serialized = item.serialize_model()
            if isinstance(item, ImageContent):
                content.extend(serialized)
            else:
                content.append(serialized)
        message_dict['content'] = content

        return message_dict
