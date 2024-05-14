---
sidebar_position: 2
---

# 🤖 LLM Backends

OpenDevin can work with any LLM backend.
For a full list of the LM providers and models available, please consult the
[litellm documentation](https://docs.litellm.ai/docs/providers).

:::warning
OpenDevin will issue many prompts to the LLM you configure. Most of these LLMs cost money--be sure to set spending limits and monitor usage.
:::

The `LLM_MODEL` environment variable controls which model is used in programmatic interactions.
But when using the OpenDevin UI, you'll need to choose your model in the settings window (the gear
wheel on the bottom left).

The following environment variables might be necessary for some LLMs:

- `LLM_API_KEY`
- `LLM_BASE_URL`
- `LLM_EMBEDDING_MODEL`
- `LLM_EMBEDDING_DEPLOYMENT_NAME`
- `LLM_API_VERSION`

We have a few guides for running OpenDevin with specific model providers:

- [ollama](llms/localLLMs)
- [Azure](llms/azureLLMs)

If you're using another provider, we encourage you to open a PR to share your setup!

## Note on Alternative Models

The best models are GPT-4 and Claude 3. Current local and open source models are
not nearly as powerful. When using an alternative model,
you may see long wait times between messages,
poor responses, or errors about malformed JSON. OpenDevin
can only be as powerful as the models driving it--fortunately folks on our team
are actively working on building better open source models!

## API retries and rate limits

Some LLMs have rate limits and may require retries. OpenDevin will automatically retry requests if it receives a 429 error or API connection error.
You can set `LLM_NUM_RETRIES`, `LLM_RETRY_MIN_WAIT`, `LLM_RETRY_MAX_WAIT` environment variables to control the number of retries and the time between retries.
By default, `LLM_NUM_RETRIES` is 5 and `LLM_RETRY_MIN_WAIT`, `LLM_RETRY_MAX_WAIT` are 3 seconds and 60 seconds respectively.
