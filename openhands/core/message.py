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
    # NOTE: this is not the same as EventSource
    # These are the roles in the LLM's APIs
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
        # We need two kinds of serializations:
        # - into a single string: for providers that don't support list of content items (e.g. no vision, no tool calls)
        # - into a list of content items: the new APIs of providers with vision/prompt caching/tool calls
        # NOTE: remove this when litellm or providers support the new API
        if (
            self.cache_enabled
            or self.vision_enabled
            or self.tool_call_id is not None
            or self.tool_calls is not None
        ):
            return self._list_serializer()
        return self._string_serializer()

    def _string_serializer(self):
        content = '\n'.join(
            item.text for item in self.content if isinstance(item, TextContent)
        )
        return {'content': content, 'role': self.role}

    def _list_serializer(self):
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
        # pop content if it's empty
        if not content or (
            len(content) == 1
            and content[0]['type'] == 'text'
            and content[0]['text'] == ''
        ):
            ret.pop('content')

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
