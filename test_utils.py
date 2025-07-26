#!/usr/bin/env python3
"""
Shared utilities for performance testing with tool calls.

This module provides common functionality for testing LLM performance
with tool interactions, following the 3-step workflow:
1. Initial tool request
2. Tool execution and response
3. Summary request
"""

import json
import os
import time
from typing import Any, Optional

# Standard math tool definition used across all tests
MATH_TOOL = {
    'type': 'function',
    'function': {
        'name': 'math',
        'description': 'Perform mathematical calculations',
        'parameters': {
            'type': 'object',
            'properties': {
                'operation': {
                    'type': 'string',
                    'description': 'The mathematical operation to perform',
                    'enum': ['add', 'subtract', 'multiply', 'divide'],
                },
                'a': {'type': 'number', 'description': 'First number'},
                'b': {'type': 'number', 'description': 'Second number'},
            },
            'required': ['operation', 'a', 'b'],
        },
    },
}

# Test prompts for the 3-step workflow
STEP1_PROMPT = 'What is the product of 45 and 126? Use the math tool to calculate this.'
STEP3_PROMPT = 'Please summarize what just happened in our conversation.'


def execute_math_tool(operation: str, a: float, b: float) -> str:
    """Execute the math tool function."""
    if operation == 'multiply':
        result = a * b
    elif operation == 'add':
        result = a + b
    elif operation == 'subtract':
        result = a - b
    elif operation == 'divide':
        if b == 0:
            return 'Error: Division by zero'
        result = a / b
    else:
        return f"Error: Unknown operation '{operation}'"

    return str(result)


def check_credentials() -> tuple[bool, dict[str, Optional[str]]]:
    """
    Check for required environment variables.

    Returns:
        Tuple of (success, credentials_dict)
    """
    credentials = {
        'litellm_api_key': os.getenv('LITELLM_PROXY_API_KEY'),
        'litellm_base_url': os.getenv('LITELLM_BASE_URL'),
        'gemini_api_key': os.getenv('GEMINI_API_KEY'),
    }

    # At least one set of credentials should be available
    has_litellm = credentials['litellm_api_key'] and credentials['litellm_base_url']
    has_gemini = credentials['gemini_api_key']

    if not (has_litellm or has_gemini):
        print('❌ No valid credentials found')
        print('   For LiteLLM: Set LITELLM_PROXY_API_KEY and LITELLM_BASE_URL')
        print('   For Gemini: Set GEMINI_API_KEY')
        return False, credentials

    # Log what we have (without exposing keys)
    if has_litellm:
        print(
            f'✅ LiteLLM credentials configured (base_url: {credentials["litellm_base_url"]})'
        )
    if has_gemini:
        print('✅ Gemini API key configured')

    return True, credentials


def extract_tool_call(response: Any) -> Optional[dict[str, Any]]:
    """
    Extract tool call information from LLM response.

    Works with both LiteLLM and native API responses.
    """
    try:
        # Handle LiteLLM response format
        if hasattr(response, 'choices') and response.choices:
            choice = response.choices[0]
            if hasattr(choice, 'message') and hasattr(choice.message, 'tool_calls'):
                tool_calls = choice.message.tool_calls
                if tool_calls and len(tool_calls) > 0:
                    tool_call = tool_calls[0]
                    return {
                        'id': tool_call.id,
                        'name': tool_call.function.name,
                        'arguments': json.loads(tool_call.function.arguments),
                    }

        # Handle native Google API response format
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                for part in candidate.content.parts:
                    if hasattr(part, 'function_call'):
                        func_call = part.function_call
                        return {
                            'id': f'call_{int(time.time())}',  # Generate ID for native API
                            'name': func_call.name,
                            'arguments': dict(func_call.args),
                        }

        return None
    except Exception as e:
        print(f'⚠️  Error extracting tool call: {e}')
        return None


def create_tool_response_message(tool_call_id: str, result: str) -> dict[str, Any]:
    """Create a tool response message for the conversation."""
    return {'role': 'tool', 'tool_call_id': tool_call_id, 'content': result}


