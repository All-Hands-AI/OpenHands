---
sidebar_position: 2
---

# 🤖 LLM Backends

OpenHands can work with any LLM backend.
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

## Note on Alternative Models

The best models are GPT-4 and Claude 3. Current local and open source models are
not nearly as powerful. When using an alternative model,
you may see long wait times between messages,
poor responses, or errors about malformed JSON. OpenHands
can only be as powerful as the models driving it--fortunately folks on our team
are actively working on building better open source models!

## API retries and rate limits

Some LLMs have rate limits and may require retries. OpenHands will automatically retry requests if it receives a 429 error or API connection error.
You can set `LLM_NUM_RETRIES`, `LLM_RETRY_MIN_WAIT`, `LLM_RETRY_MAX_WAIT` environment variables to control the number of retries and the time between retries.
By default, `LLM_NUM_RETRIES` is 5 and `LLM_RETRY_MIN_WAIT`, `LLM_RETRY_MAX_WAIT` are 3 seconds and 60 seconds respectively.
