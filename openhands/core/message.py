from enum import Enum
from typing import Literal

from litellm import ChatCompletionMessageToolCall
from pydantic import BaseModel, Field, model_serializer


class ContentType(Enum):
    TEXT = 'text'
    IMAGE_URL = 'image_url'


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


class Message(BaseModel):
    role: Literal['user', 'system', 'assistant', 'tool']
    content: list[TextContent | ImageContent] = Field(default_factory=list)
    cache_enabled: bool = False
    vision_enabled: bool = False
    # function calling
    # - tool calls (from LLM)
    tool_calls: list[ChatCompletionMessageToolCall] | None = None
    # - tool execution result (to LLM)
    tool_call_id: str | None = None
    name: str | None = None  # name of the tool

    @property
    def contains_image(self) -> bool:
        return any(isinstance(content, ImageContent) for content in self.content)

    @model_serializer
    def serialize_model(self) -> dict:
        content: list[dict] = []
        role_tool_with_prompt_caching = False
        for item in self.content:
            d = item.model_dump()
            # We have to remove cache_prompt for tool content and move it up to the message level
            # See discussion here for details: https://github.com/BerriAI/litellm/issues/6422#issuecomment-2438765472
            if self.role == 'tool' and item.cache_prompt:
                role_tool_with_prompt_caching = True
                d.pop('cache_control')
            if isinstance(item, TextContent):
                content.append(d)
            elif isinstance(item, ImageContent) and self.vision_enabled:
                content.extend(d)

        ret: dict = {'content': content, 'role': self.role}

        if role_tool_with_prompt_caching:
            ret['cache_control'] = {'type': 'ephemeral'}

        if self.tool_call_id is not None:
            assert (
                self.name is not None
            ), 'name is required when tool_call_id is not None'
            ret['tool_call_id'] = self.tool_call_id
            ret['name'] = self.name
        if self.tool_calls:
            ret['tool_calls'] = self.tool_calls
        return ret
