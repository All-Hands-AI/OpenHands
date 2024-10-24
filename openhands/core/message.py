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
    content: list[TextContent | ImageContent] = Field(default=list)
    cache_enabled: bool = False
    vision_enabled: bool = False
    # function calling
    # - tool calls (from LLM)
    tool_calls: list[ChatCompletionMessageToolCall] = Field(default=list)
    # - tool execution result (to LLM)
    tool_call_id: str | None = None
    name: str | None = None  # name of the tool

    @property
    def contains_image(self) -> bool:
        return any(isinstance(content, ImageContent) for content in self.content)

    @model_serializer
    def serialize_model(self) -> dict:
        content: list[dict] | str
        # two kinds of serializer:
        # 1. vision serializer: when prompt caching or vision is enabled
        # 2. single text serializer: for other cases
        # remove this when liteLLM or providers support this format translation
        if self.cache_enabled or self.vision_enabled:
            # when prompt caching or vision is enabled, use vision serializer
            content = []
            for item in self.content:
                if isinstance(item, TextContent):
                    content.append(item.model_dump())
                elif isinstance(item, ImageContent):
                    content.extend(item.model_dump())
        else:
            # for other cases, concatenate all text content
            # into a single string per message
            content = '\n'.join(
                item.text for item in self.content if isinstance(item, TextContent)
            )

        # FIXME: temporary workaround for LiteLLM tool output bug
        # https://github.com/BerriAI/litellm/issues/6422
        if self.tool_calls and isinstance(content, list):
            # assert no image content in the list
            assert all(
                isinstance(item, TextContent) for item in self.content
            ), f'Expected all text content in tool calls due to https://github.com/BerriAI/litellm/issues/6422. Got: {self.content}'
            # merge the content list into a single string
            content = '\n'.join(item.text for item in self.content)

        ret = {'content': content, 'role': self.role}

        if self.tool_call_id is not None:
            assert (
                self.name is not None
            ), 'name is required when tool_call_id is not None'
            ret['tool_call_id'] = self.tool_call_id
            ret['name'] = self.name
        if self.tool_calls:
            ret['tool_calls'] = self.tool_calls
        return ret
