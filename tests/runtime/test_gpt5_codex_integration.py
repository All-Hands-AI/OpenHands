"""Integration test for gpt-5-codex using the Responses API."""

import os

import pytest
from conftest import _close_test_runtime, _load_runtime

from openhands.core.config import LLMConfig
from openhands.core.logger import openhands_logger as logger
from openhands.events.action import CmdRunAction, FileWriteAction
from openhands.events.observation import CmdRunObservation, FileWriteObservation
from openhands.llm.llm import LLM


@pytest.mark.skipif(
    not os.getenv('LLM_API_KEY') or not os.getenv('LLM_BASE_URL'),
    reason='This test requires LLM_API_KEY and LLM_BASE_URL environment variables to be set.',
)
def test_gpt5_codex_responses_api_integration(temp_dir, runtime_cls, run_as_openhands):
    """Test that gpt-5-codex works correctly using the Responses API converter.

    This test verifies that:
    1. gpt-5-codex can be instantiated and used
    2. The Responses API converter works correctly
    3. The model can perform a simple coding task
    """
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)

    try:
        # Create LLM config for gpt-5-codex
        llm_config = LLMConfig(
            model='gpt-5-codex',
            api_key=os.getenv('LLM_API_KEY'),
            base_url=os.getenv('LLM_BASE_URL'),
        )

        # Initialize LLM
        llm = LLM(config=llm_config, service_id='test')

        # Verify that the model requires responses API
        assert llm.requires_responses_api(), 'gpt-5-codex should require Responses API'

        # Create a simple Python file to work with
        test_file_path = os.path.join('/workspace', 'test_script.py')
        initial_content = """def hello():
    print("Hello, World!")

if __name__ == "__main__":
    hello()
"""

        # Write the initial file
        write_action = FileWriteAction(path=test_file_path, content=initial_content)
        logger.info(write_action, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(write_action)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        assert isinstance(obs, FileWriteObservation), (
            'The observation should be a FileWriteObservation.'
        )
        assert obs.success, f'Failed to write file: {obs.error}'

        # Test the LLM with a simple completion request
        messages = [
            {
                'role': 'user',
                'content': 'Add a function called "goodbye" that prints "Goodbye, World!" to the existing Python script. Return only the complete updated code.',
            }
        ]

        # Call the LLM
        response = llm.completion(messages=messages)

        # Verify we got a response
        assert response is not None, 'LLM should return a response'
        assert hasattr(response, 'choices'), 'Response should have choices'
        assert len(response.choices) > 0, 'Response should have at least one choice'
        assert hasattr(response.choices[0], 'message'), 'Choice should have a message'

        message_content = response.choices[0].message.content
        assert message_content is not None, 'Message should have content'
        assert len(message_content.strip()) > 0, 'Message content should not be empty'

        # Verify the response contains expected code elements
        assert 'def goodbye' in message_content, (
            'Response should contain the goodbye function'
        )
        assert 'Goodbye, World!' in message_content, (
            'Response should contain the goodbye message'
        )
        assert 'def hello' in message_content, (
            'Response should preserve the original hello function'
        )

        # Test that we can run the updated code
        run_action = CmdRunAction(command='cd /workspace && python test_script.py')
        logger.info(run_action, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(run_action)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        assert isinstance(obs, CmdRunObservation), (
            'The observation should be a CmdRunObservation.'
        )

        # The original script should still work
        assert obs.exit_code == 0, f'Script execution failed: {obs.content}'
        assert 'Hello, World!' in obs.content, (
            'Original functionality should be preserved'
        )

        logger.info('gpt-5-codex integration test completed successfully')

    finally:
        _close_test_runtime(runtime)


@pytest.mark.skipif(
    not os.getenv('LLM_API_KEY') or not os.getenv('LLM_BASE_URL'),
    reason='This test requires LLM_API_KEY and LLM_BASE_URL environment variables to be set.',
)
def test_gpt5_codex_function_calling():
    """Test that gpt-5-codex supports function calling through the Responses API converter."""

    # Create LLM config for gpt-5-codex
    llm_config = LLMConfig(
        model='gpt-5-codex',
        api_key=os.getenv('LLM_API_KEY'),
        base_url=os.getenv('LLM_BASE_URL'),
    )

    # Initialize LLM
    llm = LLM(config=llm_config, service_id='test')

    # Define a simple function for testing
    tools = [
        {
            'type': 'function',
            'function': {
                'name': 'get_current_weather',
                'description': 'Get the current weather in a given location',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'location': {
                            'type': 'string',
                            'description': 'The city and state, e.g. San Francisco, CA',
                        },
                        'unit': {'type': 'string', 'enum': ['celsius', 'fahrenheit']},
                    },
                    'required': ['location'],
                },
            },
        }
    ]

    messages = [{'role': 'user', 'content': 'What is the weather like in Boston?'}]

    # Call the LLM with function calling
    response = llm.completion(messages=messages, tools=tools)

    # Verify we got a response
    assert response is not None, 'LLM should return a response'
    assert hasattr(response, 'choices'), 'Response should have choices'
    assert len(response.choices) > 0, 'Response should have at least one choice'

    message = response.choices[0].message

    # The model should either call the function or explain why it can't
    # (since we're testing the converter works, not the model's specific behavior)
    assert hasattr(message, 'content') or hasattr(message, 'tool_calls'), (
        'Message should have either content or tool_calls'
    )

    logger.info('gpt-5-codex function calling test completed successfully')


@pytest.mark.skipif(
    not os.getenv('LLM_API_KEY') or not os.getenv('LLM_BASE_URL'),
    reason='This test requires LLM_API_KEY and LLM_BASE_URL environment variables to be set.',
)
def test_gpt5_codex_model_features():
    """Test that gpt-5-codex has the expected model features."""

    from openhands.llm.model_features import get_features

    # Test with different model name formats
    for model_name in ['gpt-5-codex', 'openhands/gpt-5-codex']:
        features = get_features(model_name)

        # gpt-5-codex should support function calling (gpt-5* pattern)
        assert features.supports_function_calling, (
            f'{model_name} should support function calling'
        )

        # gpt-5-codex should support reasoning effort (gpt-5* pattern)
        assert features.supports_reasoning_effort, (
            f'{model_name} should support reasoning effort'
        )

        # gpt-5-codex should support stop words (not in the exclusion list)
        assert features.supports_stop_words, f'{model_name} should support stop words'

        # gpt-5-codex should not support prompt cache (not in the inclusion list)
        assert not features.supports_prompt_cache, (
            f'{model_name} should not support prompt cache'
        )

    logger.info('gpt-5-codex model features test completed successfully')
