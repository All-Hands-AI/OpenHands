from unittest.mock import AsyncMock, patch

import httpx
import litellm
import pytest


@pytest.mark.asyncio
async def test_gemini_thinking_patch():
    """
    Tests that we can monkey-patch the thinking config for Gemini calls.
    """
    # Import the original transformation function
    from litellm.llms.vertex_ai.gemini.transformation import (
        async_transform_request_body,
    )

    # Store the original function
    original_transform = async_transform_request_body

    # Create a patched version that adds thinkingConfig
    async def patched_transform(*args, **kwargs):
        # Add thinkingConfig to optional_params before calling the original function
        if 'optional_params' in kwargs:
            kwargs['optional_params']['thinkingConfig'] = {'includeThoughts': True}
        # Call the original function with modified params
        return await original_transform(*args, **kwargs)

    with patch(
        'litellm.llms.vertex_ai.gemini.vertex_and_google_ai_studio_gemini.async_transform_request_body',
        patched_transform,
    ):
        # Patch the actual HTTP client
        with patch(
            'litellm.llms.custom_httpx.http_handler.AsyncHTTPHandler.post',
            new_callable=AsyncMock,
        ) as mock_post:
            # Configure the mock to return a future-like object with a dummy response
            mock_request = httpx.Request('POST', 'https://example.com')
            mock_response = httpx.Response(
                200,
                request=mock_request,
                json={
                    'candidates': [
                        {'content': {'parts': [{'text': 'This is a mock response.'}]}}
                    ],
                    'usageMetadata': {
                        'promptTokenCount': 10,
                        'candidatesTokenCount': 5,
                        'totalTokenCount': 15,
                    },
                },
            )
            mock_post.return_value = mock_response

            # Simulate a call to litellm
            litellm.drop_params = True
            await litellm.acompletion(
                model='gemini/gemini-pro',
                messages=[{'role': 'user', 'content': 'Test prompt'}],
                temperature=0,
                top_p=1,
                api_key='dummy-key',  # required for the call to proceed
            )

            # Assert that the post method was called
            mock_post.assert_called()

            # Get the final JSON payload
            args, kwargs = mock_post.call_args
            final_json_payload = kwargs.get('json', {})

            # Assert that the generationConfig is what we want
            expected_generation_config = {
                'temperature': 0,
                'top_p': 1,
                'thinkingConfig': {'includeThoughts': True},
            }
            assert (
                final_json_payload.get('generationConfig') == expected_generation_config
            ), (
                f'generationConfig was {final_json_payload.get("generationConfig")}, expected {expected_generation_config}'
            )


@pytest.mark.asyncio
async def test_gemini_thinking_patch_practical_example():
    """
    Demonstrates a practical monkey-patching approach for adding thinkingConfig to Gemini calls.
    This shows how you could patch litellm in your own code to always include thinking config.
    """
    # Import the original transformation function
    from litellm.llms.vertex_ai.gemini.transformation import (
        async_transform_request_body,
    )

    # Store the original function
    original_transform = async_transform_request_body

    # Create a patched version that adds thinkingConfig with custom settings
    async def patched_transform_with_custom_thinking(*args, **kwargs):
        # Add custom thinkingConfig to optional_params
        if 'optional_params' in kwargs:
            # You can customize the thinking config here
            kwargs['optional_params']['thinkingConfig'] = {
                'includeThoughts': True,
                # Add other thinking config options as needed
            }
        return await original_transform(*args, **kwargs)

    # Apply the monkey patch
    import litellm.llms.vertex_ai.gemini.vertex_and_google_ai_studio_gemini as gemini_module

    gemini_module.async_transform_request_body = patched_transform_with_custom_thinking

    try:
        # Patch the HTTP client to capture the request
        with patch(
            'litellm.llms.custom_httpx.http_handler.AsyncHTTPHandler.post',
            new_callable=AsyncMock,
        ) as mock_post:
            # Configure the mock response
            mock_request = httpx.Request('POST', 'https://example.com')
            mock_response = httpx.Response(
                200,
                request=mock_request,
                json={
                    'candidates': [
                        {
                            'content': {
                                'parts': [
                                    {'text': 'This is a mock response with thinking.'}
                                ]
                            }
                        }
                    ],
                    'usageMetadata': {
                        'promptTokenCount': 15,
                        'candidatesTokenCount': 8,
                        'totalTokenCount': 23,
                    },
                },
            )
            mock_post.return_value = mock_response

            # Make a normal litellm call - the thinking config will be automatically added
            litellm.drop_params = True
            await litellm.acompletion(
                model='gemini/gemini-pro',
                messages=[{'role': 'user', 'content': 'Explain quantum computing'}],
                temperature=0.7,
                max_tokens=100,
                api_key='dummy-key',
            )

            # Verify the request was made
            mock_post.assert_called_once()

            # Check that thinkingConfig was included in the request
            args, kwargs = mock_post.call_args
            final_json_payload = kwargs.get('json', {})

            generation_config = final_json_payload.get('generationConfig', {})
            assert 'thinkingConfig' in generation_config
            assert generation_config['thinkingConfig']['includeThoughts'] is True

            # Verify other parameters are still present
            assert generation_config['temperature'] == 0.7

    finally:
        # Restore the original function to avoid affecting other tests
        gemini_module.async_transform_request_body = original_transform
