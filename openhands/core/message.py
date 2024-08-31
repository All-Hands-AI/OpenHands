from enum import Enum
from typing import Union

from pydantic import BaseModel, Field, model_serializer
from typing_extensions import Literal


class ContentType(Enum):
    TEXT = 'text'
    IMAGE_URL = 'image_url'


class Content(BaseModel):
    type: ContentType
    cache_prompt: bool = False

    @model_serializer
    def serialize_model(self):
        raise NotImplementedError('Subclasses should implement this method.')


class TextContent(Content):
    type: ContentType = ContentType.TEXT
    text: str

    @model_serializer
    def serialize_model(self):
        data: dict[str, str | dict[str, str]] = {
            'type': self.type.value,
            'text': self.text,
        }
        if self.cache_prompt:
            data['cache_control'] = {'type': 'ephemeral'}
        return data


class ImageContent(Content):
    type: ContentType = ContentType.IMAGE_URL
    image_urls: list[str]

    @model_serializer
    def serialize_model(self):
        images: list[dict[str, str | dict[str, str]]] = []
        for url in self.image_urls:
            images.append({'type': self.type.value, 'image_url': {'url': url}})
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
        content: list[dict[str, str | dict[str, str]]] = []

        for item in self.content:
            if isinstance(item, TextContent):
                content.append(item.model_dump())
            elif isinstance(item, ImageContent):
                content.extend(item.model_dump())

        return {'role': self.role, 'content': content}

    @staticmethod
    def format_messages(
        messages: Union['Message', 'list[Message]'], with_images: bool
    ) -> list[dict]:
        if not isinstance(messages, list):
            messages = [messages]

        if with_images:
            return [message.model_dump() for message in messages]

        formatted_messages = []
        for message in messages:
            if isinstance(message, dict):
                # If it's already a dict, just extract the content
                content = message.get('content', '')
                if isinstance(content, list):
                    # If content is a list, join the text parts
                    formatted_content = ''.join(
                        item.get('text', '')
                        for item in content
                        if item.get('type') == 'text'
                    )
                else:
                    formatted_content = content
            else:
                # If it's a Message object, process as before
                formatted_content = ''
                for content in message.content:
                    if isinstance(content, TextContent):
                        formatted_content += content.text

            formatted_messages.append(
                {
                    'role': message['role']
                    if isinstance(message, dict)
                    else message.role,
                    'content': formatted_content,
                }
            )

        return formatted_messages
