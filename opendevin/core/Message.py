from typing import List, Optional

from pydantic import BaseModel, Field, model_serializer
from typing_extensions import Literal


class Message(BaseModel):
    role: Literal['user', 'system']
    image_urls: Optional[List[str]] = Field(default=None)
    text: str

    @property
    def contains_image(self) -> bool:
        return bool(self.image_urls and len(self.image_urls) > 0)

    @model_serializer
    def serialize_model(self) -> dict:
        content: list[dict[str, str | dict[str, str]]] = [
            {
                'type': 'text',
                'text': self.text,
            }
        ]

        if self.contains_image and self.image_urls:
            for url in self.image_urls:
                content.append({'type': 'image_url', 'image_url': {'url': url}})

        return {'role': self.role, 'content': content}


# # Example usage
# message = Message(
#     role="user",
#     text="What’s in this image?",
#     image_urls=["https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg"]
# )

# # Using model_dump to call the custom serializer
# serialized_message = message.model_dump()
# print(serialized_message)
