# 🤖 LLM Backends

OpenDevin can work with any LLM backend. For a full list of the LM providers and models available, please consult the [litellm documentation](https://docs.litellm.ai/docs/providers).

> **Warning**: OpenDevin will issue many prompts to the LLM you configure. Most of these LLMs cost money--be sure to set spending limits and monitor usage.

## Model Selection

- The `LLM_MODEL` environment variable controls which model is used in programmatic interactions.
- When using the OpenDevin UI, choose your model in the settings window (the gear wheel on the bottom left).

## Environment Variables

The following environment variables might be necessary for some LLMs:

- `LLM_API_KEY`
- `LLM_BASE_URL`
- `LLM_EMBEDDING_MODEL`
- `LLM_EMBEDDING_DEPLOYMENT_NAME`
- `LLM_API_VERSION`

## Provider-Specific Guides

We have guides for running OpenDevin with specific model providers:

- [ollama](llms/localLLMs)
- [Azure](llms/azureLLMs)

If you're using another provider, we encourage you to open a PR to share your setup!

## Note on Alternative Models

The best models are GPT-4 and Claude 3. Current local and open source models are not nearly as powerful. When using an alternative model, you may experience:

- Long wait times between messages
- Poor responses
- Errors about malformed JSON

OpenDevin can only be as powerful as the models driving it. Fortunately, our team is actively working on building better open source models!

## API Retries and Rate Limits

Some LLMs have rate limits and may require retries. OpenDevin will automatically retry requests if it receives a 429 error or API connection error.

You can control the retry behavior with these environment variables:

- `LLM_NUM_RETRIES`: Number of retries (default: 5)
- `LLM_RETRY_MIN_WAIT`: Minimum wait time between retries in seconds (default: 3)
- `LLM_RETRY_MAX_WAIT`: Maximum wait time between retries in seconds (default: 60)