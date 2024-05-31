from typing import Any, Literal

import requests
from pydantic import BaseModel


class FeedbackDataModel(BaseModel):
    email: str
    token: str
    feedback: Literal['positive', 'negative']
    permissions: Literal['public', 'private']
    trajectory: list[dict[str, Any]]


FEEDBACK_URL = (
    'https://kttkfkoju5.execute-api.us-east-2.amazonaws.com/od-share-trajectory'
)


def store_feedback(feedback: FeedbackDataModel):
    response = requests.post(
        FEEDBACK_URL,
        headers={'Content-Type': 'application/json'},
        json=feedback.model_dump_json(),
    )
    if response.status_code != 200:
        raise ValueError(f'Failed to store feedback: {response.text}')
