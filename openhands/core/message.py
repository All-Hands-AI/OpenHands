from enum import Enum
from typing import Literal

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
    role: Literal['user', 'system', 'assistant']
    content: list[TextContent | ImageContent] = Field(default=list)

    @property
    def contains_image(self) -> bool:
        return any(isinstance(content, ImageContent) for content in self.content)

    @model_serializer
    def serialize_model(self) -> dict:
        content: list[dict] | str
        if self.role == 'system':
            # For system role, concatenate all text content into a single string
            content = '\n'.join(
                item.text for item in self.content if isinstance(item, TextContent)
            )
        elif self.role == 'assistant' and not self.contains_image:
            # For assistant role without vision, concatenate all text content into a single string
            content = '\n'.join(
                item.text for item in self.content if isinstance(item, TextContent)
            )
        else:
            # For user role or assistant role with vision enabled, serialize each content item
            content = []
            for item in self.content:
                if isinstance(item, TextContent):
                    content.append(item.model_dump())
                elif isinstance(item, ImageContent):
                    content.extend(item.model_dump())

        return {'content': content, 'role': self.role}
