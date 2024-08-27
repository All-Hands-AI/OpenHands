---
sidebar_position: 2
---

# 🤖 LLM Backends

OpenHands can connect to many LLMs. However, the recommended models to use are GPT-4 and Claude 3.5.

Current local and open source models are not nearly as powerful. When using an alternative model, you may see long
wait times between messages, poor responses, or errors about malformed JSON. OpenHands can only be as powerful as the
models driving it.
For a full list of the LM providers and models available, please consult the
[litellm documentation](https://docs.litellm.ai/docs/providers).

:::warning
OpenHands will issue many prompts to the LLM you configure. Most of these LLMs cost money--be sure to set spending limits and monitor usage.
:::

The `LLM_MODEL` environment variable controls which model is used in programmatic interactions.
But when using the OpenHands UI, you'll need to choose your model in the settings window.

The following environment variables might be necessary for some LLMs/providers:

- `LLM_API_KEY`
- `LLM_BASE_URL`
- `LLM_EMBEDDING_MODEL`
- `LLM_EMBEDDING_DEPLOYMENT_NAME`
- `LLM_API_VERSION`
- `LLM_DROP_PARAMS`

We have a few guides for running OpenHands with specific model providers:

- [OpenAI](llms/openai-llms)
- [ollama](llms/local-llms)
- [Azure](llms/azure-llms)
- [Google](llms/google-llms)

If you're using another provider, we encourage you to open a PR to share your setup!

## API retries and rate limits

Some LLMs have rate limits and may require retries. OpenHands will automatically retry requests if it receives a 429 error or API connection error.
You can set the following environment variables to control the number of retries and the time between retries:
* `LLM_NUM_RETRIES` (Default of 5)
* `LLM_RETRY_MIN_WAIT` (Default of 3 seconds)
* `LLM_RETRY_MAX_WAIT` (Default of 60 seconds)