class ToolCallTestResult:
    """Container for tool call test results."""

    def __init__(self):
        self.success = False
        self.error = None
        self.messages: list[dict[str, Any]] = []

        # Timing metrics
        self.step1_duration = 0.0  # Initial tool request
        self.step2_duration = 0.0  # Tool execution response
        self.step3_duration = 0.0  # Summary generation
        self.total_duration = 0.0

        # Tool call metrics
        self.tool_call_success = False
        self.tool_call_result = None
        self.expected_result = '5670'  # 45 * 126

        # Response metrics
        self.step1_response_length = 0
        self.step2_response_length = 0
        self.step3_response_length = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary for analysis."""
        return {
            'success': self.success,
            'error': self.error,
            'step1_duration': self.step1_duration,
            'step2_duration': self.step2_duration,
            'step3_duration': self.step3_duration,
            'total_duration': self.total_duration,
            'tool_call_success': self.tool_call_success,
            'tool_call_result': self.tool_call_result,
            'result_correct': self.tool_call_result == self.expected_result,
            'step1_response_length': self.step1_response_length,
            'step2_response_length': self.step2_response_length,
            'step3_response_length': self.step3_response_length,
            'message_count': len(self.messages),
        }


def run_tool_call_test(
    completion_func, model_name: str, **kwargs
) -> ToolCallTestResult:
    """
    Run the standardized 3-step tool call test.

    Args:
        completion_func: Function to call for LLM completions
        model_name: Name of the model being tested
        **kwargs: Additional parameters for the completion function

    Returns:
        ToolCallTestResult with timing and success metrics
    """
    result = ToolCallTestResult()
    start_time = time.time()

    try:
        # Step 1: Initial tool request
        print('🔧 Step 1: Requesting tool call...')
        step1_start = time.time()

        result.messages = [{'role': 'user', 'content': STEP1_PROMPT}]

        step1_response = completion_func(
            messages=result.messages, tools=[MATH_TOOL], **kwargs
        )

        result.step1_duration = time.time() - step1_start

        # Extract tool call from response
        tool_call = extract_tool_call(step1_response)
        if not tool_call:
            result.error = 'No tool call found in Step 1 response'
            return result

        result.tool_call_success = True
        print(f'✅ Tool call extracted: {tool_call["name"]}({tool_call["arguments"]})')

        # Add assistant response to messages
        result.messages.append(
            {
                'role': 'assistant',
                'content': '',
                'tool_calls': [
                    {
                        'id': tool_call['id'],
                        'type': 'function',
                        'function': {
                            'name': tool_call['name'],
                            'arguments': json.dumps(tool_call['arguments']),
                        },
                    }
                ],
            }
        )

        # Step 2: Execute tool and send result
        print('🔧 Step 2: Executing tool and sending result...')
        step2_start = time.time()

        # Execute the math tool
        args = tool_call['arguments']
        tool_result = execute_math_tool(
            args.get('operation', 'multiply'), args.get('a', 45), args.get('b', 126)
        )
        result.tool_call_result = tool_result
        print(f'✅ Tool result: {tool_result}')

        # Add tool response to messages
        result.messages.append(
            create_tool_response_message(tool_call['id'], tool_result)
        )

        # Get LLM response to tool result
        step2_response = completion_func(messages=result.messages, **kwargs)

        result.step2_duration = time.time() - step2_start

        # Extract content from step 2 response
        step2_content = ''
        if hasattr(step2_response, 'choices') and step2_response.choices:
            step2_content = step2_response.choices[0].message.content or ''
        elif hasattr(step2_response, 'candidates') and step2_response.candidates:
            step2_content = step2_response.candidates[0].content.parts[0].text or ''

        result.step2_response_length = len(step2_content)
        result.messages.append({'role': 'assistant', 'content': step2_content})

        # Step 3: Request summary
        print('🔧 Step 3: Requesting summary...')
        step3_start = time.time()

        result.messages.append({'role': 'user', 'content': STEP3_PROMPT})

        step3_response = completion_func(messages=result.messages, **kwargs)

        result.step3_duration = time.time() - step3_start

        # Extract content from step 3 response
        step3_content = ''
        if hasattr(step3_response, 'choices') and step3_response.choices:
            step3_content = step3_response.choices[0].message.content or ''
        elif hasattr(step3_response, 'candidates') and step3_response.candidates:
            step3_content = step3_response.candidates[0].content.parts[0].text or ''

        result.step3_response_length = len(step3_content)
        result.messages.append({'role': 'assistant', 'content': step3_content})

        result.success = True
        print('✅ All steps completed successfully')

    except Exception as e:
        result.error = str(e)
        print(f'❌ Test failed: {e}')

    result.total_duration = time.time() - start_time
    return result


def print_tool_call_results(results: list[ToolCallTestResult], test_name: str):
    """Print formatted results for tool call tests."""
    print(f'\n📊 {test_name} - Tool Call Test Results')
    print('=' * 60)

    successful_results = [r for r in results if r.success]

    if not successful_results:
        print('❌ No successful tests to analyze')
        return

    # Summary statistics
    total_tests = len(results)
    success_rate = len(successful_results) / total_tests * 100

    print(
        f'Success Rate: {success_rate:.1f}% ({len(successful_results)}/{total_tests})'
    )

    # Timing analysis
    avg_total = sum(r.total_duration for r in successful_results) / len(
        successful_results
    )
    avg_step1 = sum(r.step1_duration for r in successful_results) / len(
        successful_results
    )
    avg_step2 = sum(r.step2_duration for r in successful_results) / len(
        successful_results
    )
    avg_step3 = sum(r.step3_duration for r in successful_results) / len(
        successful_results
    )

    print('\nTiming Analysis:')
    print(f'  Average Total Duration: {avg_total:.3f}s')
    print(f'  Average Step 1 (Tool Request): {avg_step1:.3f}s')
    print(f'  Average Step 2 (Tool Response): {avg_step2:.3f}s')
    print(f'  Average Step 3 (Summary): {avg_step3:.3f}s')

    # Tool call accuracy
    tool_success_rate = (
        sum(1 for r in successful_results if r.tool_call_success)
        / len(successful_results)
        * 100
    )
    correct_results = (
        sum(1 for r in successful_results if r.tool_call_result == '5670')
        / len(successful_results)
        * 100
    )

    print('\nTool Call Analysis:')
    print(f'  Tool Call Success Rate: {tool_success_rate:.1f}%')
    print(f'  Correct Results (5670): {correct_results:.1f}%')

    # Find fastest and slowest
    fastest = min(successful_results, key=lambda x: x.total_duration)
    slowest = max(successful_results, key=lambda x: x.total_duration)

    print('\nPerformance Range:')
    print(f'  Fastest: {fastest.total_duration:.3f}s')
    print(f'  Slowest: {slowest.total_duration:.3f}s')

    if fastest.total_duration > 0:
        speedup = slowest.total_duration / fastest.total_duration
        print(f'  Speed Difference: {speedup:.2f}x')
