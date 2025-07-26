#!/usr/bin/env python3
"""
Test the impact of thinking budget on Gemini 2.5 Pro performance with tool calls.

This is the PRIMARY test for thinking/reasoning functionality, using the new
3-step tool call architecture to better simulate real-world usage.
"""

import os

import google.generativeai as genai
from google import genai as new_genai
from google.genai import types

# Import shared utilities
from test_utils import (
    MATH_TOOL,
    check_credentials,
    run_tool_call_test,
)

# Add LiteLLM import
try:
    import litellm

    LITELLM_AVAILABLE = True
except ImportError:
    LITELLM_AVAILABLE = False
    print('⚠️  LiteLLM not available - skipping LiteLLM tests')


def create_old_genai_completion_func():
    """Create completion function using old google.generativeai API."""
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        return None

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-pro', tools=[MATH_TOOL])

    def completion_func(messages, **kwargs):
        # Convert messages to old API format
        if messages and messages[-1]['role'] == 'user':
            prompt = messages[-1]['content']
            return model.generate_content(prompt)
        return None

    return completion_func


def create_new_genai_completion_func(thinking_budget: int = None):
    """Create completion function using new google.genai API with thinking budget."""
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        return None

    client = new_genai.Client(api_key=api_key)

    config = {}
    if thinking_budget:
        config['thinking'] = {'budget_tokens': thinking_budget}

    def completion_func(messages, tools=None, **kwargs):
        # Convert to new API format
        contents = []
        for msg in messages:
            if msg['role'] == 'user':
                contents.append(
                    types.Content(
                        role='user', parts=[types.Part.from_text(msg['content'])]
                    )
                )
            elif msg['role'] == 'assistant':
                if 'tool_calls' in msg:
                    # Handle tool calls
                    parts = []
                    for tool_call in msg['tool_calls']:
                        parts.append(
                            types.Part.from_function_call(
                                types.FunctionCall(
                                    name=tool_call['function']['name'],
                                    args=tool_call['function']['arguments'],
                                )
                            )
                        )
                    contents.append(types.Content(role='model', parts=parts))
                else:
                    contents.append(
                        types.Content(
                            role='model', parts=[types.Part.from_text(msg['content'])]
                        )
                    )
            elif msg['role'] == 'tool':
                contents.append(
                    types.Content(
                        role='function',
                        parts=[
                            types.Part.from_function_response(
                                types.FunctionResponse(
                                    name='math', response={'result': msg['content']}
                                )
                            )
                        ],
                    )
                )

        # Convert tools to new API format
        tool_configs = []
        if tools:
            for tool in tools:
                tool_configs.append(
                    types.Tool(
                        function_declarations=[
                            types.FunctionDeclaration(
                                name=tool['function']['name'],
                                description=tool['function']['description'],
                                parameters=tool['function']['parameters'],
                            )
                        ]
                    )
                )

        return client.models.generate_content(
            model='gemini-2.5-pro',
            contents=contents,
            tools=tool_configs,
            config=types.GenerateContentConfig(**config),
        )

    return completion_func


def create_litellm_completion_func(
    reasoning_effort: str = None, thinking_budget: int = None
):
    """Create completion function using LiteLLM with secure credentials."""
    if not LITELLM_AVAILABLE:
        return None

    api_key = os.getenv('LITELLM_PROXY_API_KEY')
    base_url = os.getenv('LITELLM_BASE_URL')

    if not api_key or not base_url:
        print('⚠️  LiteLLM credentials not available - skipping LiteLLM tests')
        return None

    def completion_func(messages, tools=None, **kwargs):
        params = {
            'model': 'gemini-2.5-pro',
            'messages': messages,
            'api_key': api_key,
            'base_url': base_url,
            'drop_params': True,
        }

        if tools:
            params['tools'] = tools

        if reasoning_effort:
            params['reasoning_effort'] = reasoning_effort

        if thinking_budget:
            params['thinking'] = {'budget_tokens': thinking_budget}

        return litellm.completion(**params)

    return completion_func


