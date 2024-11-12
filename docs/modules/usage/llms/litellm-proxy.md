
# LiteLLM Proxy

OpenHands supports using the [LiteLLM proxy](https://docs.litellm.ai/docs/proxy/quick_start) to access various LLM providers. This is particularly useful when you want to:

- Use a single interface to access multiple LLM providers
- Add authentication, rate limiting, and other features to your LLM API
- Route requests through a proxy for security or networking requirements

## Configuration

To use LiteLLM proxy with OpenHands, you need to:

1. Set up a LiteLLM proxy server (see [LiteLLM documentation](https://docs.litellm.ai/docs/proxy/quick_start))
2. Configure OpenHands to use the proxy

Here's an example configuration:

```toml
[llm]
# Important: Use `litellm_proxy/` instead of `openai/`
model = "litellm_proxy/anthropic.claude-3-5-sonnet-20241022-v2:0"  # The model name as configured in your LiteLLM proxy
base_url = "https://your-litellm-proxy.com"  # Your LiteLLM proxy URL
api_key = "your-api-key"  # API key for authentication with the proxy
```

:::caution
When using LiteLLM proxy, make sure to use the `litellm_proxy` provider instead of `openai`. Using `openai` as the provider may cause compatibility issues with certain LLM providers like Bedrock.
:::

## Example Usage

Here's how to use LiteLLM proxy in your OpenHands configuration:

```toml
[llm]
model = "litellm_proxy/anthropic.claude-3-5-sonnet-20241022-v2:0"
base_url = "https://proxy.example.com"
api_key = "your-api-key"
temperature = 0.0
top_p = 1.0

```

## Supported Models

The supported models depend on your LiteLLM proxy configuration. OpenHands supports any model that your LiteLLM proxy is configured to handle, including:

- OpenAI models
- Anthropic Claude models
- AWS Bedrock models
- Azure OpenAI models
- And more

Refer to your LiteLLM proxy configuration for the list of available models and their names.
