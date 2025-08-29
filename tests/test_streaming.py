import asyncio
from typing import Type

from openhands.core.config import load_app_config
from openhands.llm.llm import LLM
from openhands.llm.streaming_llm import StreamingLLM

config = load_app_config()


def test_llm():
    return _get_llm(LLM)


def _get_llm(type_: Type[LLM]):
    return type_(config=config.get_llm_config())


config_type = _get_llm(StreamingLLM)
print(config_type)


def _get(obj, field, default=None):
    if isinstance(obj, dict):
        return obj.get(field, default)
    return getattr(obj, field, default)


messages = [
    {
        'role': 'user',
        'content': 'Write and execute a complex Python program that simulates a simple game of Tic Tac Toe. The program should allow two players to take turns, display the game board after each move, and determine the winner or if the game ends in a draw. The code should be well-structured and include functions for initializing the game, displaying the board, checking for a win or draw, and handling player input.',
    }
]

tools = [
    {
        'type': 'function',
        'function': {
            'name': 'execution_python_code',
            'description': 'Execute a Python code snippet and return the result.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'string', 'description': 'Python code to execute.'}
                },
                'required': ['code'],
            },
        },
    }
]


async def test_acompletion_streaming_StreamingLLM():
    print('\nLLM Response (streaming):\n')

    full_response = ''
    tool_call_accumulators = {}

    llm = _get_llm(StreamingLLM)

    async for chunk in llm.async_streaming_completion(
        messages=messages, tools=tools, tool_choice='auto', stream=True
    ):
        if not chunk or 'choices' not in chunk or not chunk['choices']:
            continue
        print('Chunk result: ', chunk)
        choice = chunk['choices'][0]
        delta = _get(choice, 'delta', {})

        content_piece = _get(delta, 'content', None)
        if content_piece:
            # print(content_piece, end="", flush=True)
            full_response += content_piece

        streamed_tool_calls = _get(delta, 'tool_calls', None) or []
        for tc in streamed_tool_calls:
            idx = _get(tc, 'index', 0) or 0
            func = _get(tc, 'function', None)

            if idx not in tool_call_accumulators:
                tool_call_accumulators[idx] = {'name': '', 'arguments': ''}

            name_piece = _get(func, 'name', None) if func is not None else None
            args_piece = _get(func, 'arguments', None) if func is not None else None

            if isinstance(name_piece, str) and name_piece:
                tool_call_accumulators[idx]['name'] += name_piece

            if isinstance(args_piece, str) and args_piece:
                # print(args_piece, end="", flush=True)
                tool_call_accumulators[idx]['arguments'] += args_piece


if __name__ == '__main__':
    asyncio.run(test_acompletion_streaming_StreamingLLM())
