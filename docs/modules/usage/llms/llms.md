# LLM Backends

OpenDevin supports various Large Language Model (LLM) backends to power its AI capabilities. This flexibility allows you to choose the most suitable LLM for your needs and integrate it seamlessly with OpenDevin.

## Supported LLM Providers

OpenDevin can work with any LLM backend supported by the [litellm library](https://docs.litellm.ai/docs/providers). Some popular options include:

- OpenAI (GPT models)
- Anthropic (Claude models)
- Google (Gemini and Vertex AI)
- Azure OpenAI
- Local models (via Ollama)

For a full list of available LLM providers and models, please consult the [litellm documentation](https://docs.litellm.ai/docs/providers).

## Model Selection

To choose your preferred LLM:

1. **Programmatic interactions**: Set the `LLM_MODEL` environment variable.
2. **OpenDevin UI**: Select your model in the settings window (gear icon in the bottom left corner).

## Common Environment Variables

Depending on your chosen LLM, you may need to set the following environment variables:

- `LLM_API_KEY`: API key for the LLM service
- `LLM_BASE_URL`: Base URL for the API endpoint
- `LLM_MODEL`: Name of the specific model to use
- `LLM_EMBEDDING_MODEL`: Model to use for text embeddings
- `LLM_EMBEDDING_DEPLOYMENT_NAME`: (For some providers) Deployment name for the embedding model
- `LLM_API_VERSION`: API version to use

## Provider-Specific Guides

We have detailed guides for setting up OpenDevin with specific LLM providers:

- [Local LLMs with Ollama](llms/localLLMs)
- [Azure OpenAI](llms/azureLLMs)
- [Google (Gemini and Vertex AI)](llms/googleLLMs)

If you're using another provider, we encourage you to contribute a guide by opening a pull request!

## Note on Alternative Models

While OpenDevin supports various LLMs, please note that the best performance is typically achieved with advanced models like GPT-4 and Claude 3. When using alternative or local models, you may experience:

- Longer response times
- Less accurate or less coherent responses
- Occasional errors in JSON formatting

OpenDevin's capabilities are directly tied to the underlying LLM's performance. Our team is actively working on improving compatibility with a wide range of models, including open-source options.

## API Retries and Rate Limits

To handle rate limits and potential API issues, OpenDevin automatically retries requests that receive a 429 error or encounter API connection problems.

You can customize the retry behavior using these environment variables:

- `LLM_NUM_RETRIES`: Number of retry attempts (default: 5)
- `LLM_RETRY_MIN_WAIT`: Minimum wait time between retries in seconds (default: 3)
- `LLM_RETRY_MAX_WAIT`: Maximum wait time between retries in seconds (default: 60)

## Warning

> **Caution**: Using OpenDevin with an LLM may result in multiple API calls and associated costs. Be sure to set appropriate spending limits and monitor your usage to avoid unexpected expenses.

We're continuously working to improve OpenDevin's integration with various LLM backends. If you encounter any issues or have suggestions for improvements, please don't hesitate to open an issue or contribute to the project!