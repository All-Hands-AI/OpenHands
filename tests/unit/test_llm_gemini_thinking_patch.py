from unittest.mock import AsyncMock, patch

import litellm
import pytest


@pytest.mark.asyncio
async def test_gemini_thinking_patch():
    """
    Tests that we can monkey-patch the thinking config for Gemini calls.
    """
    # The path to the function we want to patch
    patch_target = 'litellm.llms.vertex_ai.gemini.vertex_and_google_ai_studio_gemini.VertexGeminiConfig._map_reasoning_effort_to_thinking_budget'

    # The desired thinking config
    desired_thinking_config = {'includeThoughts': True}

    with patch(patch_target, return_value=desired_thinking_config):
        # Patch the actual HTTP client
        with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
            # Configure the mock to return a future-like object with a dummy response
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                'candidates': [
                    {'content': {'parts': [{'text': 'This is a mock response.'}]}}
                ]
            }

            # Simulate a call to litellm
            litellm.drop_params = True
            await litellm.acompletion(
                model='gemini/gemini-pro',
                messages=[{'role': 'user', 'content': 'Test prompt'}],
                reasoning_effort='low',  # This will be ignored by our patch
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
                'topP': 1,
                'thinkingConfig': {'includeThoughts': True},
            }
            assert (
                final_json_payload.get('generationConfig') == expected_generation_config
            ), (
                f'generationConfig was {final_json_payload.get("generationConfig")}, expected {expected_generation_config}'
            )