def test_thinking_budget_configurations():
    """Test various thinking budget configurations with tool calls."""
    print('🧠 Testing Thinking Budget Configurations with Tool Calls')
    print('=' * 70)

    # Check credentials
    success, credentials = check_credentials()
    if not success:
        return

    all_results = []

    # Test configurations
    test_configs = [
        {
            'name': 'Old API (No Thinking)',
            'func': create_old_genai_completion_func(),
            'available': credentials['gemini_api_key'] is not None,
        },
        {
            'name': 'New API - Thinking Budget: 128',
            'func': create_new_genai_completion_func(thinking_budget=128),
            'available': credentials['gemini_api_key'] is not None,
        },
        {
            'name': 'New API - Thinking Budget: 1024',
            'func': create_new_genai_completion_func(thinking_budget=1024),
            'available': credentials['gemini_api_key'] is not None,
        },
        {
            'name': 'New API - Thinking Budget: 4096',
            'func': create_new_genai_completion_func(thinking_budget=4096),
            'available': credentials['gemini_api_key'] is not None,
        },
        {
            'name': 'LiteLLM - Reasoning Effort: Low',
            'func': create_litellm_completion_func(reasoning_effort='low'),
            'available': LITELLM_AVAILABLE
            and credentials['litellm_api_key'] is not None,
        },
        {
            'name': 'LiteLLM - Reasoning Effort: High',
            'func': create_litellm_completion_func(reasoning_effort='high'),
            'available': LITELLM_AVAILABLE
            and credentials['litellm_api_key'] is not None,
        },
        {
            'name': 'LiteLLM - Thinking Budget: 128',
            'func': create_litellm_completion_func(thinking_budget=128),
            'available': LITELLM_AVAILABLE
            and credentials['litellm_api_key'] is not None,
        },
    ]

    # Run tests
    for config in test_configs:
        if not config['available'] or config['func'] is None:
            print(f'\n⏭️  Skipping {config["name"]} - not available')
            continue

        print(f'\n🧪 Testing: {config["name"]}')
        print('-' * 50)

        try:
            result = run_tool_call_test(config['func'], config['name'])
            result_dict = result.to_dict()
            result_dict['config_name'] = config['name']
            all_results.append(result_dict)

            if result.success:
                print(f'✅ Success - Total: {result.total_duration:.3f}s')
                print(f'   Step 1 (Tool Request): {result.step1_duration:.3f}s')
                print(f'   Step 2 (Tool Response): {result.step2_duration:.3f}s')
                print(f'   Step 3 (Summary): {result.step3_duration:.3f}s')
                print(f'   Tool Result: {result.tool_call_result}')
            else:
                print(f'❌ Failed: {result.error}')

        except Exception as e:
            print(f'❌ Test failed with exception: {e}')
            all_results.append(
                {
                    'config_name': config['name'],
                    'success': False,
                    'error': str(e),
                    'total_duration': 0,
                }
            )

    return all_results


def analyze_thinking_budget_results(results):
    """Analyze and compare thinking budget test results."""
    print('\n📊 THINKING BUDGET ANALYSIS')
    print('=' * 70)

    successful_results = [r for r in results if r['success']]

    if not successful_results:
        print('❌ No successful tests to analyze')
        return

    # Group by API type
    old_api_results = [r for r in successful_results if 'Old API' in r['config_name']]
    new_api_results = [r for r in successful_results if 'New API' in r['config_name']]
    [r for r in successful_results if 'LiteLLM' in r['config_name']]

    print('📈 Performance Summary:')

    # Show all results sorted by speed
    sorted_results = sorted(successful_results, key=lambda x: x['total_duration'])
    for i, result in enumerate(sorted_results, 1):
        print(f'   {i}. {result["config_name"]}: {result["total_duration"]:.3f}s')

    # Compare API types
    if old_api_results and new_api_results:
        old_avg = sum(r['total_duration'] for r in old_api_results) / len(
            old_api_results
        )
        new_avg = sum(r['total_duration'] for r in new_api_results) / len(
            new_api_results
        )

        print('\n🔄 API Comparison:')
        print(f'   Old API Average: {old_avg:.3f}s')
        print(f'   New API Average: {new_avg:.3f}s')

        if old_avg > 0:
            improvement = old_avg / new_avg if new_avg < old_avg else new_avg / old_avg
            direction = 'faster' if new_avg < old_avg else 'slower'
            print(f'   New API is {improvement:.2f}x {direction}')

    # Analyze thinking budget impact
    thinking_budget_results = [
        r for r in new_api_results if 'Thinking Budget' in r['config_name']
    ]
    if len(thinking_budget_results) > 1:
        print('\n🧠 Thinking Budget Impact:')
        for result in sorted(
            thinking_budget_results, key=lambda x: x['total_duration']
        ):
            budget = 'Unknown'
            if '128' in result['config_name']:
                budget = '128'
            elif '1024' in result['config_name']:
                budget = '1024'
            elif '4096' in result['config_name']:
                budget = '4096'
            print(f'   Budget {budget}: {result["total_duration"]:.3f}s')

    # Tool call accuracy
    correct_results = sum(
        1 for r in successful_results if r.get('result_correct', False)
    )
    accuracy = correct_results / len(successful_results) * 100
    print(
        f'\n🎯 Tool Call Accuracy: {accuracy:.1f}% ({correct_results}/{len(successful_results)})'
    )


def main():
    """Run thinking budget performance tests with tool calls."""
    print('🚀 THINKING BUDGET PERFORMANCE TEST WITH TOOL CALLS')
    print('=' * 70)
    print(
        'This test evaluates thinking budget impact using realistic tool call workflows'
    )
    print()

    results = test_thinking_budget_configurations()

    if results:
        analyze_thinking_budget_results(results)
    else:
        print('❌ No test results to analyze')


if __name__ == '__main__':
    main()
