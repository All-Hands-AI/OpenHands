from litellm import ModelResponse
from pydantic import BaseModel


class ToolCallMetadata(BaseModel):
    # See https://docs.litellm.ai/docs/completion/function_call#step-3---second-litellmcompletion-call
    function_name: str  # Name of the function that was called
    tool_call_id: str  # ID of the tool call

    model_response: ModelResponse
    total_calls_in_response: int
