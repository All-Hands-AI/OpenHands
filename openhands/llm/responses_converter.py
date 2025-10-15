"""Utilities for converting Responses API results into Chat Completions format."""

from typing import Any, cast

from litellm import (
    AllMessageValues as ChatCompletionMessageValues,
)
from litellm import (
    ResponseInputParam,  # typed list of responses input items
)
from litellm.types.llms.openai import ResponsesAPIResponse
from litellm.types.responses.main import (
    GenericResponseOutputItem,
    OutputFunctionToolCall,
    OutputText,
)
from litellm.types.utils import ModelResponse
from openai.types.responses.response_function_tool_call import ResponseFunctionToolCall
from openai.types.responses.response_output_message import ResponseOutputMessage
from openai.types.responses.response_output_refusal import ResponseOutputRefusal
from openai.types.responses.response_output_text import ResponseOutputText
from openai.types.responses.response_reasoning_item import ResponseReasoningItem


def messages_to_responses_items(
    messages: list[ChatCompletionMessageValues],
) -> ResponseInputParam:
    """Convert typed Chat Completions messages into Responses API input items.

    Accepts a list of AllMessageValues (TypedDicts) and produces Responses API
    input items.

    Output schema is a list of dict items compatible with OpenAI Responses API:
    - For user/system/assistant: {"role": <role>, "content": <text>}
    - For assistant.tool_calls: {"type":"function_call", ...}
    - For tool: {"type":"function_call_output", ...}
    - For images: {"type": "input_image", "image_url": <url>}
    """
    if not messages:
        return []

    def _text_and_image_items(role: str, content: Any) -> list[dict]:
        items: list[dict] = []
        if isinstance(content, str):
            if content:
                items.append({'role': role, 'content': content})
        elif isinstance(content, list):
            for seg in content:
                if isinstance(seg, dict):
                    if seg.get('type') == 'text' and seg.get('text'):
                        items.append({'role': role, 'content': seg['text']})
                    elif seg.get('type') == 'image_url' and seg.get('image_url'):
                        image_url_obj = seg['image_url']
                        if isinstance(image_url_obj, dict) and image_url_obj.get('url'):
                            items.append(
                                {
                                    'type': 'input_image',
                                    'image_url': image_url_obj['url'],
                                }
                            )
        elif content is not None:
            items.append({'role': role, 'content': str(content)})
        return items

    out: list[dict] = []

    for m in messages:
        msg = dict(m)
        role = str(msg.get('role', ''))
        if role == 'tool':
            call_id = str(msg.get('tool_call_id', ''))
            output_text = ''
            content = msg.get('content', '')
            if isinstance(content, str):
                output_text = content
            elif isinstance(content, list):
                for seg in content:
                    if (
                        isinstance(seg, dict)
                        and seg.get('type') == 'text'
                        and seg.get('text')
                    ):
                        output_text = seg['text']
                        break
            out.append(
                {
                    'type': 'function_call_output',
                    'call_id': call_id,
                    'output': output_text,
                }
            )
            continue

        if role == 'assistant':
            out.extend(_text_and_image_items('assistant', msg.get('content', '')))
            tool_calls = msg.get('tool_calls')
            if isinstance(tool_calls, list):
                for tc in tool_calls:
                    if not isinstance(tc, dict):
                        continue
                    fn = tc.get('function', {})
                    out.append(
                        {
                            'type': 'function_call',
                            'call_id': str(tc.get('id', '')),
                            'name': str(fn.get('name', '')),
                            'arguments': str(fn.get('arguments', '')),
                        }
                    )
            continue

        if role in {'user', 'system', 'developer'}:
            out.extend(_text_and_image_items(role, msg.get('content', '')))
            continue

        raise ValueError(f'Unsupported message role: {role}')

    return cast(ResponseInputParam, out)


def responses_to_completion_format(
    responses_result: ResponsesAPIResponse,
) -> ModelResponse:
    """Convert Responses API result to ChatCompletions format.

    This allows the Responses API result to be used with existing code
    that expects ChatCompletions format.

    Args:
        responses_result: Result from litellm.responses()

    Returns:
        ModelResponse in ChatCompletions format
    """
    # Extract the main content, tool calls, and reasoning content if available
    output_items = responses_result.output

    content = ''
    reasoning_content = ''
    tool_calls: list[dict[str, Any]] = []

    for item in output_items:
        # Strict typed mapping based on LiteLLM/OpenAI response classes
        if isinstance(item, ResponseOutputMessage) and item.type == 'message':
            for seg in item.content:
                if isinstance(seg, ResponseOutputText) and seg.text:
                    content = seg.text
                elif isinstance(seg, ResponseOutputRefusal):
                    pass
            continue
        if isinstance(item, ResponseFunctionToolCall) and item.type == 'function_call':
            tool_calls.append(
                {
                    'id': (item.call_id or item.id or ''),
                    'type': 'function',
                    'function': {'name': item.name, 'arguments': item.arguments},
                }
            )
            continue
        if isinstance(item, GenericResponseOutputItem) and item.type == 'message':
            for seg in item.content:
                if isinstance(seg, OutputText) and seg.text:
                    content = seg.text
            continue
        if isinstance(item, OutputFunctionToolCall) and item.type == 'function_call':
            tool_calls.append(
                {
                    'id': (item.call_id or item.id or ''),
                    'type': 'function',
                    'function': {'name': item.name, 'arguments': item.arguments},
                }
            )
            continue
        if isinstance(item, ResponseReasoningItem) and item.type == 'reasoning':
            if item.content:
                parts = [seg.text for seg in item.content if getattr(seg, 'text', None)]
                if parts:
                    reasoning_content = '\n\n'.join(parts)
            elif item.summary:
                parts = [s.text for s in item.summary if getattr(s, 'text', None)]
                if parts:
                    reasoning_content = '\n\n'.join(parts)

    # Create a ChatCompletions-compatible response
    message: dict[str, Any] = {
        'role': 'assistant',
        'content': content,
    }
    if tool_calls:
        message['tool_calls'] = tool_calls

    # Add reasoning content as a custom field if available
    if reasoning_content:
        message['reasoning_content'] = reasoning_content

    # model string
    model = responses_result.model

    finish_reason = 'tool_calls' if tool_calls else 'stop'

    response = {
        'id': responses_result.id,
        'object': 'chat.completion',
        'created': int(responses_result.created_at),
        'model': model,
        'choices': [
            {
                'index': 0,
                'message': message,
                'finish_reason': finish_reason,
            }
        ],
        'usage': {
            'prompt_tokens': 0,
            'completion_tokens': 0,
            'total_tokens': 0,
        },
    }

    # Extract usage information if available
    usage = getattr(responses_result, 'usage', None)
    if usage is not None:
        # Map Responses API usage fields to ChatCompletions format
        response['usage']['prompt_tokens'] = usage.input_tokens
        response['usage']['completion_tokens'] = usage.output_tokens
        response['usage']['total_tokens'] = usage.total_tokens

        # Map reasoning tokens if available and well-typed
        output_details = getattr(usage, 'output_tokens_details', None)
        rt = getattr(output_details, 'reasoning_tokens', None)
        if isinstance(rt, int):
            response['usage']['completion_tokens_details'] = {'reasoning_tokens': rt}

    return ModelResponse(**response)
