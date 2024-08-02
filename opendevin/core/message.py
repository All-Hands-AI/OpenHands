from enum import Enum

from pydantic import BaseModel, Field, model_serializer
from typing_extensions import Literal


class ContentType(Enum):
    TEXT = 'text'
    IMAGE_URL = 'image_url'


class Content(BaseModel):
    type: ContentType

    @model_serializer
    def serialize_model(self):
        raise NotImplementedError('Subclasses should implement this method.')


class TextContent(Content):
    type: ContentType = ContentType.TEXT
    text: str

    @model_serializer
    def serialize_model(self):
        return {'type': self.type.value, 'text': self.text}


class ImageContent(Content):
    type: ContentType = ContentType.IMAGE_URL
    image_urls: list[str]

    @model_serializer
    def serialize_model(self):
        images: list[dict[str, str | dict[str, str]]] = []
        for url in self.image_urls:
            images.append({'type': self.type.value, 'image_url': {'url': url}})
        return images


class Message(BaseModel):
    role: Literal['user', 'system', 'assistant']
    content: list[TextContent | ImageContent] = Field(default=list)

    @property
    def contains_image(self) -> bool:
        return any(isinstance(content, ImageContent) for content in self.content)

    @model_serializer
    def serialize_model(self) -> dict:
        content: list[dict[str, str | dict[str, str]]] = []

        for item in self.content:
            if isinstance(item, TextContent):
                content.append(item.model_dump())
            elif isinstance(item, ImageContent):
                content.extend(item.model_dump())

        return {'role': self.role, 'content': content}
