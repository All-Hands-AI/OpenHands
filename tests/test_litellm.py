import json
import os
import time

import litellm
from dotenv import load_dotenv

load_dotenv()
os.environ['ANTHROPIC_API_KEY'] = ''
os.environ['ANTHROPIC_API_BASE'] = ''


def execution_python_code(code: str) -> str:
    return f'Executed code: {code}'


messages = [
    {
        'role': 'user',
        'content': (
            'Write and execute a complex Python program that simulates a simple ecosystem.\n'
            'Requirements:\n'
            '- Define at least two classes: Animal and Environment\n'
            '- Each Animal has attributes like species, age, energy, and behaviors like move(), eat(), and reproduce()\n'
            '- The Environment class manages a grid where animals move, interact, and the ecosystem evolves step by step\n'
            '- Implement a simulation loop that runs for at least 50 steps, updating the state of the ecosystem\n'
            '- Include data logging of population counts to a CSV file\n'
            '- At the end of the simulation, read the CSV and plot the population trends using matplotlib\n'
            '- Use object-oriented programming principles\n'
            '- The script should be fully self-contained and executable'
        ),
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

# Stream first response from Claude
print('\nLLM Response1 (streaming):\n')
streamed_response = litellm.completion(
    model='claude-3-7-sonnet-20250219',  # Use claude-3-7-sonnet-20250219 to compare
    messages=messages,
    tools=tools,
    tool_choice='auto',
    stream=True,
)

# Track streamed content and tool_calls
full_response = ''
tool_call_accumulators = {}
tool_calls = []
response_message = None
prev_time = time.time()

for chunk in streamed_response:
    current_time = time.time()
    delta_time = current_time - prev_time
    prev_time = current_time

    if not hasattr(chunk, 'choices') or not chunk.choices:
        continue

    choice = chunk.choices[0]
    delta = getattr(choice, 'delta', {})

    # Content streaming
    content_piece = getattr(delta, 'content', None)
    if content_piece:
        print(content_piece, end='', flush=True)
        full_response += content_piece

    # Tool call streaming
    streamed_tool_calls = getattr(delta, 'tool_calls', None)
    if streamed_tool_calls:
        for tool_call in streamed_tool_calls:
            idx = getattr(tool_call, 'index', 0)
            if idx not in tool_call_accumulators:
                tool_call_accumulators[idx] = {'name': '', 'arguments': ''}

            func = getattr(tool_call, 'function', None)
            if func:
                name = func.get('name', '')
                args = func.get('arguments', '')
                print(args, end='', flush=True)

                if isinstance(name, str):
                    tool_call_accumulators[idx]['name'] += name
                if isinstance(args, str):
                    tool_call_accumulators[idx]['arguments'] += args


# Reconstruct tool_calls for next step
for index, call in tool_call_accumulators.items():
    tool_calls.append(
        {
            'id': f'tool_call_{index}',
            'type': 'function',
            'function': {'name': call['name'], 'arguments': call['arguments']},
        }
    )

# Append assistant message (with tool_calls)
if tool_calls:
    messages.append(
        {'role': 'assistant', 'tool_calls': tool_calls, 'content': full_response}
    )

# Execute tool calls
available_functions = {
    'execution_python_code': execution_python_code,
}

for tool_call in tool_calls:
    print(f'\n\nExecuting tool call:\n{tool_call}')
    function_name = tool_call['function']['name']
    function_to_call = available_functions.get(function_name)

    if not function_to_call:
        continue

    function_args = json.loads(tool_call['function']['arguments'])
    function_response = function_to_call(code=function_args.get('code'))
    print(f'Function result:\n{function_response}\n')

    messages.append(
        {
            'tool_call_id': tool_call['id'],
            'role': 'tool',
            'name': function_name,
            'content': function_response,
        }
    )
