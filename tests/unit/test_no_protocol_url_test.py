from unittest.mock import patch

from openhands.core.config import LLMConfig
from openhands.llm.llm import LLM


def test_base_url_protocol_is_fixed_before_request():
    """
    Test that LLM automatically prepends a protocol to the base_url
    if it is missing, to prevent httpx.UnsupportedProtocol error.

    This avoids runtime crashes when users forget to include 'http://' or 'https://'
    in the LLMConfig.base_url.

    Steps:
    1. Create an LLMConfig with a base_url missing the protocol.
    2. Patch httpx.get to intercept the actual URL used in the request.
    3. Initialize an LLM instance using this config.
    4. Call init_model_info() to trigger the request.
    5. Assert that the URL passed to httpx.get starts with 'http://' or 'https://'.
    """

    # Create config with base_url missing protocol
    config = LLMConfig(
        model='litellm_proxy/test-model', api_key='fake-key', base_url='api.example.com'
    )

    # Patch httpx.get to intercept the actual request
    with patch('httpx.get') as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {'model': 'mock'}

        llm = LLM(config=config)

        # Trigger model info fetch
        llm.init_model_info()

        # Extract the requested URL and assert protocol is included
        called_url = mock_get.call_args[0][0]
        print('Final URL used:', called_url)

        assert called_url.startswith('http://') or called_url.startswith('https://')
