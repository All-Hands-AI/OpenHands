from typing import Any, List, Optional

from pydantic import BaseModel, Field


class FileWithSpans(BaseModel):
    file_path: str = Field(
        description='The file path where the relevant code is found.'
    )
    span_ids: List[str] = Field(
        default_factory=list,
        description='The span ids of the relevant code in the file',
    )

    def add_span_id(self, span_id):
        if span_id not in self.span_ids:
            self.span_ids.append(span_id)

    def add_span_ids(self, span_ids: List[str]):
        for span_id in span_ids:
            self.add_span_id(span_id)


class ActionRequest(BaseModel):
    pass

    @property
    def action_name(self):
        return self.__class__.__name__


class EmptyRequest(ActionRequest):
    pass


class Finish(ActionRequest):
    thoughts: str = Field(..., description='The reason to finishing the request.')


class Reject(ActionRequest):
    thoughts: str = Field(..., description='The reason for rejecting the request.')


class Content(ActionRequest):
    content: str


class Message(BaseModel):
    role: str
    content: Optional[str] = None
    action: Optional[ActionRequest] = Field(default=None)


class AssistantMessage(Message):
    role: str = 'assistant'
    content: Optional[str] = None
    action: Optional[ActionRequest] = Field(default=None)


class UserMessage(Message):
    role: str = 'user'
    content: Optional[str] = None


class ActionResponse(BaseModel):
    trigger: Optional[str] = None
    output: Optional[dict[str, Any]] = None
    retry_message: Optional[str] = None

    @classmethod
    def retry(cls, retry_message: str):
        return cls(trigger='retry', retry_message=retry_message)

    @classmethod
    def transition(cls, trigger: str, output: Optional[dict[str, Any]] = None):
        output = output or {}
        return cls(trigger=trigger, output=output)

    @classmethod
    def no_transition(cls, output: dict[str, Any]):
        return cls(output=output)


class Response(BaseModel):
    status: str
    message: str
