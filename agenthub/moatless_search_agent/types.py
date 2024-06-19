# from typing import Any, Dict, List, Optional, Type

# from pydantic import BaseModel, Field


# class FileWithSpans(BaseModel):
#     file_path: str = Field(
#         description='The file path where the relevant code is found.'
#     )
#     span_ids: List[str] = Field(
#         default_factory=list,
#         description='The span ids of the relevant code in the file',
#     )

#     def add_span_id(self, span_id):
#         if span_id not in self.span_ids:
#             self.span_ids.append(span_id)

#     def add_span_ids(self, span_ids: List[str]):
#         for span_id in span_ids:
#             self.add_span_id(span_id)


# class ActionResponse(BaseModel):
#     message: Optional[str] = None


# class ActionRequest(BaseModel):
#     @classmethod
#     def openai_tool_parameters(cls) -> Dict[str, Any]:
#         schema = cls.model_json_schema()

#         parameters = {
#             k: v for k, v in schema.items() if k not in ('title', 'description')
#         }

#         parameters['required'] = sorted(
#             k for k, v in parameters['properties'].items() if 'default' not in v
#         )

#         # Just set type and skip anyOf on Optionals
#         for k, v in parameters['properties'].items():
#             if 'anyOf' in v:
#                 any_of = v.pop('anyOf')
#                 for type_ in any_of:
#                     if type_['type'] != 'null':
#                         v.update(type_)
#                         break

#         return parameters


# class EmptyRequest(ActionRequest):
#     pass


# class ActionSpec(BaseModel):
#     def __init__(self, **kwargs):
#         super().__init__(**kwargs)

#     @classmethod
#     def name(cls) -> str:
#         return ''

#     @classmethod
#     def description(cls) -> str:
#         return ''

#     @classmethod
#     def request_class(cls) -> Type[ActionRequest]:
#         return EmptyRequest

#     @classmethod
#     def validate_request(cls, args: Dict[str, Any]) -> ActionRequest:
#         return cls.request_class().model_validate(args, strict=True)

#     # TODO: Do generic solution to get parameters from ActionRequest
#     @classmethod
#     def openai_tool_spec(cls) -> Dict[str, Any]:
#         parameters = cls.request_class().openai_tool_parameters()
#         return {
#             'type': 'function',
#             'function': {
#                 'name': cls.name(),
#                 'description': cls.description(),
#                 'parameters': parameters,
#             },
#         }


# class FinishRequest(ActionRequest):
#     reason: str = Field(..., description='The reason to finishing the request.')


# class Finish(ActionSpec):
#     @classmethod
#     def name(self):
#         return 'finish'

#     @classmethod
#     def description(self):
#         return 'Finish.'

#     @classmethod
#     def request_class(cls):
#         return FinishRequest


# class RejectRequest(ActionRequest):
#     reason: str = Field(..., description='The reason for rejecting the request.')


# class Reject(ActionSpec):
#     @classmethod
#     def request_class(cls):
#         return RejectRequest

#     @classmethod
#     def name(self):
#         return 'reject'

#     @classmethod
#     def description(cls) -> str:
#         return 'Reject the request.'


from typing import Any, Dict, List, Optional, Type

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


class ActionResponse(BaseModel):
    message: Optional[str] = None


class ActionRequest(BaseModel):
    @classmethod
    def openai_tool_parameters(cls) -> Dict[str, Any]:
        schema = cls.model_json_schema()

        parameters = {
            k: v for k, v in schema.items() if k not in ('title', 'description')
        }

        parameters['required'] = sorted(
            k for k, v in parameters['properties'].items() if 'default' not in v
        )

        # Just set type and skip anyOf on Optionals
        for k, v in parameters['properties'].items():
            if 'anyOf' in v:
                any_of = v.pop('anyOf')
                for type_ in any_of:
                    if type_['type'] != 'null':
                        v.update(type_)
                        break

        return parameters


class EmptyRequest(ActionRequest):
    pass


class ActionSpec(BaseModel):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @classmethod
    def name(cls) -> str:
        return ''

    @classmethod
    def description(cls) -> str:
        return ''

    @classmethod
    def request_class(cls) -> Type[ActionRequest]:
        return EmptyRequest

    @classmethod
    def validate_request(cls, args: Dict[str, Any]) -> ActionRequest:
        return cls.request_class().model_validate(args, strict=True)

    # TODO: Do generic solution to get parameters from ActionRequest
    @classmethod
    def openai_tool_spec(cls) -> Dict[str, Any]:
        parameters = cls.request_class().openai_tool_parameters()
        return {
            'type': 'function',
            'function': {
                'name': cls.name(),
                'description': cls.description(),
                'parameters': parameters,
            },
        }


class FinishRequest(ActionRequest):
    reason: str = Field(..., description='The reason to finishing the request.')


class Finish(ActionSpec):
    @classmethod
    def name(self):
        return 'finish'

    @classmethod
    def description(self):
        return 'Finish.'

    @classmethod
    def request_class(cls):
        return FinishRequest


class RejectRequest(ActionRequest):
    reason: str = Field(..., description='The reason for rejecting the request.')


class Reject(ActionSpec):
    @classmethod
    def request_class(cls):
        return RejectRequest

    @classmethod
    def name(self):
        return 'reject'

    @classmethod
    def description(cls) -> str:
        return 'Reject the request.'
