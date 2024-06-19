# import logging
# from typing import Any, Dict, List, Optional, Type

# from pydantic import BaseModel, Field, model_validator

# from .file_context import FileContext
# from .index.code_index import CodeIndex
# from .index.types import SearchCodeResponse
# from .settings import Settings
# from .types import (
#     ActionRequest,
#     ActionSpec,
#     FileWithSpans,
#     Reject,
# )

# logger = logging.getLogger(__name__)


# class SearchCodeRequest(ActionRequest):
#     file_pattern: Optional[str] = Field(
#         default=None,
#         description='A glob pattern to filter search results to specific file types or directories. ',
#     )
#     query: Optional[str] = Field(
#         default=None,
#         description='A semantic similarity search query. Use natural language to describe what you are looking for.',
#     )
#     code_snippet: Optional[str] = Field(
#         default=None,
#         description='Specific code snippet to that should be exactly matched.',
#     )
#     class_name: Optional[str] = Field(
#         default=None, description='Specific class name to include in the search.'
#     )
#     function_name: Optional[str] = Field(
#         default=None, description='Specific function name to include in the search.'
#     )

#     @model_validator(mode='after')
#     def check_at_least_one_field(self):
#         if (
#             not self.query
#             and not self.code_snippet
#             and not self.class_name
#             and not self.function_name
#         ):
#             raise ValueError(
#                 'At least one of query, code_snippet, class_name, or function_name must be set'
#             )
#         return self


# class SearchCodeAction(ActionSpec):
#     code_index: CodeIndex

#     @classmethod
#     def request_class(cls) -> Type[SearchCodeRequest]:
#         return SearchCodeRequest

#     @classmethod
#     def name(self) -> str:
#         return 'search'

#     @classmethod
#     def description(cls) -> str:
#         return 'Search for code.'

#     @classmethod
#     def validate_request(cls, args: Dict[str, Any]) -> SearchCodeRequest:
#         return cls.request_class().model_validate(args, strict=True)

#     def __init__(self, code_index: CodeIndex):
#         super().__init__(code_index=code_index)

#     def search(self, request: SearchCodeRequest) -> SearchCodeResponse:
#         return self.code_index.search(**request.dict())

#     class Config:
#         arbitrary_types_allowed = True


# class IdentifyCodeRequest(ActionRequest):
#     reasoning: str = Field(None, description='The reasoning for the code selection.')

#     files_with_spans: List[FileWithSpans] = Field(
#         default=None, description='The files and spans to select.'
#     )


# class IdentifyCode(ActionSpec):
#     @classmethod
#     def request_class(cls):
#         return IdentifyCodeRequest

#     @classmethod
#     def name(self):
#         return 'identify'

#     @classmethod
#     def description(cls) -> str:
#         return 'Identify the relevant code files and spans.'


# class FindCodeRequest(ActionRequest):
#     instructions: Optional[str] = Field(
#         default=None, description='Instructions to find code based on.'
#     )


# class FindCodeResponse(BaseModel):
#     message: Optional[str] = Field(None, description='A message to show the user.')
#     files: list[FileWithSpans] = Field(
#         default_factory=list, description='The files and spans found.'
#     )


# class ActionCallWithContext(BaseModel):
#     call_id: str
#     action_name: str
#     arguments: dict
#     file_context: FileContext
#     message: Optional[str] = None

#     class Config:
#         arbitrary_types_allowed = True


# class LoopState(BaseModel):
#     def model(self) -> str:
#         return Settings.agent_model

#     def temperature(self) -> float:
#         return 0.0

#     def tools(self) -> list[Type[ActionSpec]]:
#         return []

#     def stop_words(self):
#         return []

#     def max_tokens(self):
#         return 1000


# class Searching(LoopState):
#     def tools(self) -> list[Type[ActionSpec]]:
#         return [SearchCodeAction, IdentifyCode, Reject]

import logging
from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel, Field, model_validator

from .file_context import FileContext
from .index.code_index import CodeIndex
from .index.types import SearchCodeResponse
from .settings import Settings
from .types import (
    ActionRequest,
    ActionSpec,
    FileWithSpans,
    Reject,
)

logger = logging.getLogger(__name__)


class LoopState(BaseModel):
    def model(self) -> str:
        return Settings.agent_model

    def temperature(self) -> float:
        return 0.0

    def tools(self) -> list[Type[ActionSpec]]:
        return []

    def stop_words(self):
        return []

    def max_tokens(self):
        return 1000


class SearchCodeRequest(ActionRequest):
    file_pattern: Optional[str] = Field(
        default=None,
        description='A glob pattern to filter search results to specific file types or directories. ',
    )
    query: Optional[str] = Field(
        default=None,
        description='A semantic similarity search query. Use natural language to describe what you are looking for.',
    )
    code_snippet: Optional[str] = Field(
        default=None,
        description='Specific code snippet to that should be exactly matched.',
    )
    class_name: Optional[str] = Field(
        default=None, description='Specific class name to include in the search.'
    )
    function_name: Optional[str] = Field(
        default=None, description='Specific function name to include in the search.'
    )

    @model_validator(mode='after')
    def check_at_least_one_field(self):
        if (
            not self.query
            and not self.code_snippet
            and not self.class_name
            and not self.function_name
        ):
            raise ValueError(
                'At least one of query, code_snippet, class_name, or function_name must be set'
            )
        return self


class SearchCodeAction(ActionSpec):
    code_index: CodeIndex

    @classmethod
    def request_class(cls) -> Type[SearchCodeRequest]:
        return SearchCodeRequest

    @classmethod
    def name(self) -> str:
        return 'search'

    @classmethod
    def description(cls) -> str:
        return 'Search for code.'

    @classmethod
    def validate_request(cls, args: Dict[str, Any]) -> SearchCodeRequest:
        return cls.request_class().model_validate(args, strict=True)

    def __init__(self, code_index: CodeIndex):
        super().__init__(code_index=code_index)

    def search(self, request: SearchCodeRequest) -> SearchCodeResponse:
        return self.code_index.search(**request.dict())

    class Config:
        arbitrary_types_allowed = True


class IdentifyCodeRequest(ActionRequest):
    reasoning: str = Field(None, description='The reasoning for the code selection.')

    files_with_spans: List[FileWithSpans] = Field(
        default=None, description='The files and spans to select.'
    )


class IdentifyCode(ActionSpec):
    @classmethod
    def request_class(cls):
        return IdentifyCodeRequest

    @classmethod
    def name(self):
        return 'identify'

    @classmethod
    def description(cls) -> str:
        return 'Identify the relevant code files and spans.'


class FindCodeRequest(ActionRequest):
    instructions: Optional[str] = Field(
        default=None, description='Instructions to find code based on.'
    )


class FindCodeResponse(BaseModel):
    message: Optional[str] = Field(None, description='A message to show the user.')
    files: list[FileWithSpans] = Field(
        default_factory=list, description='The files and spans found.'
    )


class ActionCallWithContext(BaseModel):
    call_id: str
    action_name: str
    arguments: dict
    file_context: FileContext
    message: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True


class Searching(LoopState):
    def tools(self) -> list[Type[ActionSpec]]:
        return [SearchCodeAction, IdentifyCode, Reject]
