import json
import os
from unittest.mock import AsyncMock, patch

import litellm
import pytest

# Set a dummy API key to avoid authentication errors
os.environ['GEMINI_API_KEY'] = 'dummy_key'


@pytest.mark.asyncio
async def test_thinking_parameter_is_not_sent_to_gemini():
    """
    Tests that the 'thinking' parameter is NOT included in the final
    request sent to Gemini, as it should be handled before the API call.
    This test patches the final HTTP call to inspect the payload.
    """
    # The path to the method that sends the final request in litellm
    patch_target = 'litellm.llms.custom_httpx.http_handler.AsyncHTTPHandler.post'

    with patch(patch_target, new_callable=AsyncMock) as mock_post:
        # Configure the mock to return a future-like object with a dummy response
        # This simulates a successful API call
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            'choices': [
                {
                    'message': {
                        'role': 'assistant',
                        'content': 'This is a mock response.',
                    }
                }
            ]
        }

        # Simulate the call as OpenHands would, including the 'thinking' parameter
        # We need to drop params, since litellm 1.18.0+ validates gemini params
        original_drop_params = litellm.drop_params
        litellm.drop_params = True
        try:
            await litellm.acompletion(
                model='gemini/gemini-pro',
                messages=[{'role': 'user', 'content': 'Test prompt'}],
                thinking={'budget_tokens': 500},
            )
        except Exception as e:
            # We don't want the test to fail if litellm throws an exception
            # after our patch, as we are only interested in the call arguments.
            print(f'litellm.acompletion call resulted in an exception (ignored): {e}')
        finally:
            litellm.drop_params = original_drop_params

        # Assert that the post method was called at least once
        mock_post.assert_called()

        # Get the arguments of the last call to the mock
        args, kwargs = mock_post.call_args

        # Extract the JSON payload from the keyword arguments
        final_json_payload = kwargs.get('json', {})

        # The core of the test: assert that 'thinking' is not in the payload
        assert 'thinking' not in final_json_payload, (
            f"'thinking' parameter was found in the final request payload: {final_json_payload}"
        )

        # Optional: Save the captured payload for inspection
        with open('litellm_final_request.json', 'w') as f:
            json.dump(final_json_payload, f, indent=2)
